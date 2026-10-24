"""Deterministic visual-similarity evidence for native PDF graphic placements.

The feature extractor never creates an object or graph edge on its own. It can
require the Registry to account for a conservative same-page mutual match, then
that model decision still needs a pair-specific visual witness before admission.
"""
from __future__ import annotations

from collections import defaultdict
from io import BytesIO
from pathlib import Path
import os
import re
from threading import Lock, Thread
import time
from typing import Any, Callable


DETECTION_VISUAL_EMBEDDING_MODEL_ID = "facebook/dinov2-small"
DETECTION_VISUAL_EMBEDDING_MODEL_REVISION = "ed25f3a31f01632728cabb09d1542f84ab7b0056"
DETECTION_NATIVE_XOBJECT_STRONG_EMBEDDING_MIN_COSINE = 0.80
DETECTION_NATIVE_XOBJECT_STRONG_EMBEDDING_MIN_MARGIN = 0.10
DETECTION_VISUAL_EMBEDDING_MODEL_DIR_ENV = "DETECTION_VISUAL_EMBEDDING_MODEL_DIR"
_GRAPHIC_XREF_PATTERN = re.compile(r"^NPIG-P\d{3}-X(?P<xref>\d+)-I\d{3}-R\d{3}$")
_ENCODER_LOCK = Lock()
_ENCODER: tuple[Any, Any] | None = None
_PRELOAD_THREAD: Thread | None = None
_PRELOAD_ERROR: str | None = None


class DetectionVisualEmbeddingUnavailable(RuntimeError):
    """The optional pair-ranking signal cannot be calculated safely."""


def detection_visual_embedding_model_dir() -> Path:
    configured = os.getenv(DETECTION_VISUAL_EMBEDDING_MODEL_DIR_ENV, "").strip()
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[1] / ".models" / "dinov2-small"


def _required_model_files(model_dir: Path) -> tuple[Path, ...]:
    return tuple(model_dir / name for name in (
        "config.json", "preprocessor_config.json", "model.safetensors",
    ))


def _load_native_xobject_encoder() -> tuple[Any, Any]:
    global _ENCODER
    with _ENCODER_LOCK:
        if _ENCODER is not None:
            return _ENCODER
        model_dir = detection_visual_embedding_model_dir()
        missing = [str(path) for path in _required_model_files(model_dir) if not path.is_file()]
        if missing:
            raise DetectionVisualEmbeddingUnavailable(
                "DINOv2 model assets are unavailable in the deployed image: "
                + ", ".join(missing)
            )
        try:
            import torch
            from transformers import AutoImageProcessor, AutoModel
        except (ImportError, ModuleNotFoundError) as exc:
            raise DetectionVisualEmbeddingUnavailable(
                "DINOv2 runtime dependencies are unavailable"
            ) from exc
        try:
            processor = AutoImageProcessor.from_pretrained(
                str(model_dir), local_files_only=True,
            )
            model = AutoModel.from_pretrained(
                str(model_dir), local_files_only=True,
            ).eval()
            # Native Railway containers are CPU-only for Detection. Explicitly keep
            # the model off a potentially partial accelerator integration.
            model.to("cpu")
            _ENCODER = (processor, model)
            return _ENCODER
        except Exception as exc:  # pragma: no cover - exact transformer errors vary by platform
            raise DetectionVisualEmbeddingUnavailable(
                "DINOv2 model assets could not be loaded offline"
            ) from exc


