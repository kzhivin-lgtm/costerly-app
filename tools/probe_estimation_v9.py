"""Run experimental Estimation 9 from Detection through Inventory Check and Calculation."""

from argparse import Namespace
import json
import logging

from tools.probe_estimation_v8_3 import main, read_json, run_pipeline


def run_parts_check(*, pdf, detection_context, output, inputs=(), request_provider=None):
    """Run from original PDF and Detection evidence, with no replay inputs."""
    args = Namespace(pdf=pdf, key="document", output=output, geometry=None, resume=False,
                     block_geometry=True, cb_parts=True, parts_profile=None, saved_dimension_inventory=None,
                     material_context=None, dimension_reader=None, dimension_unit=None)
    run_pipeline(args, {"detection_context": detection_context, "inputs": inputs}, version="9",
                 request_provider=request_provider)
    report = read_json(output / "parts-check.json")
    from use_cases.estimation_preparation_evidence import attach_preparation_evidence
    from tools.estimation_block_geometry import AUDIT_FILE

    try:
        analyze = read_json(output / "result.json")
        native = read_json(output / "geometry" / AUDIT_FILE)["documents"]["document"]
        attach_preparation_evidence(report, analyze, native)
    except Exception as exc:
        # Isolate this additive Labor output from the established Parts/Materials path.
        from observability.runtime import report_runtime_failure
        report_runtime_failure("preparation.evidence", exc)
        logging.getLogger(__name__).exception("Could not retain preparation evidence")
        for source in report["objects"].values():
            source["preparation_evidence"] = {"status": "read_failed", "interfaces": []}
    (output / "parts-check.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return report


if __name__ == "__main__":
    main(version="9")
