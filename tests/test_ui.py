from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_streamlit_analysis_and_clear(monkeypatch):
    monkeypatch.setenv("RIDSCA_MODE", "baseline")
    at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=20).run()
    assert not at.exception
    at.text_area[0].set_value("Send your OTP immediately to avoid account blocked").run()
    at.checkbox[0].check().run()
    next(b for b in at.button if b.label == "Analyze this case").click().run()
    assert not at.exception
    assert any(m.value == "High risk" for m in at.metric)
    next(b for b in at.button if b.label == "Clear case and uploads").click().run()
    assert not at.exception and not at.metric
    assert at.text_area[0].value == ""


def test_consent_disables_analysis(monkeypatch):
    monkeypatch.setenv("RIDSCA_MODE", "baseline")
    at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()
    assert next(b for b in at.button if b.label == "Analyze this case").disabled
