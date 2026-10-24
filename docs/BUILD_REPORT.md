# Build and verification report

Prepared 2026-10-24. Source based on the supplied RIDSca proposal and the requested
Streamlit/Hugging Face/open-model substitutions.

## Completed checks

| Check | Observed result |
|---|---|
| Offline unit, parsing, deployment-filter and Streamlit UI suite | 57 passed; 7 opt-in model tests deselected |
| Real local model integration suite | 7 passed; two third-party SWIG deprecation warnings |
| Ruff static analysis | Passed |
| Python source compilation | Passed |
| Python dependency consistency (`pip check`) | No broken requirements found |
| Streamlit HTTP health endpoint | HTTP 200, `ok` |
| Default model download helper | All seven pinned model repositories downloaded |
| Deployment script dry run | Source allowlist generated; no publication performed |
| Internal Markdown document links | No broken links found |

The real-model suite ran on Linux with Python 3.12 and CPU PyTorch. It exercised:

- Quantized Qwen3-4B structured generation and nested finding schemas.
- Protect AI injection classification.
- Multilingual E5 embeddings and mMiniLM reranking.
- Image classification, audio classification and Whisper transcription plumbing.
- A complete guarded financial-message assessment and follow-up response.
- Explicit handling of an observed injection-guard false positive.

The image/audio smoke inputs were synthetic. They verify that model execution
works, not accuracy on manipulated media. There is no real-world accuracy or
calibration claim. The 12-case synthetic evaluation fixture tests software
behavior only; it must not be presented as a benchmark.

## Corrections discovered during verification

- The pinned llama-cpp binding does not accept `stopping_criteria` in
  `create_chat_completion`. The adapter now uses `create_completion` with an
  explicit Qwen prompt, JSON grammar and token stopping condition.
- Concurrent Hugging Face snapshot downloads exposed a progress-lock race. The
  download helper serializes model snapshots while allowing file concurrency.
- The prompt-injection model can flag ordinary OTP requests. Semantic analysis
  is withheld visibly while deterministic warning findings remain available.
- Qwen sometimes routed a clear next-step question to sources. Clear follow-up
  intents now use deterministic routing; Qwen handles ambiguous questions.

## Not executed or not established

- No Docker image build: Docker was unavailable in the creation environment.
  The Dockerfile and GitHub CI build/health-check job are included but are not
  evidence of a successful Docker build or hosted deployment.
- No live Hugging Face deployment and no GitHub publication: no account or
  deployment credentials were provided. The repository is prepared for these
  actions, not already hosted.
- No real APK maliciousness benchmark, live reputation feed, hardened parser
  sandbox, load test, or production security audit.
- No trained temporal/lip-sync video detector, pixel-level localization masks,
  or calibrated AI-use percentage. See FEATURES.md for full coverage.

## Reproduce

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m pytest -q -m "not models"
# Install model dependencies using README, then:
RIDSCA_MODE=local RUN_MODEL_TESTS=1 python -m pytest tests/test_models_integration.py -v
```

Dependency versions and default model revisions are pinned, but operating-system
packages and all transitive dependencies are not fully locked. Results and
latency can vary across machines and future dependency changes.
