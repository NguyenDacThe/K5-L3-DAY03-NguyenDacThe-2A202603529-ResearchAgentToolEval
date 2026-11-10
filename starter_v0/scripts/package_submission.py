"""Package the lab source and evidence, excluding local secrets and dependencies."""
from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".venv", "venv", ".git", "__pycache__", ".pytest_cache", "arxiv_papers", "node_modules"}
SUFFIXES = {".py", ".md", ".yaml", ".yml", ".json", ".csv", ".toml", ".ini", ".txt"}


def main():
    secrets = []
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            value = value.strip().strip("\"'")
            if ("KEY" in key or "TOKEN" in key) and len(value) >= 12:
                secrets.extend([value.encode("utf-8"), value.encode("utf-16-le")])
    files = []
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        if p.name.startswith(".env") and p.name != ".env.example":
            continue
        if p.suffix not in SUFFIXES and p.name not in {".env.example", ".gitignore"}:
            continue
        if any(secret in p.read_bytes() for secret in secrets):
            raise RuntimeError(f"Configured secret detected in submission file: {p.relative_to(ROOT)}")
        files.append(p)
    output = ROOT.parent / "submission_v3.zip"
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for p in files:
            archive.write(p, Path("starter_v0") / p.relative_to(ROOT))
    with ZipFile(output) as archive:
        assert archive.testzip() is None
        assert all("/.venv/" not in name and not name.endswith("/.env") for name in archive.namelist())
    print(f"Packaged {len(files)} files: {output.name}; configured keys excluded and archive verified.")


if __name__ == "__main__":
    main()
