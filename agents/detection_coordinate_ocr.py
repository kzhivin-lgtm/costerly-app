"""Read tight numeric label boxes on the same rasters sent to Mistral."""

from __future__ import annotations

import hashlib
import os
import re
import sys
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, wait
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.request import urlopen

from PIL import Image, ImageOps


_MODEL_URL = "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/onnx/PP-OCRv6"
_MODELS = {
    "det": "f42c0fbd294d95eac1a550e131b277dac97462c8025fa4b6c3cec1b7894bd3d5",
    "rec": "e16e242de5937ad92609223f19bc2aff3727ee40b095f996907c24749bad251b",
}
_ENGINE_NAME = "rapidocr_ppocrv6_tiny"
_MAX_SIDE = 2200
_MAX_WAIT_SECONDS = 3.0
_BBOX_KEYS = ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")
_NUMBER = re.compile(r"\d{1,5}(?:[.,]\d{1,3})?(?:\s*(?:mm|cm|m|мм|см|м))?", re.I)
_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix="detection-coordinate-ocr")
_PAGE_SLOTS = threading.BoundedSemaphore(16)
_WORKER = threading.local()
_ENGINE_SETUP_LOCK = threading.Lock()
_engine_setup_complete = False


def _model_name(task: str) -> str:
    return f"PP-OCRv6_{task}_tiny.onnx"


def prefetch_models(directory: Path) -> None:
    """Download and verify the two pinned assets at image build time."""
    directory.mkdir(parents=True, exist_ok=True)
    for task, expected_hash in _MODELS.items():
        name = _model_name(task)
        with urlopen(f"{_MODEL_URL}/{task}/{name}", timeout=40) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != expected_hash:
            raise ValueError(f"Unexpected checksum for {name}")
        (directory / name).write_bytes(data)


def _engine(directory: Path) -> Any:
    global _engine_setup_complete
    if getattr(_WORKER, "model_dir", None) != directory:
        from rapidocr import ModelType, RapidOCR

        with _ENGINE_SETUP_LOCK:
            if not _engine_setup_complete:
                import cv2

                cv2.setNumThreads(1)
                _engine_setup_complete = True
        _WORKER.engine = RapidOCR(params={
            "Global.use_cls": False,
            "Global.text_score": 0.70,
            "Global.log_level": "warning",
            "Global.max_side_len": _MAX_SIDE,
            "Det.model_type": ModelType.TINY,
            "Det.model_path": str(directory / _model_name("det")),
            "Rec.model_type": ModelType.TINY,
            "Rec.model_path": str(directory / _model_name("rec")),
            "EngineConfig.onnxruntime.intra_op_num_threads": 2,
            "EngineConfig.onnxruntime.inter_op_num_threads": 1,
        })
        _WORKER.model_dir = directory
    return _WORKER.engine


def _overlap_ratio(first: dict[str, int], second: dict[str, int]) -> float:
    left, top, right, bottom = _BBOX_KEYS
    overlap_width = max(0, min(first[right], second[right]) - max(first[left], second[left]))
    overlap_height = max(0, min(first[bottom], second[bottom]) - max(first[top], second[top]))
    area = min(
        (first[right] - first[left]) * (first[bottom] - first[top]),
        (second[right] - second[left]) * (second[bottom] - second[top]),
    )
    return overlap_width * overlap_height / area if area > 0 else 0.0


