"""Create/update a private Docker Space from an explicit source-file allowlist."""

import argparse
import os
from pathlib import Path
from huggingface_hub import HfApi, CommitOperationAdd

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {
    "README.md",
    "Dockerfile",
    "app.py",
    "pyproject.toml",
    "requirements.txt",
    "requirements-models.txt",
    "requirements-dev.txt",
    "LICENSE",
    "NOTICE.md",
    "SECURITY.md",
    ".dockerignore",
    ".gitignore",
    ".env.example",
    "compose.yaml",
}
DIRS = {"ridsca", "docs", "scripts", "tests", "data", ".streamlit", ".github"}


def deployment_files(root=ROOT):
    files = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(
            part in {"__pycache__", ".git", ".venv", ".pytest_cache", ".ruff_cache"} for part in rel.parts
        ):
            continue
        if p.name == "secrets.toml" or p.suffix in {".pyc", ".sqlite", ".gguf", ".safetensors"}:
            continue
        if (len(rel.parts) == 1 and p.name in ROOT_FILES) or (
            len(rel.parts) > 1
            and rel.parts[0] in DIRS
            and p.suffix in {".py", ".md", ".json", ".jsonl", ".csv", ".toml", ".yaml", ".yml"}
        ):
            files.append(p)
    return sorted(files)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo_id", help="your-hf-username/ridsca")
    parser.add_argument(
        "--public", action="store_true", help="Explicitly make a NEW Space public (default private)"
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if len(args.repo_id.split("/")) != 2:
        parser.error("Use owner/space-name")
    files = deployment_files()
    if args.dry_run:
        print("\n".join(str(p.relative_to(ROOT)) for p in files))
        return
    token = os.environ.get("HF_TOKEN")
    if not token:
        parser.error("Set HF_TOKEN to a Hugging Face write token; never commit it")
    api = HfApi(token=token)
    api.create_repo(
        repo_id=args.repo_id, repo_type="space", space_sdk="docker", private=not args.public, exist_ok=True
    )
    api.create_commit(
        repo_id=args.repo_id,
        repo_type="space",
        commit_message="Deploy RIDSca application",
        operations=[
            CommitOperationAdd(path_in_repo=str(p.relative_to(ROOT)), path_or_fileobj=str(p)) for p in files
        ],
    )
    print(f"Source uploaded: https://huggingface.co/spaces/{args.repo_id}")
    print(
        "Wait for the Docker build and inspect Space logs. Upload success does not mean the runtime is healthy."
    )


if __name__ == "__main__":
    main()
