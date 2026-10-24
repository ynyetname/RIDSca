"""Prefetch exact default checkpoints without loading inference runtimes."""

import argparse
import json
from pathlib import Path
from huggingface_hub import hf_hub_download, snapshot_download

ROOT = Path(__file__).resolve().parents[1]


def download(repo, info, workers=2):
    if repo == "Qwen/Qwen3-4B-GGUF":
        hf_hub_download(repo, "Qwen3-4B-Q4_K_M.gguf", revision=info["revision"])
    else:
        patterns = ["model.safetensors", "*.json", "*.txt", "*.model"]
        if repo == "Systran/faster-whisper-small":
            patterns = [
                "config.json",
                "model.bin",
                "tokenizer.json",
                "vocabulary.*",
                "preprocessor_config.json",
            ]
        snapshot_download(
            repo,
            revision=info["revision"],
            allow_patterns=patterns,
            ignore_patterns=["checkpoint-*/*", "onnx/*", "openvino/*"],
            max_workers=workers,
        )
    print(f"Ready: {repo}@{info['revision']}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-only", action="store_true", help="Skip image, audio and Whisper models")
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    lock = json.loads((ROOT / "data/models.lock.json").read_text())
    if args.text_only:
        lock = {
            k: v
            for k, v in lock.items()
            if k.startswith(("Qwen/", "intfloat/", "cross-encoder/", "protectai/"))
        }
    # Snapshot progress locks are process-global; serialize model snapshots.
    # Files within one snapshot may still download concurrently.
    for repo, info in lock.items():
        download(repo, info, workers=max(1, min(4, args.workers)))
    print("Downloaded the default models. Custom model environment overrides are not prefetched.")


if __name__ == "__main__":
    main()
