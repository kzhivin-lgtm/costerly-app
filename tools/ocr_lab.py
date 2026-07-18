from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from agents.ocr_adapter import run_mistral_ocr
from agents.ocr_contract import OCR_PROFILES
from agents.ocr_quality import evaluate_ocr_result, score_expected_evidence
from agents.ocr_rendering import run_mistral_document_evidence_ocr


def run_lab(
    *,
    file_path: Path,
    profile: str,
    expected_path: Path | None = None,
) -> dict:
    runner = (
        run_mistral_document_evidence_ocr
        if profile == "evidence"
        else run_mistral_ocr
    )
    runner_args = {
        "file_name": file_path.name,
        "file_bytes": file_path.read_bytes(),
    }
    if runner is run_mistral_ocr:
        runner_args["profile"] = profile
    package = runner(**runner_args)
    report = {
        "lab_version": "ocr_lab_v2",
        "created_at": datetime.now(UTC).isoformat(),
        "profile": profile,
        "source_file": file_path.name,
        "metrics": evaluate_ocr_result(package),
        "ocr_result": package,
    }
    if expected_path:
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
        report["evidence_score"] = score_expected_evidence(package, expected)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Mistral OCR profiles.")
    parser.add_argument("file", type=Path)
    parser.add_argument("--profile", choices=sorted(OCR_PROFILES), default="basic")
    parser.add_argument("--expected", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/ocr_lab"))
    args = parser.parse_args()

    report = run_lab(
        file_path=args.file,
        profile=args.profile,
        expected_path=args.expected,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / f"{args.file.stem}_{args.profile}.json"
    report_path = args.output_dir / f"{args.file.stem}_{args.profile}.report.json"
    output_path.write_text(
        json.dumps(report["ocr_result"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report_path.write_text(
        json.dumps({key: value for key, value in report.items() if key != "ocr_result"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary = {
        "output": str(output_path),
        "report": str(report_path),
        "profile": args.profile,
        "metrics": report["metrics"],
        "evidence_score": report.get("evidence_score"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
