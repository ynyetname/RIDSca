# Deployment runbook

## Hugging Face

The repository's README front matter declares `sdk: docker` and `app_port: 7860`.
Docker runs as UID 1000 and binds Streamlit to `0.0.0.0:7860`. Model weights are
not built into the image. They load lazily into `/home/user/.cache/huggingface`.
The application has no AWS SDK or AWS configuration.

Hugging Face's current documentation says compute Spaces on CPU Basic require
a paid subscription even though hardware has no hourly cost. Confirm eligibility
before starting. Do not silently select paid GPU hardware. This implementation
makes no promise of free hosting or an account quota/grant.

Sources:
- https://huggingface.co/docs/hub/en/spaces-overview
- https://huggingface.co/docs/hub/en/spaces-sdks-docker
- https://huggingface.co/docs/hub/en/spaces-sdks-streamlit
- https://huggingface.co/docs/huggingface_hub/en/guides/manage-spaces

Use a **private Space** for pilot submissions. A public Space exposes the app
without per-user login. Streamlit's session separation is not application-level
access control. Do not upload real financial data to an untrusted public demo.

## Publishing from GitHub

1. Commit the extracted folder to your GitHub repository.
2. Set repository variable `HF_SPACE_ID` to `owner/space-name`.
3. Set repository secret `HF_TOKEN` to a least-privilege write token for that Space.
4. Create the GitHub Actions environment `huggingface`. Optional required reviewers
   can protect deployment in a team repository.
5. Run the `Deploy to Hugging Face` workflow manually.
6. Check HF build logs, then visit the Space and submit a synthetic case.

The script uploads an allowlist. It will not delete unrelated files in an
existing Space. Use a fresh Space for an exact clean deployment. No credentials
are embedded in this repository. The delivery does not create or publish a
GitHub repository or a Hugging Face Space on your behalf.

## Runtime checks

```bash
python scripts/doctor.py
curl --fail http://localhost:7860/_stcore/health
```

A healthy HTTP endpoint means the UI server started; it does not prove all model
weights are present. Run the opt-in model integration tests and inspect coverage
with text, image and voice samples before your demonstration.

## Common problems

| Symptom | Action |
|---|---|
| HF 402 / subscription error | Check current compute-Space eligibility; run locally if no eligible plan |
| Model unavailable | Inspect disk/network/Hub access, dependency installation and explicit model file/revision |
| Slow first submission | Weight downloads and cold model initialization; warm with synthetic samples |
| llama-cpp build fails | Install C++ build tools/CMake; on Linux explicitly set `CC=gcc CXX=g++` if compiler variables are stale |
| Local RAM exhausted | Use baseline or smaller Qwen checkpoint; reduce concurrent workloads; do not infer a result from a crash |
| OCR unavailable | Install `tesseract-ocr-eng` and `tesseract-ocr-hin` |
| APK metadata unavailable | Install `aapt`; SHA-256 still works |
| Missing reputation | Supply a properly sourced local index; no match remains unknown |
| Restart loses cache/results | HF default disk is ephemeral; session-only results intentionally do not persist |

## Before a public service

Add authentication, real rate limits, an external job queue, hard per-job resource
limits, stronger parser isolation, malware-safe storage, privacy review, real
held-out evaluation, model calibration and incident handling. Do not infer that
Docker alone makes malicious uploads safe. See SECURITY.md and FEATURES.md.
