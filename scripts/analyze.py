import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from ridsca.config import Settings
from ridsca.service import Analyzer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", default="")
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--consent", action="store_true")
    args = parser.parse_args()
    load_dotenv()
    report = Analyzer(Settings.from_env()).analyze(
        args.text, [(Path(p).name, Path(p).read_bytes()) for p in args.file], consent=args.consent
    )
    print(report.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
