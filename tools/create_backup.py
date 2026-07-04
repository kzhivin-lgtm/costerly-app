from __future__ import annotations

import argparse
import sys
import zipfile
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKUP_ROOT = REPO_ROOT / "backups"
EXCLUDED_DIRS = {".git", ".venv", ".streamlit", "__pycache__", "backups"}
EXCLUDED_FILES = {".DS_Store"}
REQUIRED_FILES = {"app.py", "notes/DONE_LOG.md"}
MAX_ARCHIVE_BYTES = 5 * 1024 * 1024


def main() -> int:
    args = parse_args()
    folder_name = f"{args.version}_{args.slug}"
    backup_dir = BACKUP_ROOT / folder_name
    backup_path = backup_dir / f"costerly-app_{folder_name}_{date.today().isoformat()}.zip"

    backup_dir.mkdir(parents=True, exist_ok=True)
    if backup_path.exists():
        raise SystemExit(f"Backup already exists: {backup_path}")

    try:
        create_archive(backup_path)
        validate_archive(backup_path)
    except Exception:
        if backup_path.exists():
            backup_path.unlink()
        raise

    print(f"Created backup: {backup_path}")
    print(f"Size: {backup_path.stat().st_size:,} bytes")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a validated local Costerly backup archive.",
    )
    parser.add_argument("version", help="Version label, for example v2.01.35")
    parser.add_argument("slug", help="Short backup slug, for example before_next_task")
    return parser.parse_args()


def create_archive(backup_path: Path) -> None:
    with zipfile.ZipFile(backup_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(REPO_ROOT.rglob("*")):
            relative = path.relative_to(REPO_ROOT)
            if should_exclude(relative):
                continue
            if path.is_dir():
                continue
            archive.write(path, relative.as_posix())


def should_exclude(relative: Path) -> bool:
    parts = set(relative.parts)
    if parts & EXCLUDED_DIRS:
        return True
    return relative.name in EXCLUDED_FILES


def validate_archive(backup_path: Path) -> None:
    with zipfile.ZipFile(backup_path) as archive:
        names = set(archive.namelist())
        bad_names = sorted(name for name in names if archive_name_is_excluded(name))
        missing = sorted(name for name in REQUIRED_FILES if name not in names)

    if bad_names:
        sample = "\n".join(bad_names[:20])
        raise RuntimeError(f"Backup contains excluded paths:\n{sample}")
    if missing:
        raise RuntimeError(f"Backup is missing required files: {', '.join(missing)}")

    size = backup_path.stat().st_size
    if size > MAX_ARCHIVE_BYTES:
        raise RuntimeError(
            f"Backup is unexpectedly large: {size:,} bytes "
            f"(limit {MAX_ARCHIVE_BYTES:,} bytes)"
        )


def archive_name_is_excluded(name: str) -> bool:
    relative = Path(name)
    return should_exclude(relative)


if __name__ == "__main__":
    sys.exit(main())
