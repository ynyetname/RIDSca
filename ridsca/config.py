from dataclasses import dataclass
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_TOTAL_BYTES = 40 * 1024 * 1024
MAX_FILES = 5
MAX_TEXT = 16000
MAX_CASE_TEXT = 48000
MAX_MEDIA_SECONDS = 120


@dataclass(frozen=True)
class Settings:
    mode: str = "baseline"
    threads: int = 2
    llm_repo: str = "Qwen/Qwen3-4B-GGUF"
    llm_file: str = "Qwen3-4B-Q4_K_M.gguf"
    llm_revision: str = "main"
    embed_model: str = "intfloat/multilingual-e5-small"
    rerank_model: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
    guard_model: str = "protectai/deberta-v3-base-prompt-injection-v2"
    image_model: str = "dima806/ai_vs_real_image_detection"
    audio_model: str = "mo-thecreator/Deepfake-audio-detection"
    whisper_model: str = "small"
    url_index: str = "local_data/url_reputation.csv"
    apk_index: str = "local_data/apk_metadata.sqlite"
    session_ttl: int = 1800

    @classmethod
    def from_env(cls):
        values = {}
        for name, field in cls.__dataclass_fields__.items():
            raw = os.getenv("RIDSCA_" + name.upper(), field.default)
            values[name] = int(raw) if name in {"threads", "session_ttl"} else raw
        if values["mode"] not in {"baseline", "local"}:
            raise ValueError("RIDSCA_MODE must be baseline or local")
        values["threads"] = max(1, min(values["threads"], 8))
        values["session_ttl"] = max(60, min(values["session_ttl"], 3600))
        return cls(**values)
