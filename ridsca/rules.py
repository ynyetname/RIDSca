"""Transparent, deliberately uncalibrated indicators. Never trained probabilities."""

import hashlib
import re
import unicodedata
from .schema import Finding

CATALOG = {
    "credentials": (
        70,
        "Request for a secret",
        "The content appears to request an OTP, PIN, password, or card security code.",
    ),
    "urgency": (
        20,
        "Urgency or account-blocking pressure",
        "A deadline or account-blocking claim can pressure a recipient to act before verifying.",
    ),
    "remote_access": (
        55,
        "Remote access request",
        "Remote control or screen-sharing requests can expose device activity and credentials.",
    ),
    "advance_fee": (
        55,
        "Advance payment request",
        "An upfront payment tied to a reward, loan, or job needs independent verification.",
    ),
    "guaranteed_returns": (
        45,
        "Guaranteed-return claim",
        "Guaranteed or unusually rapid returns are a warning sign requiring independent verification.",
    ),
    "apk_install": (
        45,
        "Application installation request",
        "An unsolicited APK or app installation request can expose a device to harm.",
    ),
}
PATTERNS = {
    "credentials": r"\b(?:share|send|tell|provide|give|enter|verify|confirm)\b.{0,65}\b(?:otp|pin|password|cvv)\b|(?:ओटीपी|पासवर्ड|पिन).{0,25}(?:बताओ|बताएं|भेजो|भेजें|साझा)",
    "urgency": r"\b(?:account.{0,35}(?:block|suspend|deactivat)|urgent|immediately|within \d+ (?:minute|hour))|(?:खाता.{0,20}बंद|तुरंत)",
    "remote_access": r"\b(?:install|download|open|enable|start)\b.{0,55}\b(?:anydesk|teamviewer|remote access|screen shar\w*)\b",
    "advance_fee": r"\b(?:pay|deposit|transfer)\b.{0,60}\b(?:processing fee|registration fee|release.{0,15}(?:prize|loan)|claim.{0,15}prize)\b",
    "guaranteed_returns": r"\b(?:guaranteed.{0,25}(?:return|profit)|double your money|risk.free.{0,20}(?:profit|return))\b",
    "apk_install": r"\b(?:install|download)\b.{0,70}(?:\.apk\b|\bapk\b)|\b(?:install|download).{0,35}app.{0,30}(?:kyc|verif)",
}
NEGATION = re.compile(r"\b(?:never|don't|do not|not to|avoid)\b|(?:मत|कभी न)", re.I)


def normalize(text):
    text = unicodedata.normalize("NFKC", text)
    return "".join(c for c in text if unicodedata.category(c) != "Cf")


def finding(category, source, excerpt="", method="rule"):
    weight, title, detail = CATALOG[category]
    key = hashlib.sha256(f"{source}:{category}:{excerpt}".encode()).hexdigest()[:12]
    return Finding(
        id="F-" + key,
        category=category,
        source=source,
        title=title,
        detail=detail,
        excerpt=excerpt[:350],
        weight=weight,
        method=method,
    )


def scan(text, source):
    text = normalize(text)
    found = []
    for category, pattern in PATTERNS.items():
        for match in re.finditer(pattern, text, re.I):
            prefix = text[max(0, match.start() - 28) : match.start()]
            if NEGATION.search(prefix):
                continue
            found.append(finding(category, source, match.group()))
            break
    return found
