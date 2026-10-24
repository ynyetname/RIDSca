# RIDSca(Risk Intelligence & Detection for Scams)

RIDSca helps people review suspicious financial messages, links, documents, media, and APK files before taking action. Built with **Streamlit** and **local open-weight models**, it brings warning signs, supporting evidence, and practical next steps into one interface.

> Research prototype: assessments are preliminary and do not guarantee safety or authenticity.

## Features

- **Combined case analysis:** Review messages and related attachments together.
- **Document extraction:** Read PDF, DOCX, PPTX, HTML, JSON, and text files.
- **OCR and QR decoding:** Extract English/Hindi text and QR payloads from images.
- **Content assessment:** Identify warning signs using rules and guarded local-model analysis.
- **Evidence retrieval:** Combine BM25, multilingual embeddings, and reranking.
- **URL and APK checks:** Inspect URLs offline, hash APKs, and review available metadata.
- **Experimental media checks:** Transcribe speech and classify audio, images, and sampled video frames.
- **Reports and follow-up:** Explore findings, ask case-specific questions, and export JSON reports.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | Python, Pydantic |
| Contextual analysis | Qwen3-4B GGUF |
| Injection screening | Protect AI DeBERTa + backend rules |
| Retrieval | BM25 + multilingual E5 |
| Reranking | Multilingual MiniLM cross-encoder |
| Transcription | Faster Whisper |
| Media classification | Pretrained Wav2Vec2 and ViT checkpoints |
| OCR and QR | Tesseract, OpenCV |
| Deployment | Docker, Hugging Face Spaces |

Model versions and selection details are documented in [docs/MODELS.md](docs/MODELS.md).

## Quick Start

Requires **Python 3.11 or 3.12**. Python 3.11 is recommended.

### 1. Clone the repository

```bash
git clone https://github.com/ynyetname/RIDSca.git
cd RIDSca
```

### 2. Create a Conda environment

```bash
conda create -n ridsca python=3.11 -y
conda activate ridsca
```

If the environment already exists, only activate it.

### 3. Install and run

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open **http://localhost:7860**.

The default Python setup starts in **baseline mode**, without AI model downloads. OCR, media parsing, and APK metadata extraction require additional system tools.

## Full Local AI Setup

The Docker configuration includes the model runtimes and system dependencies:

```bash
docker compose up --build
```

It defaults to local AI mode and downloads model weights on first use. Plan for approximately **16 GB RAM** and **15 GB free disk space**; actual requirements vary.

For setup without Docker, see [deployment instructions](docs/DEPLOYMENT.md) and `.env.example`. Windows users can use Docker Desktop or WSL2 for the complete stack.

## How It Works

1. Paste a message or upload related files.
2. Confirm consent and start the analysis.
3. Review the risk assessment and supporting evidence.
4. Check which analyses were completed, unavailable, or inconclusive.
5. Ask follow-up questions or download the report.

Repeated warning categories are counted once. Media classifier scores remain separate from financial scam risk.

## Hugging Face Deployment

Create a **Docker Space**, preserve this README's configuration header, and upload the repository.

Alternatively, set `HF_TOKEN` securely and run:

```bash
python scripts/deploy_hf.py YOUR_HF_USERNAME/ridsca --dry-run
python scripts/deploy_hf.py YOUR_HF_USERNAME/ridsca
```

The script creates a private Space by default. Manual deployment through GitHub Actions is also included.

Local inference requires no paid API. Hugging Face hosting eligibility and charges are separate—check the platform's current terms before deployment.

## Testing

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m pytest -q -m "not models"
```

Recorded verification: **57 offline/UI tests** and **7 real-model integration tests** passed. These are software checks, not evidence of real-world detection accuracy.

See [docs/BUILD_REPORT.md](docs/BUILD_REPORT.md) for the verification scope.

## Limitations and Privacy

- Risk scores are uncalibrated indicators, not probabilities of fraud.
- No detected warning signs does not establish safety.
- Video analysis uses sampled frames; temporal detection, lip-sync verification, and manipulation heatmaps are not implemented.
- Model guardrails can make mistakes or withhold semantic analysis.
- Cases are processed on the hosting machine and held in session memory.
- Submitted URLs are not visited, and uploaded APKs are not executed.
- Public deployment requires additional security and operational controls.

See [SECURITY.md](SECURITY.md) and the [feature coverage matrix](docs/FEATURES.md).

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Features and research gaps](docs/FEATURES.md)
- [Models and licenses](docs/MODELS.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Validation](docs/VALIDATION.md)

## License

Application code is licensed under the [MIT License](LICENSE). Models and dependencies retain their respective licenses.

