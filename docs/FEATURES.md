# Proposal-to-code coverage

This matrix describes actual behavior, not future claims. The supplied 14-page
RIDSca proposal is the requirements source; its private original is not copied
into the Git repository.

| Proposal element | Implementation | Remaining gap |
|---|---|---|
| Mobile-first assistant | Responsive Streamlit app | No native Android/iOS shell, text-selection hook or OS share extension |
| Related evidence / Add context | Multiple attachments and message in one case; edit and reanalyze | No persistent collaborative cases |
| PDF / DOCX / PPTX / HTML / JSON / TXT | Bounded parsing with coverage notes | Legacy PPT rejected; scanned-PDF OCR and embedded media not read |
| Image OCR / QR | Tesseract English+Hindi; OpenCV QR; payload routed to content and URL analysis | OCR/QR errors possible; UPI payload is text, not a payment authorization or reputation check |
| Voice/video transcription | Local Whisper, timestamps, up to 120 seconds | No diarization; unsupported/quiet media remains unknown |
| Content screening | Transparent rules plus structured Qwen classifications and evidence audit | Not a trained/calibrated financial-scam classifier |
| Hybrid retrieval | BM25, local E5 vectors, reciprocal rank fusion | Seed corpus is very small; no Qdrant service required |
| Reranking | Multilingual cross-encoder, up to 15 candidates, 3 returned | No FlashRank-specific dependency |
| CRAG / web fallback | References and insufficiency status | No live search, autonomous browsing or query-rewrite agent; intentionally excluded to avoid privacy leakage and untrusted browsing |
| URL parser | Offline host/transport/deception/APK-link checks | Does not contact URL, resolve DNS, inspect redirects, fetch TLS or verify page content |
| Google Safe Browsing | Local exact-match threat-index replacement | Live reputation unavailable unless operator supplies/upgrades a feed |
| APK SHA-256 | Implemented | No hash implies identity/authenticity guarantee |
| APK metadata / AndroZoo | Static aapt metadata, optional authorized CSV-to-SQLite import | No bundled AndroZoo corpus; no malware execution, signing trust verification or dynamic analysis |
| Audio spoofing | Pretrained Wav2Vec2, 4-second windows / 2-second stride | Not the proposed XLS-R + BEATs + fusion + AASIST trained architecture; no calibrated SNR/confidence |
| Image detection | Whole-image ViT synthetic-content score | No NPR/frequency fusion, edit localization or masks |
| Video detection | Six sampled image-classifier frames plus audio branch | No face alignment, temporal transformer, face-swap classifier or lip-sync detector |
| Evidence fusion | Repeated category counted once; risk and synthetic-media evidence separate | Weights/thresholds uncalibrated |
| AI percentage | Raw per-input classifier outputs with explicit labels | A scientifically unsupported overall “AI-use percentage” is deliberately not shown |
| Jev guardrails | DeBERTa input/retrieval screen, Qwen audit, strict schemas, constrained output | Not behaviorally equivalent to Jev; English guard limitations and correlated model errors remain |
| Follow-up chat | Clear intents use rules; Qwen routes ambiguous questions; vetted content rendered | Bounded case assistant, not free-form financial advice or arbitrary tool use |
| AWS | Docker deployment on HF Spaces | No AWS infrastructure needed; no actual account deployment performed |
| Privacy | Consent, temporary files, session-only results, clear/expiry, no training/log collection | Not encrypted persistent storage; platform controls apply; idle expiry enforced on interaction |
| Security | Limits, parser subprocess, no shell use for uploaded data, no link visits, non-root Docker | Not a hardened sandbox; no global rate-limited public API |
| Validation | Unit/integration/UI tests and evaluation harness | No held-out real-world dataset benchmark, accuracy claim or calibration |

## Why these deviations are necessary

The PDF describes several architectures that require new model training,
licensed/authorized datasets, calibration, and adversarial evaluation. Installing
a foundation encoder alone does not supply a trained detection head. This code
uses real pretrained checkpoints and exposes missing capabilities instead of
simulating the untrained research components. Their implementation/training is
a separate research milestone, not hidden behind a placeholder success response.
