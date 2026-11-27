"""Exercise proposal finalization in session-local PostgreSQL tables, then rollback.

Requires psycopg as an operator dependency. No production function or table is
modified: all migration references are redirected to pg_temp before execution.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
from uuid import uuid4


def verify(connection_file: Path, migration: Path) -> dict:
    import psycopg
    match = re.search(r"^SUPABASE_DB_URL='(.*)'$", connection_file.read_text(), re.M)
    if not match:
        raise RuntimeError('The existing database connection file is not configured')
    sql = migration.read_text()
    sql = re.sub(r'^begin;\s*', '', sql, flags=re.M)
    sql = re.sub(r'^commit;\s*', '', sql, flags=re.M)
    sql = sql.replace('public.', 'pg_temp.').replace('set search_path = public', 'set search_path = pg_temp')
    assert 'public.' not in sql
    company = 'proposal-contract-' + uuid4().hex
    checks = []
    with psycopg.connect(match[1], connect_timeout=15) as conn:
        try:
            conn.execute("set local statement_timeout = '15s'")
            conn.execute('create temp table rfq_runs (run_id text primary key, company_id text, project_name text, design_partner text, client text)')
            conn.execute('create temp table rfq_estimates (estimate_id text primary key, run_id text, company_id text)')
            conn.execute('create temp table rfq_object_estimates (estimate_id text, approved boolean, status text, self_cost_ex_vat numeric)')
            for table in ('organizations', 'projects', 'project_versions'):
                conn.execute(f'create temp table {table} (like public.{table} including all)')
            conn.execute('alter table pg_temp.projects add foreign key (partner_organization_id,company_id) references pg_temp.organizations(organization_id,company_id)')
            conn.execute('alter table pg_temp.projects add foreign key (client_organization_id,company_id) references pg_temp.organizations(organization_id,company_id)')
            conn.execute('alter table pg_temp.project_versions add foreign key (project_id,company_id) references pg_temp.projects(project_id,company_id)')
            conn.execute(sql)

            def scalar(query, args=()): return conn.execute(query, args).fetchone()[0]
            def seed(run, project=None, partner=None, client=None, *, owner=company, estimate=None):
                estimate = estimate or run + '-estimate'
                conn.execute('insert into pg_temp.rfq_runs values (%s,%s,%s,%s,%s) on conflict (run_id) do nothing', (run,owner,project,partner,client))
                conn.execute('insert into pg_temp.rfq_estimates values (%s,%s,%s)', (estimate,run,owner))
                conn.execute("insert into pg_temp.rfq_object_estimates values (%s,true,'completed',100)", (estimate,))
                return estimate
            snapshot = {'summary': {'total': 118}, 'rows': [{'object_key': 'object-one', 'sale_price_total': 100}]}
            def approve(run, estimate=None, *, owner=company):
                return scalar('select pg_temp.finalize_project_estimate(%s,%s,%s,%s::jsonb)', (owner,run,estimate or run+'-estimate',json.dumps(snapshot)))
            def counts():
                return tuple(scalar(f'select count(*) from pg_temp.{t}') for t in ('organizations','projects','project_versions'))

            for named in (False, True):
                for partnered in (False, True):
                    for cliented in (False, True):
                        run = uuid4().hex
                        seed(run, 'Project '+run if named else None, 'Partner '+run if partnered else None, 'Client '+run if cliented else None)
                        before = counts(); result = approve(run); after = counts()
                        assert result['created'] and after == (before[0]+partnered+cliented,before[1]+1,before[2]+1)
                        row = conn.execute('select name,partner_organization_id,client_organization_id from pg_temp.projects where project_id=%s',(result['project_id'],)).fetchone()
                        assert (row[0] is not None,row[1] is not None,row[2] is not None) == (named,partnered,cliented)
                        frozen = scalar('select snapshot from pg_temp.project_versions where version_id=%s',(result['version_id'],))
                        assert frozen == snapshot
                        # Metadata edits on retry must not create a second association or rewrite the frozen version.
                        conn.execute("update pg_temp.rfq_runs set project_name='Changed',design_partner='Changed',client='Changed' where run_id=%s",(run,))
                        again = approve(run)
                        assert not again['created'] and again['version_id']==result['version_id'] and again['project_id']==result['project_id']
                        assert counts()==after and scalar('select snapshot from pg_temp.project_versions where version_id=%s',(result['version_id'],))==frozen
                        checks.append({'project':named,'partner':partnered,'client':cliented,'created':True,'retry_frozen':True})
            for missing in ('', '  ', 'unknown', 'Unknown', 'none', 'null', '-', '—'):
                run = uuid4().hex;seed(run,missing,missing,missing)
                before=counts();result=approve(run)
                assert counts()==(before[0],before[1]+1,before[2]+1)
                assert conn.execute('select name,normalized_name,partner_organization_id,client_organization_id from pg_temp.projects where project_id=%s',(result['project_id'],)).fetchone()==(None,None,None,None)
            checks.append({'missing_sentinels':8,'invented_organizations':0})
            # An unnamed RFQ's estimates are versions of one project; different RFQs stay separate.
            run=uuid4().hex;seed(run);first=approve(run)
            second_estimate=seed(run,estimate=run+'-second');second=approve(run,second_estimate)
            other=uuid4().hex;seed(other);third=approve(other)
            assert first['project_id']==second['project_id'] and second['version_number']==2 and third['project_id']!=first['project_id']
            checks.append({'unnamed_same_rfq_versions':True,'separate_unnamed_rfqs':True})
            for partner in (None,'Known partner'):
                run=uuid4().hex;seed(run,'Same named project',partner);first=approve(run)
                other=uuid4().hex;seed(other,'Same named project',partner);second=approve(other)
                assert first['project_id']==second['project_id'] and second['version_number']==2
            checks.append({'named_project_grouping_with_and_without_partner':True})
            run=uuid4().hex;seed(run,'Isolated',None,owner=company+'-other');before=counts()
            with conn.transaction(force_rollback=True):
                try: approve(run)
                except psycopg.Error as exc: assert exc.diag.message_primary=='RFQ or estimate is not available to this company'
                else: raise AssertionError('Cross-company approval was allowed')
            assert counts()==before
            run=uuid4().hex;estimate=seed(run)
            conn.execute('update pg_temp.rfq_object_estimates set approved=false where estimate_id=%s',(estimate,));before=counts()
            with conn.transaction(force_rollback=True):
                try: approve(run)
                except psycopg.Error as exc: assert exc.diag.message_primary=='Every object must be priced and approved before Final Approval'
                else: raise AssertionError('Unapproved object was allowed')
            assert counts()==before
            checks.append({'company_ownership':True,'object_approval':True})
            assert scalar("select count(*) from pg_temp.organizations where lower(name) in ('unknown partner','unknown','untitled project')")==0
            return {'status':'passed','scope':'pg_temp only, all changes rolled back','checks':checks}
        finally:
            conn.rollback()


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--connection-file',type=Path,required=True)
    parser.add_argument('--migration',type=Path,default=Path('db/sql/2026_11_27_final_approval_optional_metadata.sql'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=verify(args.connection_file,args.migration)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
