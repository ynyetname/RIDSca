# Model decisions, rights and replacement points

Checked against publisher model cards on 2026-10-23. Model weights are separate
from the MIT application code. Check their current terms before redistribution.
Repository revisions are recorded in `data/models.lock.json` and used by loaders
for the default models. Custom models require compatible output labels/schemas.

| Model | License stated by publisher | Role |
|---|---|---|
| [Qwen/Qwen3-4B-GGUF](https://huggingface.co/Qwen/Qwen3-4B-GGUF) | Apache-2.0 | Contextual classifications, structured audit, chat routing |
| [ProtectAI/deberta-v3-base-prompt-injection-v2](https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2) | Apache-2.0 | Input and retrieved-reference injection screening |
| [intfloat/multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small) | MIT | Dense retrieval |
| [cross-encoder/mmarco-mMiniLMv2-L12-H384-v1](https://huggingface.co/cross-encoder/mmarco-mMiniLMv2-L12-H384-v1) | Apache-2.0 | Reranking |
| [SYSTRAN/faster-whisper-small](https://huggingface.co/Systran/faster-whisper-small) | MIT | Whisper small in CTranslate2 format |
| [mo-thecreator/Deepfake-audio-detection](https://huggingface.co/mo-thecreator/Deepfake-audio-detection) | Apache-2.0 | Wav2Vec2 audio classification |
| [dima806/ai_vs_real_image_detection](https://huggingface.co/dima806/ai_vs_real_image_detection) | Apache-2.0 | ViT image classification |

The code loads Hugging Face neural checkpoints with safetensors and remote custom
code disabled. Llama.cpp loads the official quantized GGUF. No hosted inference
provider is contacted. Hugging Face receives model-download requests; your case
text is not included in those requests.

## Why not claim “best”?

“Best” depends on language, operating cost, hardware, latency, and the exact
scam/deepfake distribution. There is no benchmark on RIDSca's intended users.
The defaults are CPU-feasible choices under a permissive-license constraint.
A larger Qwen model can improve reasoning but needs more memory and time.
Whisper large-v3 can improve transcription but is a poor default for a two-core
Space. Neither improvement proves better fraud detection without testing.

All content/link/APK data reaches one evidence system; numeric URL parsing,
hashes, archive checks and permissions are handled by code rather than asking
an LLM to invent facts. Qwen is used where semantic judgments are useful, and
can only emit defined categories, verbatim evidence or existing IDs.

## Jev replacement

[TypeSafe's model documentation](https://docs.typesafe.ai/models) lists Jev as
charging for input tokens. This project has no Jev client and no paid API call.
Its replacement is a layered workflow, not a claim of identical speed,
calibration or accuracy:

- DeBERTa + conservative rules screen text/references for prompt injection.
- A strict JSON grammar and Pydantic reject unknown fields and categories.
- Exact supporting quotes are required for semantic findings.
- A second structured Qwen pass audits support; rejected results are withheld.
- Risk scores and final advice are produced by backend rules.
- Chat returns existing evidence and vetted templates; the model cannot output
  arbitrary links, contact numbers, claims or action instructions.

The Protect AI project is archived, and the model card states English-focused
coverage and no general jailbreak detection. It is one defense, not a security
boundary. Hindi/other-language attacks may be missed. The smoke tests also observed false positives on ordinary OTP-request text; in
that case the UI reports withheld semantic analysis while retaining rule findings.
A separate guard model, held-out multilingual red-team set, and sandbox hardening remain necessary for
public deployment. Reusing Qwen for generation and audit can repeat the same
mistake. Exact quote validation does not establish semantic truth.

## Detector interpretation

The audio model maps `fake` to index 0 and `real` to index 1; the image model maps
`FAKE` to index 1 and `REAL` to index 0. The application looks up explicit labels
and refuses unknown `LABEL_0`-style mappings. Never hardcode fake=1 globally.
Their published in-domain accuracy numbers are not copied into this app as
RIDSca performance. Compression, re-recording, background noise, language and
unseen generators can change results substantially.

Video frames reuse the image classifier as an exploratory signal. They do not
constitute a temporal deepfake detector. No manipulation masks are fabricated.

## Reproducibility

`data/models.lock.json` records publisher revisions. Application package versions
are pinned in requirements files; transitive dependencies and OS images are not
fully locked, so this is not a bit-for-bit reproducible build. Review updates and
run CI/model smoke tests before changing any model revision or package version.
