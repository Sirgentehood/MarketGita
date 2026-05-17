from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("\n$ " + " ".join(cmd))
    subprocess.run(cmd, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the daily post-close StockGita/VCP pipeline.")
    parser.add_argument("--universe", default="data/universe_2026.csv")
    parser.add_argument("--price-dir", default="data/yahoo_prices")
    parser.add_argument("--outputs", default="outputs")
    parser.add_argument("--period", default="24mo")
    parser.add_argument("--chart-scope", default="dashboard", choices=["dashboard", "all", "none"])
    parser.add_argument("--skip-existing-charts", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    universe = Path(args.universe)
    if not universe.exists():
        raise FileNotFoundError(f"Universe file missing: {universe}. Add your universe_2026.csv before running.")

    run([
        sys.executable,
        "yahoo_data_downloader.py",
        "--universe", args.universe,
        "--outdir", args.price_dir,
        "--period", args.period,
        "--market-index", "^NSEI",
    ])

    run([
        sys.executable,
        "vcp_engine.py",
        "--universe", args.universe,
        "--wide-price", args.price_dir,
        "--outdir", args.outputs,
        "--chart-scope", args.chart_scope,
        *( ["--skip-existing-charts"] if args.skip_existing_charts else [] ),
    ])


if __name__ == "__main__":
    main()