def maybe_preload_detection_native_xobject_encoder(
    native_graphic_regions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Warm DINOv2 while Mistral OCR is still in flight when likely useful.

    This is deliberately only a preload. It does not select the route and does
    not inspect user images. The native-XObject route later checks the strict page-level anchor
    gate before using any embedding.
    """
    global _PRELOAD_ERROR, _PRELOAD_THREAD
    per_page_counts: dict[int, int] = defaultdict(int)
    for region in native_graphic_regions:
        try:
            page_number = int(region.get("page_number"))
        except (AttributeError, TypeError, ValueError):
            continue
        if page_number >= 1:
            per_page_counts[page_number] += 1
    if not per_page_counts or not all(2 <= count <= 12 for count in per_page_counts.values()):
        return {"status": "not_candidate"}

    with _ENCODER_LOCK:
        if _ENCODER is not None:
            return {"status": "ready"}
        if _PRELOAD_THREAD is not None and _PRELOAD_THREAD.is_alive():
            return {"status": "loading"}
        if _PRELOAD_ERROR is not None:
            return {"status": "failed", "reason": _PRELOAD_ERROR}

        def preload() -> None:
            global _PRELOAD_ERROR
            try:
                _load_native_xobject_encoder()
            except DetectionVisualEmbeddingUnavailable as exc:
                _PRELOAD_ERROR = str(exc)

        _PRELOAD_THREAD = Thread(
            target=preload,
            name="detection-native-xobject-embedding-preload",
            daemon=True,
        )
        _PRELOAD_THREAD.start()
    return {"status": "scheduled"}


def _graphic_xref(graphic_id: str) -> int:
    match = _GRAPHIC_XREF_PATTERN.fullmatch(graphic_id)
    if match is None:
        raise DetectionVisualEmbeddingUnavailable(
            f"native graphic ID has no recoverable PDF XObject reference: {graphic_id}"
        )
    return int(match.group("xref"))


def _extract_native_xobject_images(
    *,
    file_bytes: bytes,
    groups: list[dict[str, Any]],
) -> dict[str, Any]:
    try:
        import fitz
        from PIL import Image
    except (ImportError, ModuleNotFoundError) as exc:
        raise DetectionVisualEmbeddingUnavailable(
            "native PDF graphic extraction dependencies are unavailable"
        ) from exc

    by_graphic_id: dict[str, Any] = {}
    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as exc:  # pragma: no cover - PyMuPDF exception names vary
        raise DetectionVisualEmbeddingUnavailable(
            "source PDF cannot be reopened for native graphic extraction"
        ) from exc
    try:
        for group in groups:
            group_id = str(group.get("group_id") or "")
            graphic_id = str(group.get("native_graphic_region_id") or "")
            if not group_id or not graphic_id:
                raise DetectionVisualEmbeddingUnavailable(
                    "native graphic route supplied a group without a graphic ID"
                )
            if graphic_id not in by_graphic_id:
                xref = _graphic_xref(graphic_id)
                try:
                    extracted = document.extract_image(xref)
                except Exception as exc:  # pragma: no cover - malformed PDF branch
                    raise DetectionVisualEmbeddingUnavailable(
                        f"PDF XObject {graphic_id} cannot be extracted"
                    ) from exc
                image_bytes = extracted.get("image") if isinstance(extracted, dict) else None
                if not isinstance(image_bytes, bytes) or not image_bytes:
                    raise DetectionVisualEmbeddingUnavailable(
                        f"PDF XObject {graphic_id} has no extractable image bytes"
                    )
                by_graphic_id[graphic_id] = Image.open(BytesIO(image_bytes)).convert("RGB")
    finally:
        document.close()
    return {
        str(group["group_id"]): by_graphic_id[str(group["native_graphic_region_id"])]
        for group in groups
    }


def _encode_images(images: list[Any]) -> list[list[float]]:
    processor, model = _load_native_xobject_encoder()
    try:
        import torch
    except (ImportError, ModuleNotFoundError) as exc:  # pragma: no cover - loader checks first
        raise DetectionVisualEmbeddingUnavailable("PyTorch is unavailable") from exc
    try:
        batch = processor(images=images, return_tensors="pt")
        with torch.inference_mode():
            # DINOv2 CLS represents the entire image, its documented use case.
            vectors = model(**batch).last_hidden_state[:, 0, :]
        vectors = torch.nn.functional.normalize(vectors, p=2, dim=1)
        return vectors.cpu().tolist()
    except Exception as exc:  # pragma: no cover - library failures are platform-specific
        raise DetectionVisualEmbeddingUnavailable(
            "DINOv2 image feature extraction failed"
        ) from exc


def build_detection_native_xobject_embedding_prior(
    *,
    file_bytes: bytes,
    visual_groups: list[dict[str, Any]],
    image_extractor: Callable[..., dict[str, Any]] = _extract_native_xobject_images,
    image_encoder: Callable[[list[Any]], list[list[float]]] = _encode_images,
) -> dict[str, Any]:
    """Return auditable same-page DINOv2 pair rankings for native XObjects.

    The returned scores are intentionally never converted into an edge. The
    caller may show them to Registry only as an image-similarity prior.
    """
    started = time.perf_counter()
    groups = [
        group for group in visual_groups
        if str(group.get("native_graphic_region_id") or "")
    ]
    if len(groups) < 2:
        raise DetectionVisualEmbeddingUnavailable(
            "fewer than two native graphic groups are available for pair ranking"
        )
    groups_by_page: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for group in groups:
        try:
            page_number = int(group["page_number"])
        except (KeyError, TypeError, ValueError) as exc:
            raise DetectionVisualEmbeddingUnavailable(
                "native graphic group has no valid page number"
            ) from exc
        groups_by_page[page_number].append(group)

    images_by_group = image_extractor(file_bytes=file_bytes, groups=groups)
    scores: list[dict[str, Any]] = []
    rankings: list[dict[str, Any]] = []
    embedding_dimension = 0
    for page_number, page_groups in sorted(groups_by_page.items()):
        ordered = sorted(page_groups, key=lambda group: str(group["group_id"]))
        group_ids = [str(group["group_id"]) for group in ordered]
        if any(group_id not in images_by_group for group_id in group_ids):
            raise DetectionVisualEmbeddingUnavailable(
                f"native graphic image is missing for page {page_number}"
            )
        vectors = image_encoder([images_by_group[group_id] for group_id in group_ids])
        if len(vectors) != len(group_ids) or not vectors:
            raise DetectionVisualEmbeddingUnavailable(
                f"DINOv2 returned an incomplete embedding batch for page {page_number}"
            )
        embedding_dimension = len(vectors[0])
        if any(len(vector) != embedding_dimension for vector in vectors):
            raise DetectionVisualEmbeddingUnavailable(
                "DINOv2 returned embeddings with inconsistent dimensions"
            )
        pair_scores: dict[tuple[str, str], float] = {}
        for left_index, left_id in enumerate(group_ids):
            for right_index in range(left_index + 1, len(group_ids)):
                right_id = group_ids[right_index]
                score = round(sum(
                    float(left) * float(right)
                    for left, right in zip(vectors[left_index], vectors[right_index], strict=True)
                ), 6)
                pair_scores[(left_id, right_id)] = score
                scores.append({
                    "page_number": page_number,
                    "group_id_a": left_id,
                    "group_id_b": right_id,
                    "cosine_similarity": score,
                })
        for group_id in group_ids:
            candidates = []
            for other_id in group_ids:
                if other_id == group_id:
                    continue
                pair_key = tuple(sorted((group_id, other_id)))
                candidates.append({
                    "group_id": other_id,
                    "cosine_similarity": pair_scores[pair_key],
                })
            candidates.sort(
                key=lambda row: (-float(row["cosine_similarity"]), str(row["group_id"]))
            )
            rankings.append({
                "page_number": page_number,
                "group_id": group_id,
                "ranked_candidates": [
                    {**candidate, "rank": index}
                    for index, candidate in enumerate(candidates, start=1)
                ],
            })
    return {
        "status": "available",
        "model_id": DETECTION_VISUAL_EMBEDDING_MODEL_ID,
        "model_revision": DETECTION_VISUAL_EMBEDDING_MODEL_REVISION,
        "input_kind": "native_pdf_image_xobject",
        "embedding_dimension": embedding_dimension,
        "group_count": len(groups),
        "same_page_pair_count": len(scores),
        "scores": scores,
        "rankings": rankings,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
    }


def derive_detection_native_xobject_strong_mutual_pairs(
    prior: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return conservative, same-page mutual-top-one visual evidence.

    A DINO score is not a graph edge. This gate merely identifies pairs for
    which the Registry must account for a materially stronger-than-alternative
    visual resemblance. The Registry still needs a concrete visible witness to
    admit a same-object edge.
    """
    if prior.get("status") != "available":
        return []
    rankings_by_group = {
        str(row.get("group_id") or ""): list(row.get("ranked_candidates") or [])
        for row in prior.get("rankings") or []
        if isinstance(row, dict) and str(row.get("group_id") or "")
    }
    page_by_group = {
        str(row.get("group_id") or ""): int(row.get("page_number") or 0)
        for row in prior.get("rankings") or []
        if isinstance(row, dict) and str(row.get("group_id") or "")
    }
    strong_pairs: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for group_id, candidates in sorted(rankings_by_group.items()):
        if not candidates:
            continue
        top = candidates[0]
        other_id = str(top.get("group_id") or "")
        other_candidates = rankings_by_group.get(other_id) or []
        if not other_id or not other_candidates:
            continue
        reciprocal = other_candidates[0]
        if str(reciprocal.get("group_id") or "") != group_id:
            continue
        pair = tuple(sorted((group_id, other_id)))
        if pair in seen_pairs or page_by_group.get(group_id) != page_by_group.get(other_id):
            continue
        score = float(top.get("cosine_similarity") or 0.0)
        reciprocal_score = float(reciprocal.get("cosine_similarity") or 0.0)
        if abs(score - reciprocal_score) > 0.000001:
            continue
        next_scores = [
            float(candidates[1].get("cosine_similarity") or 0.0)
            if len(candidates) > 1 else None,
            float(other_candidates[1].get("cosine_similarity") or 0.0)
            if len(other_candidates) > 1 else None,
        ]
        margins = [score - value for value in next_scores if value is not None]
        if not margins:
            # With only two graphic placements there is no alternative against
            # which to establish a preference margin. Keep that pair ranked,
            # but do not elevate it to strong typed evidence.
            continue
        min_margin = min(margins)
        if score < DETECTION_NATIVE_XOBJECT_STRONG_EMBEDDING_MIN_COSINE:
            continue
        if min_margin < DETECTION_NATIVE_XOBJECT_STRONG_EMBEDDING_MIN_MARGIN:
            continue
        seen_pairs.add(pair)
        strong_pairs.append({
            "page_number": page_by_group[group_id],
            "group_id_a": pair[0],
            "group_id_b": pair[1],
            "cosine_similarity": round(score, 6),
            "minimum_margin_to_next_candidate": round(min_margin, 6),
            "embedding_reference": f"native_mutual_top1:{score:.4f}",
        })
    return strong_pairs


def format_detection_native_xobject_embedding_prior(
    prior: dict[str, Any],
    *,
    strong_pairs: list[dict[str, Any]] | None = None,
) -> str:
    """Format typed visual-similarity evidence for the pairwise Registry call."""
    if prior.get("status") != "available":
        return (
            "NATIVE XOBJECT VISUAL-SIMILARITY EVIDENCE: unavailable. For every "
            "ledger row use embedding_reference=not_applicable and "
            "embedding_assessment=not_applicable."
        )
    strong_pairs = strong_pairs if strong_pairs is not None else (
        derive_detection_native_xobject_strong_mutual_pairs(prior)
    )
    lines = [
        "NATIVE XOBJECT VISUAL-SIMILARITY EVIDENCE:",
        "DINOv2 compared the source-authored graphic images, not page crops.",
        "A listed strong mutual pair is typed evidence of visual identity, but "
        "cannot independently create a graph edge. A same_object decision still "
        "needs one concrete, pair-specific visible identity witness.",
    ]
    if strong_pairs:
        lines.append("STRONG MUTUAL TOP-1 PAIRS, REQUIRED LEDGER ACCOUNTING:")
        for pair in strong_pairs:
            margin = pair.get("minimum_margin_to_next_candidate")
            margin_text = (
                f", next-margin={float(margin):.4f}" if margin is not None else ""
            )
            lines.append(
                f"P{int(pair['page_number'])} {pair['group_id_a']} <-> "
                f"{pair['group_id_b']}: reference={pair['embedding_reference']}"
                f"{margin_text}."
            )
        lines.extend([
            "For each listed pair, copy its exact embedding_reference and set "
            "embedding_assessment to supports_same_object or "
            "contradicted_by_visible_separation.",
            "A different_object decision for a listed pair is valid only with an "
            "explicit author distinction, incompatible visible dimensions, or "
            "physical separation of two completed products. A generic envelope, "
            "material, frame, or functional difference is not a contradiction.",
        ])
    else:
        lines.append("No pair meets the strong mutual-top-1 evidence gate.")
    lines.append(
        "For every pair not listed above use embedding_reference=not_applicable "
        "and embedding_assessment=not_applicable."
    )
    for row in prior.get("rankings") or []:
        candidates = list(row.get("ranked_candidates") or [])[:2]
        rendered = ", ".join(
            f"#{candidate['rank']} {candidate['group_id']}={float(candidate['cosine_similarity']):.4f}"
            for candidate in candidates
        )
        if rendered:
            lines.append(f"P{int(row['page_number'])} {row['group_id']}: {rendered}")
    return "\n".join(lines)
