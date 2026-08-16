from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from renko_research.config import load_config
from renko_research.volrix import render_volrix_strategy


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate standalone Volrix Renko code")
    parser.add_argument("config", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--class-name", default="ParameterizedRenkoSynthetic")
    parser.add_argument("--analysis-only", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    code = render_volrix_strategy(
        config,
        class_name=args.class_name,
        analysis_only=args.analysis_only,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(code, encoding="utf-8")


if __name__ == "__main__":
    main()
