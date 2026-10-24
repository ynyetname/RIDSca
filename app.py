"""Streamlit UI. User data lives in this browser session, never a shared cache."""

import json
import time
import streamlit as st
from dotenv import load_dotenv
from ridsca.config import Settings, ROOT
from ridsca.parsing import EXTENSIONS
from ridsca.service import Analyzer, BusyError

load_dotenv()
st.set_page_config(page_title="RIDSca | Check before you trust", page_icon="🛡️", layout="wide")


@st.cache_resource
def service(settings):
    # Only models + immutable public reference corpus are shared; no case data.
    return Analyzer(settings)


settings = Settings.from_env()
engine = service(settings)
state = st.session_state
state.setdefault("epoch", 0)
state.setdefault("cases", [])
state.setdefault("messages", [])
state.setdefault("last_touch", time.time())
state.setdefault("last_submit", 0.0)


def clear_case():
    state["epoch"] += 1
    state["cases"] = []
    state["messages"] = []
    state.pop("report", None)
    for key in list(state):
        if key.startswith(("input_", "files_", "consent_")):
            del state[key]
    state["last_touch"] = time.time()


if time.time() - state.last_touch > settings.session_ttl:
    clear_case()
    st.info("The previous case expired after inactivity. Start a new check.")
state.last_touch = time.time()

with st.sidebar:
    st.markdown("## RIDSca")
    st.caption("Risk Intelligence & Detection for Scams")
    st.divider()
    st.write(
        "**Runtime:** "
        + ("Local open models" if settings.mode == "local" else "Baseline · no model downloads")
    )
    st.caption("Models load on first use. CPU analysis may take several minutes.")
    if st.button("Clear case and uploads", use_container_width=True):
        clear_case()
        st.rerun()
    st.divider()
    st.write("**Your data**")
    st.caption(
        "Submitted content is processed on this app's server. No paid inference API, automatic URL visits, or training collection. Temporary parser files are removed after processing. Results remain in this browser session until cleared or expired."
    )
    st.caption(
        "Streamlit also buffers uploads in memory. Clearing rotates upload widgets; disconnected sessions expire after 60 seconds. Hosting infrastructure is outside this app's control."
    )
    st.caption("Research prototype · not a safety certificate")

st.caption("TEAM SCAMURAI  /  IIT ROORKEE")
st.title("Check before you trust.")
st.write("Bring a suspicious message, link, QR code, document or media file into one evidence-based review.")
if settings.mode == "baseline":
    st.info(
        "Baseline mode runs rules, parsing, QR/OCR and local indexes. AI models and media authenticity checks are off. See README to enable them."
    )

left, right = st.columns([2, 1], gap="large")
with left:
    st.subheader("1 · Add the communication")
    examples = json.loads((ROOT / "data/examples.json").read_text(encoding="utf-8"))
    sample = st.selectbox("Try an example", ["Custom input"] + [e["name"] for e in examples])
    initial = next((e["text"] for e in examples if e["name"] == sample), "")
    if st.button("Load selected example", disabled=sample == "Custom input"):
        state[f"input_{state.epoch}"] = initial
    text = st.text_area(
        "Message or related context",
        height=190,
        max_chars=16000,
        key=f"input_{state.epoch}",
        placeholder="Paste the message, including any link you want inspected…",
    )
    uploaded = st.file_uploader(
        "Related attachments · up to 5 files / 40 MiB total",
        type=sorted(e[1:] for e in EXTENSIONS),
        accept_multiple_files=True,
        key=f"files_{state.epoch}",
    )
    st.caption(
        "PDF, DOCX, PPTX, text, HTML, JSON, images, audio, video and APK. Max 20 MiB each. Media analysis covers up to 120 seconds. Legacy PPT is not supported."
    )
    consent = st.checkbox(
        "I have permission to submit this content and consent to processing it on this app's server.",
        key=f"consent_{state.epoch}",
    )
    run = st.button("Analyze this case", type="primary", use_container_width=True, disabled=not consent)
