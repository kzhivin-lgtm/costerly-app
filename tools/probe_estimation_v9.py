"""Run experimental Estimation 9 from Detection through Inventory Check and Calculation."""

from argparse import Namespace

from tools.probe_estimation_v8_3 import main, read_json, run_pipeline


def run_parts_check(*, pdf, detection_context, output, inputs=(), request_provider=None):
    """Run from original PDF and Detection evidence, with no replay inputs."""
    args = Namespace(pdf=pdf, key="document", output=output, geometry=None, resume=False,
                     block_geometry=True, cb_parts=True, parts_profile=None, saved_dimension_inventory=None,
                     material_context=None, dimension_reader=None, dimension_unit=None)
    run_pipeline(args, {"detection_context": detection_context, "inputs": inputs}, version="9",
                 request_provider=request_provider)
    return read_json(output / "parts-check.json")


if __name__ == "__main__":
    main(version="9")
