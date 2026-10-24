"""Lexical and exact local-index URL checks. Never resolve or visit submitted URLs."""

import csv
import hashlib
import ipaddress
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit
from .schema import Check, Finding


def extract_urls(text):
    urls = re.findall(r"(?:https?://|www\.)[^\s<>\"']+", text, re.I)
    return list(dict.fromkeys(u.rstrip(".,;!?)。") for u in urls))[:30]


def canonical_url(raw):
    if raw.lower().startswith("www."):
        raw = "https://" + raw
    p = urlsplit(raw)
    if p.scheme.lower() not in {"http", "https"} or not p.hostname:
        raise ValueError("Only HTTP(S) URLs with a host can be checked")
    if len(raw) > 2048 or any(ord(c) < 32 for c in raw):
        raise ValueError("Invalid URL length or control character")
    host = p.hostname.encode("idna").decode().lower()
    port = p.port
    netloc = f"[{host}]" if ":" in host else host
    if port and not (
        p.scheme.lower() == "https" and port == 443 or p.scheme.lower() == "http" and port == 80
    ):
        netloc += f":{port}"
    # Preserve credentials for exact lookup rather than conflating with benign URL.
    if p.username is not None:
        netloc = p.netloc.rsplit("@", 1)[0] + "@" + netloc
    return urlunsplit((p.scheme.lower(), netloc, p.path or "/", p.query, ""))


def analyze_url(raw, source, index_path):
    findings, checks = [], []

    def add(category, title, detail, weight):
        ident = hashlib.sha256(f"{raw}:{category}".encode()).hexdigest()[:12]
        findings.append(
            Finding(
                id="F-" + ident,
                category=category,
                source=source,
                title=title,
                detail=detail,
                excerpt=raw[:350],
                weight=weight,
            )
        )

    try:
        url = canonical_url(raw)
        p = urlsplit(url)
    except (ValueError, UnicodeError):
        return [], [
            Check(
                component="URL parser", status="failed", detail="Malformed URL; not visited.", source=source
            )
        ]
    host = p.hostname
    if p.username is not None:
        add(
            "url_deception",
            "URL contains user information",
            "Text before @ can disguise the actual destination host.",
            35,
        )
    if "xn--" in host:
        add(
            "url_deception",
            "Internationalized hostname",
            "Punycode can be legitimate, but visually similar characters need review.",
            15,
        )
    try:
        address = ipaddress.ip_address(host)
        add(
            "url_address",
            "IP-address destination",
            "A numeric destination does not establish the sender's identity.",
            15,
        )
        if not address.is_global:
            checks.append(
                Check(
                    component="URL network",
                    status="skipped",
                    detail="Private/local address; never fetched.",
                    source=source,
                )
            )
    except ValueError:
        pass
    if host in {"bit.ly", "tinyurl.com", "t.co", "shorturl.at"}:
        add(
            "url_shortener",
            "Shortened link",
            "The final destination is hidden and has not been expanded.",
            15,
        )
    if p.scheme == "http":
        add("url_transport", "Unencrypted URL", "HTTP does not protect submitted information in transit.", 10)
    if p.path.lower().endswith(".apk"):
        add(
            "apk_install",
            "Link to an Android package",
            "An APK download should be verified independently before installation.",
            45,
        )
    index = Path(index_path)
    if index.is_file():
        match = None
        with index.open(encoding="utf-8", newline="") as handle:
            for n, row in enumerate(csv.DictReader(handle)):
                if n >= 100000:
                    checks.append(
                        Check(
                            component="URL reputation",
                            status="partial",
                            detail="Index scan capped at 100,000 rows.",
                            source=source,
                        )
                    )
                    break
                try:
                    if canonical_url(row.get("url", "")) == url:
                        match = row
                        break
                except (ValueError, UnicodeError):
                    continue
        if match and match.get("verdict", "").lower() == "malicious":
            add(
                "known_threat",
                "Local threat-index match",
                "Exact URL matched a locally supplied record; review its date and source.",
                90,
            )
            checks.append(
                Check(
                    component="URL reputation",
                    status="complete",
                    detail=f"Local record: {match.get('source', 'unspecified')}; observed {match.get('observed_at', 'unknown')}.",
                    source=source,
                )
            )
        else:
            checks.append(
                Check(
                    component="URL reputation",
                    status="partial",
                    detail="No malicious exact match in local index. Absence is not evidence of safety.",
                    source=source,
                )
            )
    else:
        checks.append(
            Check(
                component="URL reputation",
                status="unavailable",
                detail="No local reputation index configured; lexical checks only.",
                source=source,
            )
        )
    checks.append(
        Check(
            component="URL lexical analysis",
            status="complete",
            detail="URL parsed offline; destination, redirects, TLS and page content not verified.",
            source=source,
        )
    )
    return findings, checks
