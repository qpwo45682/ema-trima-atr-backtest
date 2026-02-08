"""
Create a small sample csv from a full dataset for repo/demo usage.

Usage:
  python scripts/make_sample.py --in data/TXF_60.csv --out data/sample_TXF_60.csv --rows 2000
"""
import argparse
import pandas as pd


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", dest="out", required=True)
    p.add_argument("--rows", type=int, default=2000)
    args = p.parse_args()

    df = pd.read_csv(args.inp)
    df.head(args.rows).to_csv(args.out, index=False)
    print(f"[OK] wrote sample: {args.out} ({min(args.rows, len(df))} rows)")


if __name__ == "__main__":
    main()
