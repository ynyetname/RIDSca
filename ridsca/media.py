import io
from pathlib import Path
import subprocess
import tempfile
from .config import MAX_MEDIA_SECONDS
from .schema import Check, MediaSignal


def analyze_media(data, ext, parsed, models):
    signals, checks, transcript = [], [], ""

    def note(component, status, detail):
        checks.append(Check(component=component, status=status, detail=detail, source=parsed.source))

    if models.s.mode != "local":
        note(
            "Media models",
            "skipped",
            "Baseline mode: no media authenticity model or speech recognition was run.",
        )
        return signals, checks, transcript
    if parsed.kind == "image":
        try:
            from PIL import Image

            with Image.open(io.BytesIO(data)) as im:
                score = models.image_score(im.convert("RGB"))
            signals.append(
                MediaSignal(
                    source=parsed.source, modality="image", model=models.s.image_model, raw_score=score
                )
            )
            note(
                "Image detector",
                "partial",
                "Whole-image synthetic-content classifier; not a face-swap detector, edit localizer, or authenticity certification.",
            )
        except Exception:
            note(
                "Image detector",
                "unavailable",
                "Model could not produce a score; authenticity remains unknown.",
            )
        return signals, checks, transcript
    with tempfile.TemporaryDirectory(prefix="ridsca-media-") as directory:
        path = Path(directory) / ("input" + ext)
        path.write_bytes(data)
        duration = min(float(parsed.metadata.get("duration", 0)), MAX_MEDIA_SECONDS)
        if parsed.metadata.get("duration", 0) > MAX_MEDIA_SECONDS:
            note("Media coverage", "partial", f"Only the first {MAX_MEDIA_SECONDS}s were analyzed.")
        if parsed.metadata.get("has_audio"):
            try:
                import numpy as np

                result = subprocess.run(
                    [
                        "ffmpeg",
                        "-v",
                        "error",
                        "-nostdin",
                        "-protocol_whitelist",
                        "file,pipe",
                        "-i",
                        str(path),
                        "-t",
                        str(MAX_MEDIA_SECONDS),
                        "-vn",
                        "-ac",
                        "1",
                        "-ar",
                        "16000",
                        "-f",
                        "f32le",
                        "pipe:1",
                    ],
                    capture_output=True,
                    timeout=30,
                    check=True,
                )
                samples = np.frombuffer(result.stdout, dtype=np.float32).copy()
                if len(samples) < 8000 or not np.isfinite(samples).all():
                    raise ValueError("Insufficient usable audio")
                rms = float(np.sqrt(np.mean(samples**2)))
                clipped = float(np.mean(abs(samples) > 0.99))
                if rms < 0.002:
                    note(
                        "Audio quality",
                        "partial",
                        "Near-silence; speech recognition and spoof scoring withheld.",
                    )
                else:
                    note(
                        "Audio quality",
                        "partial" if clipped > 0.01 else "complete",
                        f"RMS={rms:.4f}; clipping fraction={clipped:.4f}. Not an SNR or reliability calibration.",
                    )
                    try:
                        segments, language = models.transcribe(samples)
                        transcript = "\n".join(
                            f"[{s['start']:.1f}-{s['end']:.1f}s] {s['text']}" for s in segments
                        )
                        note(
                            "Speech recognition",
                            "partial",
                            f"Whisper transcript; detected language {language}. May mishear names, numbers or speech.",
                        )
                    except Exception:
                        note(
                            "Speech recognition",
                            "unavailable",
                            "Whisper unavailable; no transcript inferred.",
                        )
                    try:
                        # 4s windows / 2s stride, bounded to first 120s. Ignore quiet windows.
                        windows = 0
                        for start in range(0, max(1, len(samples) - 8000), 32000):
                            window = samples[start : start + 64000]
                            if len(window) < 8000 or float(np.sqrt(np.mean(window**2))) < 0.002:
                                continue
                            score = models.audio_score(window)
                            signals.append(
                                MediaSignal(
                                    source=parsed.source,
                                    modality="audio",
                                    model=models.s.audio_model,
                                    raw_score=score,
                                    start=start / 16000,
                                    end=(start + len(window)) / 16000,
                                )
                            )
                            windows += 1
                            if start + 64000 >= len(samples):
                                break
                        note(
                            "Audio spoof detector",
                            "partial",
                            f"Scored {windows} windows. Uncalibrated Wav2Vec2 classifier; real-world and language generalization unverified.",
                        )
                    except Exception:
                        note(
                            "Audio spoof detector",
                            "unavailable",
                            "Detector failed; any completed windows are partial only.",
                        )
            except Exception:
                note("Audio decoding", "failed", "Unable to obtain usable bounded audio.")
        else:
            note("Audio stream", "skipped", "No audio stream found.")
        if parsed.kind == "video":
            # ffmpeg limits scale before raster decode; no remote inputs/playlist protocols.
            for n in range(6):
                timestamp = duration * (n + 0.5) / 6
                try:
                    from PIL import Image

                    result = subprocess.run(
                        [
                            "ffmpeg",
                            "-v",
                            "error",
                            "-nostdin",
                            "-protocol_whitelist",
                            "file,pipe",
                            "-ss",
                            str(timestamp),
                            "-i",
                            str(path),
                            "-frames:v",
                            "1",
                            "-vf",
                            "scale=640:-2",
                            "-f",
                            "image2pipe",
                            "-vcodec",
                            "png",
                            "pipe:1",
                        ],
                        capture_output=True,
                        timeout=15,
                        check=True,
                    )
                    with Image.open(io.BytesIO(result.stdout)) as im:
                        score = models.image_score(im.convert("RGB"))
                    signals.append(
                        MediaSignal(
                            source=parsed.source,
                            modality="video_frame",
                            model=models.s.image_model,
                            raw_score=score,
                            start=round(timestamp, 2),
                        )
                    )
                except Exception:
                    note(
                        "Video frame classifier",
                        "unavailable",
                        "Frame extraction or model failed; no whole-video authenticity conclusion.",
                    )
                    break
            note(
                "Video forensic coverage",
                "partial",
                "Up to 6 sampled frame scores only. Temporal face-swap detection, lip-sync analysis, face alignment and localization are not implemented.",
            )
    return signals, checks, transcript
