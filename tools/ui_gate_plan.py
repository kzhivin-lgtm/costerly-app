"""Classify changes cumulatively against production, never just the last push."""
from pathlib import PurePosixPath
import subprocess


def needs_full_gate(paths: list[str]) -> bool:
    protected_docs = {"notes/UI_GUIDELINES.md"}
    return any(path in protected_docs or not (
        path == "README.md" or (path.startswith("notes/") and PurePosixPath(path).suffix == ".md")
    ) for path in paths)


if __name__ == "__main__":
    changed = subprocess.check_output(["git", "diff", "--name-only", "-z", "origin/main...HEAD"])
    paths = changed.decode().strip("\0").split("\0") if changed else []
    print("full=" + str(needs_full_gate(paths)).lower())
