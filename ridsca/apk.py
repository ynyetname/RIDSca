import hashlib
from pathlib import Path
import sqlite3
from .schema import Check, Finding

DANGEROUS = {
    "android.permission.READ_SMS",
    "android.permission.RECEIVE_SMS",
    "android.permission.SEND_SMS",
    "android.permission.SYSTEM_ALERT_WINDOW",
    "android.permission.REQUEST_INSTALL_PACKAGES",
    "android.permission.BIND_ACCESSIBILITY_SERVICE",
}


def analyze_apk(parsed, index_path):
    findings, checks = [], []
    meta = parsed.metadata
    digest = meta.get("sha256", "")
    if len(digest) != 64:
        return findings, [
            Check(component="APK hash", status="failed", detail="SHA-256 unavailable.", source=parsed.source)
        ]
    permissions = set(meta.get("permissions", [])) & DANGEROUS
    if permissions:
        findings.append(
            Finding(
                id="F-" + hashlib.sha256((digest + "permissions").encode()).hexdigest()[:12],
                category="apk_permissions",
                source=parsed.source,
                title="Sensitive permissions declared",
                detail="Permissions are capabilities, not proof of malware: "
                + ", ".join(sorted(permissions)),
                weight=25,
            )
        )
    path = Path(index_path)
    if not path.is_file():
        checks.append(
            Check(
                component="APK reputation",
                status="unavailable",
                source=parsed.source,
                detail="No local APK metadata index. Unknown hash does not mean safe.",
            )
        )
    else:
        try:
            with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
                row = db.execute(
                    "SELECT package_name, vt_detection, observed_at FROM apk_metadata WHERE sha256 = ?",
                    (digest.lower(),),
                ).fetchone()
            if row:
                checks.append(
                    Check(
                        component="APK reputation",
                        status="complete",
                        source=parsed.source,
                        detail=f"Local hash record: package={row[0]}, detections={row[1]}, observed={row[2]}. May be stale.",
                    )
                )
                if row[1] is not None and int(row[1]) > 0:
                    findings.append(
                        Finding(
                            id="F-" + digest[:12],
                            category="known_threat",
                            source=parsed.source,
                            title="APK hash has recorded detections",
                            detail="A locally imported scanner-count record flags this hash. Review source/date; no current scan was performed.",
                            weight=85,
                        )
                    )
            else:
                checks.append(
                    Check(
                        component="APK reputation",
                        status="partial",
                        source=parsed.source,
                        detail="Hash absent from local index; not a clean verdict.",
                    )
                )
        except (sqlite3.Error, ValueError):
            checks.append(
                Check(
                    component="APK reputation",
                    status="failed",
                    source=parsed.source,
                    detail="Local index could not be read.",
                )
            )
    checks.append(
        Check(
            component="APK behavior",
            status="skipped",
            source=parsed.source,
            detail="No installation, execution, dynamic analysis, or certificate-trust verification.",
        )
    )
    return findings, checks
