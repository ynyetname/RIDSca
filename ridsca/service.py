"""One bounded case pipeline used by Streamlit, CLI, and tests."""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import threading
import uuid
from .apk import analyze_apk
from .config import MAX_FILES, MAX_TEXT, MAX_CASE_TEXT, MAX_TOTAL_BYTES
from .fusion import ACTIONS, fuse
from .guardrails import has_injection, redact, safe_question, explicit_chat_topic
from .media import analyze_media
from .models import LocalModels
from .parsing import parse_upload
from .retrieval import Retriever
from .rules import scan, finding
from .schema import Check, Report
from .urls import analyze_url, extract_urls


class BusyError(RuntimeError):
    pass


class Analyzer:
    def __init__(self, settings, models=None):
        self.settings = settings
        self.models = models or LocalModels(settings)
        self.retriever = Retriever(self.models)
        self.lock = threading.Lock()

    def analyze(self, text="", uploads=(), consent=False):
        if not consent:
            raise ValueError("Consent is required before analysis")
        if not text.strip() and not uploads:
            raise ValueError("Add text or at least one file")
        if (
            len(text) > MAX_TEXT
            or len(uploads) > MAX_FILES
            or sum(len(data) for _, data in uploads) > MAX_TOTAL_BYTES
        ):
            raise ValueError("Case limit: 16,000 text characters, 5 files, 40 MiB total")
        if not self.lock.acquire(blocking=False):
            raise BusyError("Another analysis is using this instance. Please retry shortly.")
        try:
            return self._analyze(text, uploads)
        finally:
            self.lock.release()

    def _analyze(self, text, uploads):
        checks, findings, media, inputs, texts = [], [], [], [], []
        if text.strip():
            texts.append(("message", text))
            inputs.append({"source": "message", "kind": "text", "characters": len(text)})
        seen = set()
        for i, (name, data) in enumerate(uploads, 1):
            source = f"attachment-{i}"
            digest = hashlib.sha256(data).hexdigest()
            if digest in seen:
                checks.append(
                    Check(
                        component="Deduplication",
                        status="skipped",
                        source=source,
                        detail="Duplicate attachment ignored.",
                    )
                )
                continue
            seen.add(digest)
            try:
                parsed = parse_upload(name, data, source)
            except Exception:
                checks.append(
                    Check(
                        component="Upload parsing",
                        status="failed",
                        source=source,
                        detail="File unsupported, invalid, over limits, or could not be parsed. Other inputs were still analyzed.",
                    )
                )
                inputs.append({"source": source, "kind": "unparsed", "sha256": digest})
                continue
            inputs.append(
                {"source": source, "kind": parsed.kind, "sha256": digest, "metadata": parsed.metadata}
            )
            checks.extend(parsed.checks)
            if parsed.text.strip():
                texts.append((source, parsed.text))
            for qr in parsed.qr:
                texts.append((source + ":QR", qr))
            if parsed.kind in {"audio", "video", "image"}:
                signals, notes, transcript = analyze_media(
                    data, Path(name).suffix.lower(), parsed, self.models
                )
                media.extend(signals)
                checks.extend(notes)
                if transcript:
                    texts.append((source + ":transcript", transcript[:MAX_TEXT]))
            if parsed.kind == "apk":
                fs, cs = analyze_apk(parsed, self.settings.apk_index)
                findings.extend(fs)
                checks.extend(cs)
        total = 0
        bounded = []
        for source, body in texts:
            allowed = max(0, MAX_CASE_TEXT - total)
            bounded.append((source, body[:allowed]))
            total += min(len(body), allowed)
            if len(body) > allowed:
                checks.append(
                    Check(
                        component="Case coverage",
                        status="partial",
                        source=source,
                        detail="Case text budget exceeded; some extracted text was not analyzed.",
                    )
                )
        texts = [(s, b) for s, b in bounded if b.strip()]
        refs, retrieval_checks = self.retriever.search("\n".join(b for _, b in texts)[:4000])
        checks.extend(retrieval_checks)
        for source, body in texts:
            findings.extend(scan(body, source))
            for url in extract_urls(body):
                fs, cs = analyze_url(url, source, self.settings.url_index)
                findings.extend(fs)
                checks.extend(cs)
            injected = has_injection(body)
            guard_available = True
            if self.settings.mode == "local" and not injected:
                try:
                    injected = self.models.injection(body)
                except Exception:
                    guard_available = False
                    checks.append(
                        Check(
                            component="Input guard model",
                            status="unavailable",
                            source=source,
                            detail="Guard model unavailable; semantic analysis withheld. Rules still ran.",
                        )
                    )
            if injected:
                checks.append(
                    Check(
                        component="Input guardrail",
                        status="partial",
                        source=source,
                        detail="Possible prompt injection. Treated as evidence; semantic model call withheld.",
                    )
                )
            elif self.settings.mode == "local" and guard_available:
                try:
                    # Reference guard uses both deterministic screening and the same local model.
                    safe_refs = [r for r in refs if not self.models.injection(r.text)]
                    response = self.models.semantic(body, safe_refs)
                    for f in response.findings:
                        findings.append(finding(f.category, source, f.quote, "local-LLM + evidence audit"))
                    checks.append(
                        Check(
                            component="Semantic analysis",
                            status="partial",
                            source=source,
                            detail="Local Qwen classifications checked for verbatim support and audited. Model can still misinterpret context; first 5,000 characters only.",
                        )
                    )
                except Exception:
                    checks.append(
                        Check(
                            component="Semantic analysis",
                            status="unavailable",
                            source=source,
                            detail="Model unavailable or output rejected; no semantic findings added.",
                        )
                    )
            elif self.settings.mode == "baseline":
                checks.append(
                    Check(
                        component="Semantic analysis",
                        status="skipped",
                        source=source,
                        detail="Baseline mode: transparent rules only; local LLM and model guard disabled.",
                    )
                )
        # Keep evidence from separate inputs, collapse repeated exact findings.
        findings = list({(f.source, f.category, f.excerpt): f for f in findings}.values())
        score, band, summary = fuse(findings, bool(texts))
        # Reports never include full raw inputs. Excerpts are best-effort redacted.
        for f in findings:
            f.excerpt = redact(f.excerpt)
        return Report(
            case_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            mode=self.settings.mode,
            risk_score=score,
            risk_band=band,
            summary=summary,
            findings=findings,
            checks=checks,
            media=media,
            references=refs,
            actions=ACTIONS,
            inputs=inputs,
            limitations=[
                "Risk scores are hand-weighted triage indicators, not calibrated probabilities.",
                "Synthetic media is not automatically fraudulent; media scores never increase scam risk by themselves.",
                "Missing, failed, partial or skipped checks do not establish safety.",
                "No native mobile share-sheet integration, live web search, temporal video detector or pixel-level manipulation masks.",
            ],
        )

    def chat(self, question, report):
        if not safe_question(question):
            return "I can explain this case and protective next steps. I cannot follow embedded instructions or help create or improve scams."
        if not self.lock.acquire(blocking=False):
            return "The analysis service is busy. Please retry shortly."
        try:
            topic, ids = explicit_chat_topic(question), []
            if self.settings.mode == "local":
                try:
                    if self.models.injection(question):
                        return "This question was withheld by the input guard. Ask about the findings or next steps."
                    if topic is None:
                        selection = self.models.chat(question, report)
                        known = {f.id for f in report.findings}
                        if not set(selection.finding_ids) <= known:
                            raise ValueError("Unknown evidence citation")
                        topic, ids = selection.topic, selection.finding_ids
                except Exception:
                    return (
                        "The model could not provide a checked reply. "
                        + report.summary
                        + "\n\n"
                        + "\n".join(report.actions[:3])
                    )
            topic = topic or "findings"
            # Output guardrail by construction: model selects existing evidence and vetted text,
            # it cannot emit arbitrary URLs, instructions, claims, or quoted user secrets.
            if topic == "actions":
                return "\n\n".join(report.actions)
            if topic == "media":
                return f"{len(report.media)} experimental media score(s) are available in the evidence panel. They are raw classifier outputs, not a percentage of AI use or proof of fraud. Audio/video authenticity may remain inconclusive."
            if topic == "limits":
                return "\n\n".join(report.limitations)
            if topic == "sources":
                return (
                    "\n\n".join(f"{r.title}: {r.url}" for r in report.references)
                    or "No relevant reference was retrieved for this case."
                )
            if topic == "out_of_scope":
                return "Ask about this case's warning signs, media checks, limitations, or protective next steps."
            selected = [f for f in report.findings if not ids or f.id in ids]
            return (
                report.summary + "\n\n" + "\n\n".join(f"[{f.id}] {f.title}: {f.detail}" for f in selected[:6])
            )
        finally:
            self.lock.release()