def read_page_labels(page_bytes: bytes, directory: Path) -> tuple[tuple[int, int], list[dict[str, Any]]]:
    """Return standalone numeric readings and tight boxes in original raster pixels."""
    with Image.open(BytesIO(page_bytes)) as source:
        ImageOps.exif_transpose(source, in_place=True)
        width, height = source.size
        source.thumbnail((_MAX_SIDE, _MAX_SIDE), Image.Resampling.LANCZOS)
        image = source.convert("RGB")
    scale_x, scale_y = width / image.width, height / image.height
    # CAD vertical labels generally run bottom-to-top. Rotate them upright.
    # RapidOCR rotates the newly vertical horizontal-label crops back itself.
    oriented = image.transpose(Image.Transpose.ROTATE_270)
    result = _engine(directory)(oriented)
    readings: list[dict[str, Any]] = []
    if result.boxes is not None:
        for box, text, score in zip(result.boxes, result.txts, result.scores, strict=True):
            text = text.strip()
            if not _NUMBER.fullmatch(text):
                continue
            xs, ys = zip(*((y, oriented.width - x) for x, y in box), strict=True)
            left = max(0, round(min(xs) * scale_x))
            top = max(0, round(min(ys) * scale_y))
            right = min(width, round(max(xs) * scale_x))
            bottom = min(height, round(max(ys) * scale_y))
            if right > left and bottom > top:
                readings.append({
                    "source": _ENGINE_NAME,
                    "text": text,
                    "bbox": dict(zip(_BBOX_KEYS, (left, top, right, bottom), strict=True)),
                    "confidence": round(float(score), 4),
                })
    unique: list[dict[str, Any]] = []
    for item in sorted(readings, key=lambda row: -row["confidence"]):
        if not any(
            item["text"] == prior["text"] and _overlap_ratio(item["bbox"], prior["bbox"]) >= 0.6
            for prior in unique
        ):
            unique.append(item)
    return (width, height), sorted(unique, key=lambda item: tuple(item["bbox"].values()))


class CoordinateOCR:
    """Overlap bounded local CPU work with the existing OCR request pipeline."""

    def __init__(self) -> None:
        self.directory = Path(os.getenv("DETECTION_COORDINATE_OCR_MODEL_DIR", "/opt/costerly-models/detection-ocr"))
        self.enabled = os.getenv("DETECTION_COORDINATE_OCR_ENABLED", "1") == "1"
        self.available = all((self.directory / _model_name(task)).is_file() for task in _MODELS)
        self.pending: dict[Future, int] = {}
        self.skipped: list[int] = []

    def submit(self, page_number: int, page_bytes: bytes) -> None:
        if not self.enabled or not self.available:
            return
        if not _PAGE_SLOTS.acquire(blocking=False):
            self.skipped.append(page_number)
            return
        try:
            future = _POOL.submit(read_page_labels, page_bytes, self.directory)
        except Exception:
            _PAGE_SLOTS.release()
            raise
        future.add_done_callback(lambda _: _PAGE_SLOTS.release())
        self.pending[future] = page_number

    def collect(self, pages: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        start = time.perf_counter()
        if not self.enabled or not self.available:
            return [], {"status": "disabled" if not self.enabled else "models_unavailable"}
        frames = {page["page_number"]: page.get("dimensions") or {} for page in pages}
        done, pending = wait(self.pending, timeout=_MAX_WAIT_SECONDS)
        missing = {self.pending[future]: "timeout" for future in pending}
        missing.update({page: "capacity" for page in self.skipped})
        for future in pending:
            future.cancel()
        labels: list[dict[str, Any]] = []
        completed: list[int] = []
        for future in sorted(done, key=self.pending.__getitem__):
            page = self.pending[future]
            try:
                (width, height), rows = future.result()
            except Exception:
                missing[page] = "reader_error"
                continue
            frame = frames.get(page, {})
            frame_width, frame_height = frame.get("width"), frame.get("height")
            if not frame_width or not frame_height:
                missing[page] = "coordinate_frame_unavailable"
                continue
            for row in rows:
                bbox = {
                    key: round(value * (frame_width / width if key.endswith("_x") else frame_height / height))
                    for key, value in row["bbox"].items()
                }
                if bbox["bottom_right_x"] > bbox["top_left_x"] and bbox["bottom_right_y"] > bbox["top_left_y"]:
                    labels.append({**row, "page_number": page, "bbox": bbox})
            completed.append(page)
        return labels, {
            "engine": _ENGINE_NAME,
            "status": "partial" if missing else "complete",
            "pages_completed": completed,
            "pages_unavailable": dict(sorted(missing.items())),
            "label_count": len(labels),
            "wait_seconds": round(time.perf_counter() - start, 3),
        }

    def cancel(self) -> None:
        for future in self.pending:
            future.cancel()


if __name__ == "__main__":
    prefetch_models(Path(sys.argv[1]))
