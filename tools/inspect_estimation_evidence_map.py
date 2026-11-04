"""Offline source-line witness from a replay capsule; no provider/DB access."""
import argparse
import base64
from io import BytesIO
import json
from pathlib import Path
import time

from PIL import Image, ImageDraw

from use_cases.estimation_evidence_map import build_evidence_map


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capsule", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        parser.error("Choose a fresh output directory")
    capsule = json.loads(args.capsule.read_text())
    pages = {ref: base64.b64decode(data) for ref, data in capsule["source_pages_base64"].items()}
    started = time.monotonic()
    cache, maps = {}, []
    for row in capsule["inputs"]:
        maps.append(build_evidence_map(input_row=row, page_bytes_by_ref=pages, page_cache=cache))
    args.output_dir.mkdir(parents=True)
    (args.output_dir / "evidence_maps.json").write_text(json.dumps(maps, indent=2, ensure_ascii=False))
    for index, evidence in enumerate(maps):
        for page in evidence["pages"]:
            if not page["coordinate_frame"] or page["source_ref"] not in pages:
                continue
            image = Image.open(BytesIO(pages[page["source_ref"]])).convert("RGB")
            draw = ImageDraw.Draw(image)
            frame = page["coordinate_frame"]
            def point(value):
                return value["x"] * image.width / frame[0], value["y"] * image.height / frame[1]
            for number in evidence["dimensions"]:
                if number["page_number"] != page["page_number"]:
                    continue
                for candidate in number["line_candidates"][:1]:
                    a, b = point(candidate["start"]), point(candidate["end"])
                    draw.line((a, b), fill="blue", width=3)
                    draw.text(a, f"{number['raw_text']} CANDIDATE", fill="blue")
            image.save(args.output_dir / f"object-{index}-page-{page['page_number']}.png")
    print(json.dumps({"objects": len(maps), "seconds": round(time.monotonic() - started, 3),
        "dimensions": sum(len(m["dimensions"]) for m in maps),
        "with_candidates": sum(bool(n["line_candidates"]) for m in maps for n in m["dimensions"]),
        "output_dir": str(args.output_dir)}))


if __name__ == "__main__":
    main()
