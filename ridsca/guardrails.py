import re
from .rules import normalize

INJECTION = re.compile(
    r"ignore.{0,35}(?:previous|above|system|instructions)|(?:system|developer)\s*(?:prompt|message)"
    r"|reveal.{0,25}(?:secret|prompt)|<\|(?:im_start|im_end|system)|\[INST\]"
    r"|(?:disregard|override).{0,25}(?:rules|instructions)|mark.{0,20}(?:safe|low risk)",
    re.I,
)
MISUSE = re.compile(
    r"(?:write|create|improve|generate|bypass|evade).{0,60}(?:phishing|scam|fraud|detector|guardrail)", re.I
)


def has_injection(text):
    return bool(INJECTION.search(normalize(text)))


def redact(text):
    text = re.sub(r"(?i)\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", "[EMAIL]", text)
    text = re.sub(r"(?<!\w)(?:\+?\d[\d -]{7,}\d)(?!\w)", "[NUMBER]", text)
    text = re.sub(r"(?i)\b(otp|pin|password|cvv)\s*[:=]?\s*\d{3,8}\b", r"\1 [REDACTED]", text)
    return text


def safe_question(question):
    return 0 < len(question.strip()) <= 1000 and not has_injection(question) and not MISUSE.search(question)


def validate_semantic(response, text):
    """Exact evidence support is necessary, but not sufficient: an independent audit follows."""
    from .schema import SemanticResponse

    result = SemanticResponse.model_validate(response)
    for item in result.findings:
        if item.quote not in text or has_injection(item.quote):
            raise ValueError("Model finding has no valid verbatim support")
    return result


def explicit_chat_topic(question):
    """Honor clear UI intents before using a probabilistic topic classifier."""
    q = normalize(question).casefold()
    if re.search(
        r"\b(next steps?|what should i do|what can i do|what do i do|how (?:do|can) i report|lost money)\b|क्या करूं|क्या करूँ|अगला कदम",
        q,
    ):
        return "actions"
    if re.search(r"\b(sources?|references?|citations?)\b", q):
        return "sources"
    if re.search(r"\b(audio|voice|video|image|deepfake|ai)\b", q):
        return "media"
    if re.search(r"\b(safe|certain|certainty|limits?|limitations?|reliable)\b", q):
        return "limits"
    return None
