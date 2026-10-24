"""Bounded file parsing in a short-lived subprocess; files are never executed."""

import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import zipfile
from .config import MAX_FILE_BYTES, MAX_TEXT, ROOT
from .schema import ParsedInput

EXTENSIONS = {
    ".txt",
    ".md",
    ".json",
    ".html",
    ".htm",
    ".pdf",
    ".docx",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".wav",
    ".mp3",
    ".ogg",
    ".opus",
    ".amr",
    ".aac",
    ".m4a",
    ".mp4",
    ".mov",
    ".avi",
    ".webm",
    ".apk",
}
IMAGES = {".png", ".jpg", ".jpeg", ".webp"}
AUDIO = {".wav", ".mp3", ".ogg", ".opus", ".amr", ".aac", ".m4a"}
VIDEO = {".mp4", ".mov", ".avi", ".webm"}


def inspect_zip(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        members = z.infolist()
        if len(members) > 5000 or sum(i.file_size for i in members) > 80 * 1024 * 1024:
            raise ValueError("Archive exceeds expansion limits")
        for item in members:
            path = PurePosixPath(item.filename.replace("\\", "/"))
            if path.is_absolute() or ".." in path.parts or item.flag_bits & 1:
                raise ValueError("Unsafe or encrypted archive")
            if item.file_size > max(1024 * 1024, item.compress_size * 200):
                raise ValueError("Suspicious archive compression ratio")
        return {i.filename for i in members}


def validate_upload(name, data):
    ext = Path(name).suffix.lower()
    if ext not in EXTENSIONS:
        raise ValueError("Unsupported file type. Use PPTX instead of legacy PPT.")
    if not data or len(data) > MAX_FILE_BYTES:
        raise ValueError("File must be non-empty and at most 20 MiB")
    if ext == ".pdf" and not data.startswith(b"%PDF-"):
        raise ValueError("File content does not match PDF extension")
    if ext in {".docx", ".pptx", ".apk"}:
        names = inspect_zip(data)
        expected = {
            ".docx": "word/document.xml",
            ".pptx": "ppt/presentation.xml",
            ".apk": "AndroidManifest.xml",
        }[ext]
        if expected not in names:
            raise ValueError("Archive content does not match its extension")
    if ext in IMAGES:
        from PIL import Image

        Image.MAX_IMAGE_PIXELS = 16_000_000
        with Image.open(io.BytesIO(data)) as image:
            if image.width * image.height > 16_000_000:
                raise ValueError("Image exceeds 16 megapixels")
            if image.format not in {"PNG", "JPEG", "WEBP"}:
                raise ValueError("Unsupported image content")
            image.verify()
    if ext in AUDIO | VIDEO:
        plausible = (
            data.startswith((b"RIFF", b"ID3", b"OggS", b"#!AMR", b"\x1a\x45\xdf\xa3"))
            or data[4:8] == b"ftyp"
            or data[0] == 0xFF
        )
        if not plausible:
            raise ValueError("Media header does not match a supported container")
    return ext


def parse_upload(name, data, source):
    ext = validate_upload(name, data)
    with tempfile.TemporaryDirectory(prefix="ridsca-") as directory:
        path = Path(directory) / ("input" + ext)
        path.write_bytes(data)
        result = subprocess.run(
            [sys.executable, "-m", "ridsca.parser_worker", str(path), source],
            cwd=ROOT,
            capture_output=True,
            timeout=50,
            check=False,
        )
        if result.returncode or len(result.stdout) > 250_000:
            raise ValueError("Parser failed or exceeded resource limits")
        obj = json.loads(result.stdout)
        if "error" in obj:
            raise ValueError(obj["error"])
        return ParsedInput.model_validate(obj)


def clamp_text(text):
    return text[:MAX_TEXT], len(text) > MAX_TEXT
