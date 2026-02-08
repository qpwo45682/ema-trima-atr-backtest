# XMA/TRIMA + ATR Trailing Stop Backtest (TXF 60m)

This repository demonstrates an interview-ready quant research project:
- **Entry**: EMA(21) crosses TRIMA(21) (signal confirmed at close, executed next open)
- **Filters**
  - Long momentum confirmation: Mom_1 and Mom_2 must be > -0.25
  - Short regime filter: allow shorts only if Close < SMA200
- **Risk / Exit**: Entry-fixed ATR stop distance + trailing stop (gap-aware fills)
- **Operational**: Force exit on the 3rd Tuesday at 13:00 (to avoid settlement / microstructure risk)

> Note: The full dataset is **not** included. Provide your own `TXF_60.csv` in `data/` or pass a path via CLI.

## Project Structure
```
xma-trima-atr-backtest/
├─ src/
│  ├─ indicators.py    # data loading + indicators + filters
│  ├─ backtest.py      # custom OHLC backtest engine (close-to-open execution)
│  └─ report.py        # tearsheet-like report (equity / DD / decomposition / PnL hist)
├─ scripts/
│  └─ make_sample.py   # build a small sample csv from a full dataset (optional)
├─ data/
│  ├─ sample_TXF_60.csv
│  └─ (your full TXF_60.csv goes here, but is gitignored)
├─ outputs/
│  └─ .gitkeep
├─ run.py              # CLI entrypoint
├─ requirements.txt
├─ .gitignore
└─ README.md
```

## Data Format
Your csv can use either naming convention:
- `time/open/high/low/close/volume`
- OR `Date/Open/High/Low/Close/Volume`

## Quickstart
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# run with the included sample
python run.py --data data/sample_TXF_60.csv --out outputs

# run with your full dataset (place file in data/TXF_60.csv)
python run.py --data data/TXF_60.csv --out outputs
```

## Outputs
- `outputs/Strategy_Performance_Report.png`
- `outputs/trades.csv`
- `outputs/equity.csv`

## Notes on Backtest Assumptions
- **No look-ahead**: signals are computed at close, executed at next open.
- **Gap-aware stop fills**:
  - Long stop fill: `min(Open, StopPrice)`
  - Short stop fill: `max(Open, StopPrice)`
- **Entry-fixed ATR stop distance**: computed from `ATR_{t-1}` at entry; does not drift during the trade.
