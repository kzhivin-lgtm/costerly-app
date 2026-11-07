"""Saved-input V7 experiment. Local files only; --execute authorizes one call."""
import argparse
import base64
from html import escape
from hashlib import sha256
import json
import os
from pathlib import Path
import time
import tomllib

from agents.estimation_analyze_v7_agent import run_analyze, prepare_content, VERSION
from use_cases.estimation_detection_context_v7 import build_context, digest


def render_report(witness):
    parts = ["<!doctype html><meta charset=utf-8><title>Estimation V7 Analyze</title>",
             "<style>body{font:16px system-ui;max-width:1150px;margin:40px auto;line-height:1.5}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:8px;text-align:left}pre{white-space:pre-wrap}small{color:#666}</style>",
             f"<h1>{escape(witness.get('version', VERSION))}</h1><p>{escape(witness['status'])}, semantic review required</p>"]
    result = witness.get("result")
    if result is None and witness.get("raw_response_text"):
        # Display the original structured reply even when contract validation
        # failed. This does not repair it or change the capsule's status.
        from agents.estimation_understanding_agent import _json_object
        try:
            result = _json_object(witness["raw_response_text"])
            parts.append("<p><strong>FORMAT FAILURE: original unvalidated model response below.</strong></p>")
        except (ValueError, TypeError):
            result = {}
    if witness.get("error"):
        parts.append(f"<p>{escape(witness['error'])}</p>")
    for obj in (result or {}).get("objects", []):
        u = obj["understanding"]
        parts.append(f"<h2>{escape(obj['object_id'])}: {escape(u['name'])}</h2><table><tr><th>Island</th><th>Projection</th><th>Content role</th><th>Observation</th></tr>")
        for i in obj["islands"]:
            projection = i["projection"] + (f" {i['elevation_index']}" if i.get("elevation_index") else "")
            parts.append("<tr>" + "".join(f"<td>{escape(value)}</td>" for value in (i["island_id"], projection, i["content_role"], i["observation"])) + "</tr>")
        parts.append("</table>")
        for row in witness.get("island_normalization", []):
            if row["object_id"] != obj["object_id"]:
                continue
            values = "; ".join(f"{m['original_text']} ({m['source_unit']}) → {m['value_mm']} mm; conversion={m['conversion_required']}" for m in row["readings"])
            parts.append(f"<p>{escape(row['island_id'])}: {escape(values or 'No dimension readings')}. <small>{escape(json.dumps(row['unit_context'], ensure_ascii=False))}</small></p>")
        parts.append(f"<p>{escape(u['description'])}</p><ul>")
        for item in u["characteristics"]:
            parts.append(f"<li>{escape(item['statement'])} <small>({escape(item['basis'])}; {escape(', '.join(item['island_ids']))})</small></li>")
        parts.append("</ul><h3>Materials</h3><ul>")
        for m in u["materials"]:
            parts.append(f"<li>{escape(m['part'])}: {escape(m['material'])}, {escape(m['finish'])}, {m['thickness_mm']} mm. {escape(m['reason'])} ({escape(m['basis'])})</li>")
        parts.append("</ul>")
        for field in ("assumptions", "conflicts"):
            parts.append(f"<h3>{field.title()}</h3><ul>" + "".join(f"<li>{escape(x)}</li>" for x in u[field]) + "</ul>")
        if "front" in obj:
            parts.append("<h3>Front</h3><pre>" + escape(json.dumps(obj["front"], ensure_ascii=False, indent=2)) + "</pre>")
        if "planner" in obj:
            parts.append("<h3>Blocks</h3><ul>")
            for b in obj["planner"]["blocks"]:
                parts.append(f"<li>{escape(b['id'])}: {escape(b['name'])}. {escape(b['contains'])} ({escape(b['reason'])})</li>")
            parts.append("</ul><h3>Shared elements</h3><ul>")
            for b in obj["planner"]["shared_parts"]:
                parts.append(f"<li>{escape(b['id'])}: {escape(b['name'])}, {escape(', '.join(b['block_ids']))}</li>")
            parts.append("</ul>")
    parts.append("<details><summary>Original model text</summary><pre>" + escape(witness.get("raw_response_text", "")) + "</pre></details>")
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--revision", choices=["V7", "V7.2", "V7.3"], default="V7")
    args = parser.parse_args()
    paths = [args.output, args.output.with_suffix(".html"), args.output.with_suffix(".raw.txt")]
    if any(p.exists() for p in paths):
        parser.error("refuse to overwrite experiment")
    snapshot = json.loads(args.snapshot.read_text())
    events = [e for e in snapshot["events"] if e["id"] == args.event_id]
    if len(events) != 1:
        parser.error("exactly one matching Detection event required")
    event = dict(events[0])
    run = snapshot.get("run") or {}
    if event.get("company_id") is None:
        if run.get("run_id") != event.get("run_id") or run.get("company_id") is None:
            parser.error("saved run/company identity is unavailable")
        event["company_id"] = str(run["company_id"])
    capsules = [json.loads(p.read_text()) for p in args.input]
    inputs = [r for c in capsules for r in c["inputs"]]
    if len({r["input_id"] for r in inputs}) != len(inputs):
        parser.error("duplicate input")
    page_bytes = {}
    for capsule in capsules:
        for ref, value in capsule["source_pages_base64"].items():
            decoded = base64.b64decode(value)
            if ref in page_bytes and page_bytes[ref] != decoded:
                raise ValueError("source ref has contradictory pixels")
            page_bytes[ref] = decoded
    ocr_ids = {r["input_payload"]["document"]["ocr_event_id"] for r in inputs}
    if len(ocr_ids) != 1:
        parser.error("one OCR event per document required")
    ocr_events = [e for e in snapshot["events"] if e["id"] in ocr_ids]
    if ocr_events and (len(ocr_events) != 1 or ocr_events[0].get("run_id") != event["run_id"]):
        parser.error("OCR event belongs to another run")
    ocr_package = ocr_events[0]["raw_usage"].get("ocr_result") if ocr_events else None
    context = build_context(inputs=inputs, event=event, ocr_package=ocr_package,
                            include_measurements=args.revision in {"V7.2", "V7.3"})
    runner, version = run_analyze, VERSION
    if args.revision == "V7.2":
        from agents import estimation_analyze_v7_2_agent as current
        runner, version = current.run_analyze, current.VERSION
    elif args.revision == "V7.3":
        from agents import estimation_analyze_v7_3_agent as current
        runner, version = current.run_analyze, current.VERSION
    content = prepare_content(inputs=inputs, page_bytes=page_bytes, detection_context=context)
    witness = dict(version=version, database_writes=False, status="prepared_no_provider_calls",
        semantic_status="not_reviewed", provider_calls=0, front_calls=0, planner_calls=0, calculate_calls=0,
        input_files=[dict(path=str(p), sha256=sha256(p.read_bytes()).hexdigest()) for p in args.input],
        detection_snapshot_sha256=sha256(args.snapshot.read_bytes()).hexdigest(),
        inputs=inputs, source_pages_base64={k: base64.b64encode(v).decode() for k,v in page_bytes.items()},
        detection_context=context, preflight=dict(image_count=sum(b["type"] == "image" for b in content),
        object_count=len(inputs), island_count=sum(len(o["islands"]) for o in context["objects"])))
    if args.revision == "V7.3":
        witness["island_normalization"] = current.island_normalization(context)
        witness["derived_fields"] = ["result.objects[].front.totals", "island_normalization"]
    def save():
        args.output.write_text(json.dumps(witness, ensure_ascii=False, indent=2))
    save()
    if not args.execute:
        print(json.dumps(witness["preflight"]))
        return
    # Credentials are loaded only for the authorized call and never recorded.
    for k,v in tomllib.loads(Path("/Users/qb/costerly-app/.streamlit/secrets.toml").read_text()).items():
        if isinstance(v, (str,int,float)):
            os.environ.setdefault(k,str(v))
    started = time.monotonic()
    def record(stage, request, response):
        if stage == "request":
            witness.update(provider_request=request, request_sha256=digest(request),
                           prompt_sha256=sha256(request["system"].encode()).hexdigest(), provider_calls=1)
        else:
            raw = response.model_dump(mode="json")
            text = "\n".join(b["text"] for b in raw["content"] if b["type"] == "text")
            witness.update(provider_response=raw, raw_response_text=text, usage=raw.get("usage"),
                           stop_reason=raw.get("stop_reason"))
            args.output.with_suffix(".raw.txt").write_text(text)
        save()
    try:
        witness["result"] = runner(inputs=inputs, page_bytes=page_bytes, detection_context=context, record=record)
        if args.revision in {"V7.2", "V7.3"}:
            witness["hardware_preview"] = current.hardware_preview(witness["result"])
        witness["status"] = "analyze_requires_semantic_review"
    except Exception as exc:
        witness.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    finally:
        witness["elapsed_seconds"] = round(time.monotonic()-started,3)
        save()
        args.output.with_suffix(".html").write_text(render_report(witness))
    print(json.dumps({k:witness.get(k) for k in ("status","error","elapsed_seconds","preflight","usage")},ensure_ascii=False))


if __name__ == "__main__":
    main()
