"""Offline environment checks; does not download model weights."""

import importlib.util
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from ridsca.config import Settings

load_dotenv()
s = Settings.from_env()
print(f"Python {sys.version.split()[0]}; mode={s.mode}")
modules = ["streamlit", "pydantic", "pypdf", "PIL", "cv2", "pytesseract", "docx", "pptx"]
if s.mode == "local":
    modules += ["torch", "transformers", "sentence_transformers", "faster_whisper", "llama_cpp"]
missing = []
for mod in modules:
    found = bool(importlib.util.find_spec(mod))
    print(f"{'OK' if found else 'MISSING'} Python module: {mod}")
    if not found:
        missing.append(mod)
for exe in ["ffmpeg", "ffprobe", "tesseract", "aapt"]:
    found = shutil.which(exe)
    print(f"{'OK' if found else 'OPTIONAL MISSING'} command: {exe}")
print("Local models:", s.llm_repo, s.llm_file)
print("Model weights, real inference, GPU performance, and HF account eligibility were NOT checked.")
sys.exit(bool(missing))
