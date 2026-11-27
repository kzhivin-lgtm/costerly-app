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
            conn.execute('create temp table companies (company_id text primary key)')
            conn.execute('create temp table company_members (company_id text, user_id uuid)')
            conn.execute('create temp table rfq_runs (run_id text primary key, company_id text, project_name text, design_partner text, client text)')
            conn.execute('create temp table rfq_estimates (estimate_id text primary key, run_id text, company_id text)')
            conn.execute('create temp table rfq_object_estimates (estimate_id text, approved boolean, status text, self_cost_ex_vat numeric)')
            conn.execute('alter table rfq_object_estimates add column run_id text, add column company_id text, add column object_id text, add column object_name text, add column updated_at timestamptz')
            conn.execute('create temp table rfq_detected_objects (run_id text,company_id text,object_id text,object_name text,primary key(run_id,object_id))')
            conn.execute('create temp table rfq_estimate_lines (estimate_id text, company_id text, line_id text, hours numeric, cost numeric)')
            conn.execute('create temp table rfq_estimate_material_plans (estimate_id text, company_id text, plan_payload jsonb)')
            conn.execute('create temp table rfq_estimate_pricing_overrides (estimate_id text, object_key text, field text, value numeric)')
            conn.execute('create temp table rfq_estimate_material_norm_overrides (estimate_id text, company_id text, quantity_per_item numeric)')
            conn.execute('create temp table rfq_estimate_material_purchase_overrides (estimate_id text, company_id text, purchase_quantity numeric)')
            for table in ('organizations', 'projects', 'project_versions'):
                conn.execute(f'create temp table {table} (like public.{table} including all)')
            conn.execute('alter table pg_temp.projects add foreign key (partner_organization_id,company_id) references pg_temp.organizations(organization_id,company_id)')
            conn.execute('alter table pg_temp.projects add foreign key (client_organization_id,company_id) references pg_temp.organizations(organization_id,company_id)')
            conn.execute('alter table pg_temp.project_versions add foreign key (project_id,company_id) references pg_temp.projects(project_id,company_id)')
            conn.execute(sql)

            def scalar(query, args=()): return conn.execute(query, args).fetchone()[0]
            def seed(run, project=None, partner=None, client=None, *, owner=company, estimate=None):
                estimate = estimate or run + '-estimate'
                conn.execute('insert into pg_temp.companies values (%s) on conflict do nothing',(owner,))
                conn.execute('insert into pg_temp.rfq_runs values (%s,%s,%s,%s,%s) on conflict (run_id) do nothing', (run,owner,project,partner,client))
                conn.execute('insert into pg_temp.rfq_estimates values (%s,%s,%s)', (estimate,run,owner))
                conn.execute("insert into pg_temp.rfq_detected_objects values (%s,%s,'object-one','Object one') on conflict do nothing",(run,owner))
                conn.execute("insert into pg_temp.rfq_object_estimates(estimate_id,approved,status,self_cost_ex_vat,run_id,company_id,object_id,object_name) values (%s,true,'completed',100,%s,%s,'object-one','Object one')", (estimate,run,owner))
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
                        assert {k:v for k,v in frozen.items() if k!='calculation'} == snapshot
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
            if 'project_versions_proposal_request_key' in sql:
                run=uuid4().hex;estimate=seed(run,'Revision project','Revision partner')
                snapshot['proposal_request_id']=uuid4().hex
                source_a=f'storage://rfq-estimation-originals/{company}/'+('a'*64)+'.pdf'
                source_b=f'storage://rfq-estimation-originals/{company}/'+('b'*64)+'.pdf'
                snapshot['document']={'source':{'storage_ref':source_a,'content_sha256':'a'*64,'file_name':'first.pdf','mime_type':'application/pdf','size_bytes':100}}
                conn.execute("insert into pg_temp.rfq_estimate_lines select %s,%s,'line-'||n,1,10 from generate_series(1,1201) n",(estimate,company))
                first=approve(run,estimate)
                assert scalar('select source_file_path from pg_temp.project_versions where version_id=%s',(first['version_id'],))==source_a
                frozen=scalar('select snapshot from pg_temp.project_versions where version_id=%s',(first['version_id'],))
                assert len(frozen['calculation']['lines'])==1201
                file_a=scalar('select source_file_id from pg_temp.project_versions where version_id=%s',(first['version_id'],))
                assert file_a is not None
                snapshot['summary']['total']=999
                retry=approve(run,estimate)
                assert not retry['created'] and retry['version_id']==first['version_id']
                assert scalar('select snapshot from pg_temp.project_versions where version_id=%s',(first['version_id'],))==frozen
                snapshot['proposal_request_id']=uuid4().hex
                conn.execute("update pg_temp.rfq_runs set project_name='Renamed',design_partner=null where run_id=%s",(run,))
                second=approve(run,estimate)
                assert second['created'] and second['project_id']==first['project_id'] and second['version_number']==first['version_number']+1
                assert second['version_id']!=first['version_id']
                assert scalar('select source_file_id from pg_temp.project_versions where version_id=%s',(second['version_id'],))==file_a
                snapshot['summary']['total']=118
                snapshot['proposal_request_id']=uuid4().hex
                third=approve(run,estimate)
                assert third['created'] and third['version_number']==second['version_number']+1
                assert third['project_id']==first['project_id']
                assert scalar('select source_file_path from pg_temp.project_versions where version_id=%s',(third['version_id'],))==source_a
                assert scalar('select snapshot from pg_temp.project_versions where version_id=%s',(first['version_id'],))==frozen
                assert not approve(run,estimate)['created']
                snapshot.pop('proposal_request_id')
                assert approve(run,estimate)['version_id']==third['version_id'], 'Old client reuses latest, no duplicate'
                new_run=uuid4().hex;new_estimate=seed(new_run,'Different title','Different presentation partner')
                snapshot['target_project_id']=first['project_id']
                snapshot['proposal_request_id']=uuid4().hex
                snapshot['document']['source']={'storage_ref':source_b,'content_sha256':'b'*64,'file_name':'second.pdf','mime_type':'application/pdf','size_bytes':101}
                fourth=approve(new_run,new_estimate)
                assert fourth['project_id']==first['project_id'] and fourth['version_number']==third['version_number']+1
                file_b=scalar('select source_file_id from pg_temp.project_versions where version_id=%s',(fourth['version_id'],))
                assert file_b!=file_a
                assert scalar('select count(*) from pg_temp.project_files where project_id=%s',(first['project_id'],))==2
                with conn.transaction(force_rollback=True):
                    try:conn.execute('update pg_temp.project_files set content_sha256=%s where file_id=%s',('c'*64,file_a))
                    except psycopg.Error as exc:assert exc.diag.message_primary=='Project source file identity is immutable'
                    else:raise AssertionError('File content identity was rewritten')
                # A repeated filename cannot merge different contents or object sets.
                snapshot['document']['source']['file_name']='first.pdf'
                snapshot['proposal_request_id']=uuid4().hex
                fifth=approve(new_run,new_estimate)
                assert scalar('select source_file_id from pg_temp.project_versions where version_id=%s',(fifth['version_id'],))==file_b
                conn.execute("update pg_temp.rfq_estimate_lines set hours=7 where estimate_id=%s",(estimate,))
                assert scalar('select snapshot from pg_temp.project_versions where version_id=%s',(first['version_id'],))==frozen
                with conn.transaction(force_rollback=True):
                    try:conn.execute("update pg_temp.project_versions set snapshot='{}'::jsonb where version_id=%s",(first['version_id'],))
                    except psycopg.Error as exc:assert exc.diag.message_primary=='Issued project versions are immutable'
                    else:raise AssertionError('Issued snapshot was rewritten')
                conn.execute("update pg_temp.project_versions set proposal_pdf_path='first.pdf' where version_id=%s",(first['version_id'],))
                with conn.transaction(force_rollback=True):
                    try:conn.execute("update pg_temp.project_versions set proposal_pdf_path='replacement.pdf' where version_id=%s",(first['version_id'],))
                    except psycopg.Error as exc:assert exc.diag.message_primary=='Issued project versions are immutable'
                    else:raise AssertionError('Issued PDF reference was replaced')
                snapshot['proposal_request_id']='invalid'
                with conn.transaction(force_rollback=True):
                    try: approve(run,estimate)
                    except psycopg.Error as exc: assert exc.diag.message_primary=='Invalid proposal revision request'
                    else: raise AssertionError('Malformed revision was accepted')
                checks.append({'same_estimate_revisions':3,'retry_frozen':True,'metadata_edits_keep_project':True,
                               'return_to_old_values_gets_new_number':True,'legacy_client_idempotent':True,'frozen_source_per_version':True,
                               'same_content_reuses_file':True,'changed_content_new_file':True,'same_name_not_identity':True,
                               'all_calculation_lines':1201,'old_calculation_retained_after_edits':True,'append_only_snapshots':True,'immutable_file_identity':True,
                               'explicit_project_id_not_title_matching':True})
                foreign=scalar('insert into pg_temp.projects(company_id,name,normalized_name) values (%s,%s,%s) returning project_id',(company+'-other','Foreign project','foreign project'))
                snapshot['proposal_request_id']=uuid4().hex
                snapshot['target_project_id']=str(foreign)
                with conn.transaction(force_rollback=True):
                    try: approve(new_run,new_estimate)
                    except psycopg.Error as exc:assert exc.diag.message_primary=='Project is not available to this company'
                    else:raise AssertionError('Foreign target project was accepted')
                other_owned=scalar('select project_id from pg_temp.projects where company_id=%s and project_id<>%s limit 1',(company,first['project_id']))
                snapshot['target_project_id']=str(other_owned)
                with conn.transaction(force_rollback=True):
                    try:approve(new_run,new_estimate)
                    except psycopg.Error as exc:assert exc.diag.message_primary=='An issued estimate cannot be moved to another project'
                    else:raise AssertionError('Issued estimate was moved')
                snapshot['target_project_id']=first['project_id']
                checks.append({'explicit_project_company_ownership':True,'issued_estimate_project_is_stable':True})
                snapshot['proposal_request_id']=uuid4().hex
                snapshot['document']['source']['storage_ref']=f'storage://rfq-estimation-originals/other-company/{"b"*64}.pdf'
                with conn.transaction(force_rollback=True):
                    try: approve(run,estimate)
                    except psycopg.Error as exc: assert exc.diag.message_primary=='Proposal source does not belong to this company'
                    else: raise AssertionError('Foreign source was accepted')
                checks.append({'source_company_ownership':True})
                assert scalar('select pg_temp.rename_file_review_object(%s,%s,%s,%s,%s)',(company,run,'object-one','Object one','Renamed desk'))
                assert scalar('select object_name from pg_temp.rfq_object_estimates where estimate_id=%s',(estimate,))=='Renamed desk'
                conn.execute("update pg_temp.rfq_object_estimates set object_name='Stale worker' where estimate_id=%s",(estimate,))
                assert scalar('select object_name from pg_temp.rfq_object_estimates where estimate_id=%s',(estimate,))=='Renamed desk'
                assert not scalar('select pg_temp.rename_file_review_object(%s,%s,%s,%s,%s)',(company,run,'object-one','Object one','Stale user'))
                assert scalar('select object_name from pg_temp.rfq_detected_objects where run_id=%s',(run,))=='Renamed desk'
                assert scalar('select snapshot from pg_temp.project_versions where version_id=%s',(first['version_id'],))==frozen
                with conn.transaction(force_rollback=True):
                    try:scalar('select pg_temp.rename_file_review_object(%s,%s,%s,%s,%s)',(company+'-other',run,'object-one','Renamed desk','Foreign'))
                    except psycopg.Error as exc:assert exc.diag.message_primary=='RFQ is not available to this company'
                    else:raise AssertionError('Foreign object rename was accepted')
                checks.append({'manual_name_and_estimate_mirrors_atomic':True,'late_worker_cannot_restore_old_name':True,'rename_cas_and_tenant_protection':True,'issued_names_unchanged':True})
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
