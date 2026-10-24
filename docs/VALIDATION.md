# Validation and release status

The baseline test suite exercises case orchestration, input consent, limits,
negated safety advice, English/Hindi patterns, deduplicated categories, invalid
uploads, archive traversal/bombs, offline URL handling, reputation lookup,
APK index behavior, model-output rejection, chat constraints and session
separation. Streamlit AppTest exercises analyze and clear flows.

## Commands

```bash
python -m pip install -r requirements-dev.txt
python -m ruff check .
python -m pytest -q -m "not models"
RIDSCA_MODE=baseline python scripts/evaluate.py --dataset data/evaluation_smoke.jsonl
```

Optional real-model checks require the model dependencies, internet access for
weight downloads and substantial CPU time:

```bash
RIDSCA_MODE=local RUN_MODEL_TESTS=1 python -m pytest tests/test_models_integration.py -v
```

See `docs/BUILD_REPORT.md` for the exact checks completed in the creation
environment, failures/constraints, and untested deployment claims. The code
includes a GitHub CI Docker build/health check, but inclusion of a workflow is
not evidence that it has run successfully on GitHub.

## Do not confuse tests with accuracy

The bundled JSONL contains synthetic functional examples. A passing smoke test
means the implementation follows the expected test behavior. It does not prove
that false alarms, missed scams or deepfake detection are acceptable in the wild.
The evaluation script reports abstentions explicitly; it does not count
inconclusive cases as correct “genuine” classifications.

## Real evaluation plan

1. Obtain licensed/consented messages and media relevant to intended users.
2. Label scam intent separately from media authenticity. Have independent
   reviewers adjudicate ambiguous examples.
3. Group related messages, campaign templates, users, speakers and source videos
   before splitting. No near duplicates across development/test partitions.
4. Hold out new generators, codecs, phone re-recordings, languages and campaigns.
5. Measure false alarms, scam recall (including abstentions), precision, coverage,
   latency p50/p95, and per-language/per-source slices. For media: ROC-AUC/EER
   where appropriate, plus robustness under transformations.
6. Audit whether each explanation is supported, whether a genuine safety reminder
   was misread as a request, and whether follow-up answers add unsupported claims.
7. Fit Platt/isotonic calibration only on a separate validation split, then freeze
   thresholds before final test. Current hand weights are not calibrated.
8. Red-team multilingual prompt injection, malformed documents, huge archives,
   misleading URLs, model outages, concurrency, expiry and deletion.
9. Only after those results establish acceptable operating characteristics,
   consider public release and the advanced temporal/localization research work.

ASVspoof, FaceForensics++, Celeb-DF, FakeAVCeleb and other named datasets are
research candidates from the proposal; no data from them is bundled or falsely
claimed to have been used to train this repository.
