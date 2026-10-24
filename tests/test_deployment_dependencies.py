from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def test_uv_is_the_single_dependency_source() -> None:
    assert (ROOT / "pyproject.toml").is_file()
    assert (ROOT / "uv.lock").is_file()
    assert not (ROOT / "requirements.txt").exists()


def test_production_dependencies_are_exactly_pinned() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())

    assert project["project"]["requires-python"] == ">=3.13,<3.14"
    assert project["project"]["dependencies"] == [
        "anthropic==0.111.0",
        "cryptography==49.0.0",
        "huggingface-hub==2.3.0",
        "httpx==0.28.1",
        "openpyxl==3.1.5",
        "pandas==3.0.6",
        "xlrd==2.0.2",
        "pillow==12.2.0",
        "pillow-heif>=0.20,<2",
        "pymupdf==1.28.2",
        "streamlit==1.64.0",
        "supabase==2.31.0",
        "torch==2.11.0",
        "transformers==5.20.2",
    ]
    assert project["tool"]["uv"]["package"] is False
    assert project["tool"]["uv"]["sources"]["torch"] == {"index": "pytorch-cpu"}
    assert project["tool"]["uv"]["index"] == [{
        "name": "pytorch-cpu",
        "url": "https://download.pytorch.org/whl/cpu",
        "explicit": True,
    }]


def test_railway_model_artifact_is_before_application_source() -> None:
    railway = tomllib.loads((ROOT / "railway.toml").read_text())
    dockerfile = (ROOT / "Dockerfile").read_text()
    dockerignore = (ROOT / ".dockerignore").read_text().splitlines()

    assert railway["build"] == {
        "builder": "DOCKERFILE",
        "dockerfilePath": "Dockerfile",
    }
    assert "python:3.13.15-slim-bookworm" in dockerfile
    assert "ghcr.io/astral-sh/uv:0.13.5" in dockerfile
    assert "DETECTION_VISUAL_EMBEDDING_MODEL_DIR=/opt/costerly-models/dinov2-small" in dockerfile
    assert "uv sync --locked --no-dev --no-install-project" in dockerfile
    assert "tools/prefetch_detection_visual_embedding.py" in dockerfile
    assert dockerfile.index("tools/prefetch_detection_visual_embedding.py") < dockerfile.index("COPY . /app")
    assert ".models" in dockerignore
    assert ".streamlit/secrets.toml" in dockerignore
