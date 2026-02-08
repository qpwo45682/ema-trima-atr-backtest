import argparse
from pathlib import Path

import pandas as pd

from src.indicators import load_and_process_data, calculate_indicators
from src.backtest import run_custom_backtest
from src.report import analyze_performance


def parse_args():
    p = argparse.ArgumentParser(description="XMA/TRIMA + ATR trailing stop backtest")
    p.add_argument("--data", type=str, required=True, help="Path to csv (e.g., data/TXF_60.csv)")
    p.add_argument("--out", type=str, default="outputs", help="Output directory")
    p.add_argument("--initial_capital", type=float, default=1_000_000, help="Initial capital (TWD)")
    p.add_argument("--length", type=int, default=21, help="EMA/TRIMA length")
    p.add_argument("--use_atr", action="store_true", help="Use ATR-based fixed stop distance at entry")
    p.add_argument("--atr_multiplier", type=float, default=5.0, help="ATR multiplier for stop distance (if --use_atr)")
    p.add_argument("--fallback_stop", type=float, default=150.0, help="Fallback fixed stop distance if ATR is not available")
    return p.parse_args()


def main():
    args = parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Load
    df = load_and_process_data(args.data).sort_index()
    print(f"[OK] Loaded: {len(df):,} rows")

    # 2) Indicators / filters
    df = calculate_indicators(df, length=args.length)

    # 3) Backtest
    trades, equity_df = run_custom_backtest(
        df,
        initial_capital=args.initial_capital,
        strategy_x=args.fallback_stop,
        use_atr=args.use_atr,
        atr_multiplier=args.atr_multiplier,
    )

    # 4) Save artifacts
    trades_path = out_dir / "trades.csv"
    equity_path = out_dir / "equity.csv"
    trades.to_csv(trades_path, index=False)
    equity_df.to_csv(equity_path)

    # 5) Report (png)
    analyze_performance(trades, equity_df, initial_capital=args.initial_capital, out_path=str(out_dir / "Strategy_Performance_Report.png"))

    print(f"[OK] Saved trades: {trades_path}")
    print(f"[OK] Saved equity : {equity_path}")


if __name__ == "__main__":
    main()
