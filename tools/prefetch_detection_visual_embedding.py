"""Fetch the pinned DINOv2 assets during Railway build, never at RFQ runtime."""
from __future__ import annotations

from pathlib import Path
import sys

from huggingface_hub import snapshot_download

# ``uv run python tools/...`` executes this file with ``tools`` as sys.path[0].
# Add the repository root before importing the shared model contract.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.detection_visual_embedding import (
    DETECTION_VISUAL_EMBEDDING_MODEL_ID,
    DETECTION_VISUAL_EMBEDDING_MODEL_REVISION,
    detection_visual_embedding_model_dir,
)


def main() -> None:
    destination = detection_visual_embedding_model_dir()
    snapshot_download(
        repo_id=DETECTION_VISUAL_EMBEDDING_MODEL_ID,
        revision=DETECTION_VISUAL_EMBEDDING_MODEL_REVISION,
        local_dir=Path(destination),
        allow_patterns=[
            "config.json",
            "preprocessor_config.json",
            "model.safetensors",
        ],
    )
    required = [destination / name for name in (
        "config.json", "preprocessor_config.json", "model.safetensors",
    )]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("DINOv2 prefetch did not produce required assets: " + ", ".join(missing))
    print(f"Prepared {DETECTION_VISUAL_EMBEDDING_MODEL_ID}@{DETECTION_VISUAL_EMBEDDING_MODEL_REVISION}")


if __name__ == "__main__":
    main()
