# syntax=docker/dockerfile:1.7
# Keep the interpreter and uv binary reproducible. The tags are checked before
# each change because the virtual environment and DINO assets are Linux-only.
FROM python:3.13.15-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /uvx /bin/

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    DETECTION_VISUAL_EMBEDDING_MODEL_DIR=/opt/costerly-models/dinov2-small

# This layer changes only when locked runtime dependencies change. It is kept
# before all application files so source-only deploys reuse it.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# The model artifact is deliberately built before the application source. Its
# cache key is the locked runtime plus this explicit model contract, never an
# unrelated code or documentation change.
COPY agents/detection_visual_embedding.py /model-build/agents/detection_visual_embedding.py
COPY tools/prefetch_detection_visual_embedding.py /model-build/tools/prefetch_detection_visual_embedding.py
RUN PYTHONPATH=/model-build /app/.venv/bin/python /model-build/tools/prefetch_detection_visual_embedding.py \
    && rm -rf /model-build

# Application changes happen after the model asset layer.
COPY . /app

CMD ["sh", "-c", "exec streamlit run app.py --server.address 0.0.0.0 --server.port ${PORT:-8080} --server.headless true"]
