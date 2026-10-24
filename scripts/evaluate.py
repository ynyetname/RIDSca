"""Evaluate supplied held-out labels; explicit abstentions, no invented accuracy."""

import argparse
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from ridsca.config import Settings
from ridsca.service import Analyzer


def evaluate(rows, analyzer):
    if not rows:
        raise ValueError("Dataset must not be empty")
    seen_ids = set()
    records = []
    for row in rows:
        if row["id"] in seen_ids or row["label"] not in {"scam", "genuine"}:
            raise ValueError("Duplicate id or invalid label")
        seen_ids.add(row["id"])
        started = time.perf_counter()
        report = analyzer.analyze(row["text"], consent=True)
        prediction = (
            "abstain"
            if report.risk_score is None
            else "flagged"
            if report.risk_score >= 40
            else "not_flagged"
        )
        records.append(
            {
                "id": row["id"],
                "group": row.get("group", row["id"]),
                "label": row["label"],
                "prediction": prediction,
                "seconds": round(time.perf_counter() - started, 3),
            }
        )
    scammers = [r for r in records if r["label"] == "scam"]
    genuine = [r for r in records if r["label"] == "genuine"]
    flagged = [r for r in records if r["prediction"] == "flagged"]

    def metric(numerator, denominator):
        return round(numerator / denominator, 4) if denominator else None

    stats = {
        "n": len(records),
        "abstention_rate": metric(sum(r["prediction"] == "abstain" for r in records), len(records)),
        "scam_flag_recall_including_abstentions_as_not_flagged": metric(
            sum(r["prediction"] == "flagged" for r in scammers), len(scammers)
        ),
        "genuine_false_alarm_rate": metric(sum(r["prediction"] == "flagged" for r in genuine), len(genuine)),
        "flag_precision": metric(sum(r["label"] == "scam" for r in flagged), len(flagged)),
        "mean_seconds": round(sum(r["seconds"] for r in records) / len(records), 3),
    }
    return {
        "mode": analyzer.settings.mode,
        "metrics": stats,
        "records": records,
        "note": "Synthetic fixtures measure software behavior only. Real-world performance requires an independently labeled, grouped, held-out dataset.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    load_dotenv()
    with open(args.dataset, encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    result = evaluate(rows, Analyzer(Settings.from_env()))
    data = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(data, encoding="utf-8")
    else:
        print(data)


if __name__ == "__main__":
    main()
