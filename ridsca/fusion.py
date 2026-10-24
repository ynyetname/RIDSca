from .schema import Finding

ACTIONS = [
    "Pause any requested payment, credential sharing, or app installation until independently verified.",
    "Contact the organization using its official app, a known website, or a number already on your card or statement—not contact details from the suspicious message.",
    "Do not share OTPs, PINs, passwords or remote access with the sender.",
    "Preserve the original message and transaction references privately. If money was lost, contact your bank promptly and report through India's cybercrime.gov.in or 1930.",
]


def fuse(findings: list[Finding], has_text=False):
    # Identical/correlated categories count once even across OCR/transcript/message.
    by_category = {}
    for f in findings:
        if f.weight:
            by_category[f.category] = max(by_category.get(f.category, 0), f.weight)
    if not by_category:
        # No red flags is not enough to decide that the content is low risk.
        return (
            None,
            "Inconclusive",
            "No supported warning indicator was found by the available checks. This does not establish that the communication is safe.",
        )
    score = min(100, sum(by_category.values()))
    band = "High risk" if score >= 70 else "Suspicious" if score >= 40 else "Low risk"
    summary = f"{len(by_category)} distinct warning category/categories produced a preliminary {band.lower()} triage score. Sender identity and authenticity remain unverified."
    return score, band, summary
