# RIDSca — check before you trust

**Risk Intelligence & Detection for Scams · Team SCAMURAI · IIT Roorkee**

A runnable Streamlit research prototype based on the RIDSca proposal. It connects
messages, documents, QR payloads, voice, images, video and APK metadata into one
case, shows evidence and missing checks, and answers bounded follow-up questions.
Inference runs locally with open-weight models. No Jev, Gemini, Bedrock, AWS,
paid inference endpoint, or externally hosted vector database is required.

**Status:** application and deployment source, with 57 passing offline/UI tests and 7 passing real-model integration tests. This is
not a trained reproduction of all research architectures in the proposal, a
production fraud engine, or a guarantee of authenticity. Read
[feature coverage](docs/FEATURES.md) and [validation](docs/VALIDATION.md) before a demo.

## Start here

### Option A: Docker — complete dependencies

Install Docker Desktop / Docker Engine, then run from this directory:

```bash
docker compose up --build
```

Open **http://localhost:7860**. This includes FFmpeg, English/Hindi Tesseract, aapt,
CPU PyTorch and the local models' runtimes. Weights download on first use; allow
several GB of disk space and several minutes. Aim for **16 GB system RAM** and
at least 15 GB free disk; these are planning estimates, not measured minimums.
The model cache survives local container restarts; cases do not persist.

For a fast first demo with no model downloads:

```bash
RIDSCA_MODE=baseline docker compose up --build
```

PowerShell equivalent:

```powershell
$env:RIDSCA_MODE="baseline"
docker compose up --build
```

### Option B: Python — lightweight baseline

Use Python **3.11 or 3.12**. Run from the repository root.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows, activate with `.venv\Scripts\Activate.ps1`. Baseline is the default
when no `.env` exists: it starts without downloading AI models. OCR, audio/video
container parsing and APK manifest parsing require system tools; missing tools
appear as explicit coverage gaps. PDF, DOCX, PPTX, text and URL checks still work.

### Enable local AI models

On Debian/Ubuntu (Docker already includes these):

```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake ffmpeg tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin aapt
python -m pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
CMAKE_ARGS="-DGGML_NATIVE=OFF -DGGML_OPENMP=ON" python -m pip install -r requirements-models.txt
cp .env.example .env
python scripts/doctor.py
python -m streamlit run app.py
```

Windows users should prefer Docker/WSL2 for the complete stack. Native
`llama-cpp-python` installation requires a supported C++ compiler. Keep `.env`
out of Git. A Hugging Face token is optional for downloads; no inference API
key is needed. Full model tests download weights and are explicitly opt-in.

## What happens in a case

1. Consent and size/type validation; each file is parsed in a bounded subprocess.
2. Extract text, QR payloads, OCR and (in local mode) speech transcripts.
3. Run content rules, guarded local semantic classification, offline URL checks,
   static APK analysis and available experimental media detectors.
4. Retrieve a small curated advisory corpus using BM25 + multilingual embeddings,
   fuse ranks and rerank with a multilingual cross-encoder.
5. Deduplicate correlated warning categories, produce a preliminary risk band,
   display coverage gaps and offer vetted next steps.
6. Download a JSON case report; ask follow-ups or add context and reanalyze.

A missing model never returns a fabricated score. No warning indicators means
**Inconclusive**, not automatically safe. Low/suspicious/high bands use the
proposal's 0–39 / 40–69 / 70–100 thresholds only when supported risk indicators
exist. They are **hand-weighted, uncalibrated triage scores**.

Media scores are displayed separately. They **never increase scam risk by
 themselves**, and are not an “AI-use percentage.”

## Model choices

| Task | Default | Reason / limit |
|---|---|---|
| Contextual classifications, evidence audit, follow-up routing | Qwen3-4B GGUF Q4_K_M | Permissive, multilingual, quantized CPU deployment; slower than a small classifier |
| Jev input/retrieval screening replacement | Protect AI DeBERTa v3 prompt-injection v2 + rules | Local classifier; English-focused and upstream project archived; not a complete Jev equivalent |
| Output guard | Pydantic schemas, exact evidence quotes, Qwen audit, vetted output templates | No arbitrary model-generated advice is released; audit can still misjudge evidence |
| Dense retrieval | multilingual-e5-small | Compact multilingual embeddings; local vectors, no Qdrant service |
| Reranking | mmarco-mMiniLMv2-L12-H384-v1 | Multilingual cross-encoder; reused across the case |
| Speech recognition | faster-whisper `small`, int8 CPU | Multilingual; lower latency/quality tradeoff than large-v3 |
| Audio synthetic-content classifier | mo-thecreator/Deepfake-audio-detection | Pretrained Wav2Vec2; experimental and incompletely documented training data |
| Image / sampled video frame classifier | dima806/ai_vs_real_image_detection | ViT synthetic-image classifier; not a temporal video or face-swap detector |
| OCR / QR | Tesseract eng+hin / OpenCV | Free, local, no vision LLM needed |

These are practical CPU-compatible choices, **not a claim of universal
state-of-the-art performance**. No project-specific benchmark supports “best.”
[Model decisions and licenses](docs/MODELS.md) explain alternatives and gaps.
Weights are not bundled in this Git repository. To download the pinned default
checkpoints before a demo, run `python scripts/download_models.py` (or add
`--text-only` to omit media models).

