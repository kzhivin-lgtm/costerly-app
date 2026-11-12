"""Replay CB Parts on saved Analyze, Block Geometry and native contour evidence."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from use_cases.estimation_cb_geometry_parts import compile_geometry_parts


def run_geometry_parts(audit_path, analyze, geometry, key):
    native = audit_path.read_bytes()
    if sha256(native).hexdigest() != analyze["source_audit_sha256"]:
        raise ValueError("Parts must use the native evidence locked by Analyze")
    return compile_geometry_parts(analyze, geometry, json.loads(native)["documents"][key])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analyze", type=Path, required=True)
    parser.add_argument("--block-geometry", type=Path, required=True)
    parser.add_argument("--native-evidence", type=Path, required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_geometry_parts(args.native_evidence, json.loads(args.analyze.read_text()),
                                json.loads(args.block_geometry.read_text()), args.key)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