with right:
    with st.container(border=True):
        st.subheader("What you will get")
        st.write("**A risk assessment**\n\nSupported warning signs, with uncertainty made visible.")
        st.write("**Evidence by input**\n\nQuotes, URL checks, APK metadata and experimental media scores.")
        st.write("**Practical next steps**\n\nWays to verify the request independently.")
        st.caption(
            "Add more context and analyze again to replace the current assessment. The uploaded evidence remains selected until you clear it."
        )

if run:
    if time.time() - state.last_submit < 5:
        st.warning("Please wait a few seconds before starting another analysis.")
    else:
        state.last_submit = time.time()
        state.pop("report", None)
        state.messages = []
        try:
            with st.spinner("Checking inputs, retrieving references and assembling evidence…"):
                state.report = engine.analyze(
                    text, [(f.name, f.getvalue()) for f in uploaded], consent=consent
                )
            state.messages = []
        except (ValueError, BusyError) as exc:
            st.error(str(exc))
        except Exception:
            st.error(
                "Analysis did not complete. Try a smaller case or consult the setup diagnostics. No result was inferred."
            )

if "report" in state:
    report = state.report
    st.divider()
    st.subheader("2 · Review the assessment")
    a, b, c = st.columns(3)
    a.metric("Risk band", report.risk_band)
    b.metric("Preliminary triage score", "—" if report.risk_score is None else f"{report.risk_score}/100")
    c.metric("Coverage gaps", sum(ch.status != "complete" for ch in report.checks))
    st.write(report.summary)
    st.caption("The score is not a probability of fraud. AI/media scores are separate and uncalibrated.")
    tabs = st.tabs(["Warning signs", "Media evidence", "Check coverage", "References & next steps"])
    with tabs[0]:
        if not report.findings:
            st.info(
                "No supported warning signs were detected. Incomplete checks and new scam patterns can still hide risk."
            )
        for f in report.findings:
            with st.expander(f"{f.title} · {f.source}", expanded=True):
                st.write(f.detail)
                if f.excerpt:
                    st.code(f.excerpt, language=None)
                st.caption(f"{f.id} · {f.method} · preliminary weight {f.weight}")
    with tabs[1]:
        if report.media:
            st.dataframe([m.model_dump() for m in report.media], use_container_width=True, hide_index=True)
        else:
            st.info(
                "No media classifier scores are available for this case. This does not establish authenticity."
            )
        st.caption(
            "Scores are model outputs, not percentages of AI use. Video rows describe individual sampled frames, not a temporal or lip-sync detector."
        )
    with tabs[2]:
        st.dataframe([ch.model_dump() for ch in report.checks], use_container_width=True, hide_index=True)
        with st.expander("Input metadata"):
            st.json(report.inputs)
    with tabs[3]:
        for step in report.actions:
            st.write("• " + step)
        st.divider()
        for ref in report.references:
            st.write(f"**{ref.title}**")
            st.write(ref.text)
            st.caption(f"{ref.id} · reviewed {ref.reviewed_on}")
            if ref.id != "RIDSCA-LIMITS":
                st.link_button("Read source", ref.url)
        for limit in report.limitations:
            st.caption(limit)
    st.download_button(
        "Download case report (JSON)",
        report.model_dump_json(indent=2),
        file_name=f"ridsca-{report.case_id[:8]}.json",
        mime="application/json",
    )
    st.caption("Reports contain best-effort redacted excerpts and metadata. Review before sharing.")
    st.subheader("3 · Ask about this case")
    for role, content in state.messages:
        with st.chat_message(role):
            st.text(content)
    question = st.chat_input("Why was this flagged? What should I do next?", max_chars=1000)
    if question:
        with st.chat_message("user"):
            st.text(question)
        with st.chat_message("assistant"):
            with st.spinner("Checking the question…"):
                reply = engine.chat(question, report)
            st.text(reply)
        state.messages.extend([("user", question), ("assistant", reply)])
        state.messages = state.messages[-20:]