## Deploy to Hugging Face Spaces

Use a **Docker Space**, not the deprecated built-in Streamlit SDK.

1. Create a Hugging Face account and verify eligibility for Docker Spaces.
2. Create a **private Docker Space**, such as `your-name/ridsca`.
3. Add the repository contents to it, keeping this README's YAML header.
4. Select CPU Basic when available. Set `RIDSCA_MODE=local` in Space variables
   (the Dockerfile already defaults to local). Optional `HF_TOKEN` belongs in
   **Space Secrets**, never source files.
5. Wait for the build, open the app, submit an example, and inspect **Check coverage**.

Or deploy using the included script:

```bash
# Set HF_TOKEN securely in your shell/session first.
python scripts/deploy_hf.py your-name/ridsca --dry-run
python scripts/deploy_hf.py your-name/ridsca
```

The script creates a private Space by default and does not upgrade hardware.
`--public` explicitly creates a new public Space. It does not change visibility
of an existing Space. Deployment source is allowlisted; secrets, uploaded files,
local intelligence indexes and model weights are excluded.

**Cost clarification, checked 2026-10-23:** Hugging Face currently documents
CPU Basic as having no hourly hardware charge, but requires a paid plan for new
compute Spaces (Docker/Gradio). Thus a completely free Hugging Face deployment
cannot be promised. Local use has no per-call model/API fee. See
[official Spaces overview](https://huggingface.co/docs/hub/en/spaces-overview).
No live Space has been created by this repository's delivery.

[Detailed deployment guide](docs/DEPLOYMENT.md) includes GitHub Actions setup,
troubleshooting, cold-start behavior and operating limits.

## Put this on GitHub

Extract this folder and open a terminal inside it. Create an empty GitHub
repository through your account, then:

```bash
git init
git add .
git commit -m "Build RIDSca Streamlit prototype"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ridsca.git
git push -u origin main
```

Replace `YOUR_USERNAME`. Review `git diff --cached` before committing. The
original private PDF, model weights, user cases and tokens are not bundled.

Optional deployment automation: set GitHub Actions secret `HF_TOKEN` and
repository variable `HF_SPACE_ID=your-name/ridsca`; create the `huggingface`
environment, then run **Deploy to Hugging Face** manually. CI runs on pushes/PRs;
deployment does not run automatically on every push.

## Tests and evaluation

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m pytest -q -m "not models"
python scripts/evaluate.py --dataset data/evaluation_smoke.jsonl
```

Real model integration tests:

```bash
RIDSCA_MODE=local RUN_MODEL_TESTS=1 python -m pytest tests/test_models_integration.py -v
```

The tiny synthetic evaluation fixtures are functional smoke tests, **not** an
accuracy benchmark. See [validation methodology](docs/VALIDATION.md).

## Local threat intelligence

URL reputation is exact-match against an operator-supplied CSV. Without it,
only lexical checks run. The bundled example CSV is synthetic and is **not
loaded automatically**. Place a real authorized feed at
`local_data/url_reputation.csv`; required columns are
`url,verdict,source,observed_at`. Only `verdict=malicious` adds a known-threat
indicator. Never interpret a missing record as safe.

For authorized APK metadata (including an AndroZoo-format CSV):

```bash
python scripts/import_apk_metadata.py /path/to/authorized.csv
```

This imports only hash metadata into SQLite; it does not download APKs or
execute uploaded packages. Access to AndroZoo data is subject to its own terms.
No scanner/reputation API account is silently required.

## Repository map

```text
app.py                     Streamlit input, result, evidence and chat UI
ridsca/service.py          Case orchestration and shared model lock
ridsca/models.py           Local open-model loading and structured inference
ridsca/parsing.py          Upload validation and bounded parser subprocess
ridsca/parser_worker.py    Text/document/OCR/QR/media/APK parsing
ridsca/retrieval.py        BM25 + dense retrieval + reranking
ridsca/urls.py             Offline URL analysis and local reputation
ridsca/apk.py              Static permission and hash-index checks
ridsca/media.py            Transcripts, audio windows, image/video-frame scores
ridsca/fusion.py           Deduplicated, preliminary risk scoring
ridsca/guardrails.py       Injection rules, evidence checks, redaction
ridsca/schema.py           Strict typed contracts
scripts/                   CLI, diagnostics, evaluation, index import, deployment
data/                      Curated references and synthetic fixtures
tests/                     Offline, UI, deployment and opt-in model checks
docs/                      Architecture, coverage, deployment and validation
.github/workflows/         CI and manually triggered HF deployment
```

## Privacy and limitations

Cases stay in session memory; only temporary parser files are written and then
removed. **No claim of forensic secure erasure** is made. Upload widgets also
hold memory; use Clear case. Idle case state is cleared on the next interaction
after 30 minutes; disconnected sessions expire after 60 seconds. No persistent
case database or training collection exists. JSON exports may still contain
sensitive metadata despite best-effort excerpt redaction.

Use a private Space for a controlled pilot. Resource limits and subprocesses
are defense in depth, not a complete hostile-file sandbox. The app has no
public-service authentication, IP rate limiter, queue, or high-availability
backend. See [SECURITY.md](SECURITY.md). Do not expose it as a production
malware-analysis service without additional isolation and review.
