import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns


def analyze_performance(trades_df: pd.DataFrame, equity_df: pd.DataFrame, initial_capital: float = 1_000_000, out_path: str = "outputs/Strategy_Performance_Report.png"):
    """
    Generate a compact tearsheet-style report and save as PNG.
    """
    # Use a clean, default matplotlib style (avoid hard-coding colors in interviews unless requested)
    plt.style.use("bmh")

    equity = equity_df.copy()
    equity["Drawdown"] = equity["Equity"] - equity["Equity"].cummax()
    equity["Drawdown_Pct"] = equity["Drawdown"] / equity["Equity"].cummax()

    # Trade stats
    if len(trades_df) > 0:
        total_trades = len(trades_df)
        wins = trades_df[trades_df["PnL"] > 0]
        losses = trades_df[trades_df["PnL"] <= 0]

        gross_profit = wins["PnL"].sum()
        gross_loss = abs(losses["PnL"].sum())
        net_profit = trades_df["PnL"].sum()

        win_rate = (len(wins) / total_trades) * 100
        profit_factor = (gross_profit / gross_loss) if gross_loss != 0 else np.inf

        avg_win = wins["PnL"].mean() if len(wins) else 0.0
        avg_loss = abs(losses["PnL"].mean()) if len(losses) else 0.0
        avg_win_loss = (avg_win / avg_loss) if avg_loss != 0 else np.nan

        long_pnl = trades_df.loc[trades_df["Type"] == "Long", "PnL"].sum()
        short_pnl = trades_df.loc[trades_df["Type"] == "Short", "PnL"].sum()
    else:
        total_trades = 0
        win_rate = 0.0
        profit_factor = 0.0
        net_profit = 0.0
        avg_win_loss = np.nan
        long_pnl = 0.0
        short_pnl = 0.0

    mdd_pct = equity["Drawdown_Pct"].min() * 100
    mdd_amt = equity["Drawdown"].min()

    # --- Plot layout ---
    fig = plt.figure(figsize=(10, 12))
    gs = gridspec.GridSpec(3, 2, height_ratios=[2, 1, 1])

    # Equity curve
    ax1 = plt.subplot(gs[0, :])
    ax1.plot(equity.index, equity["Equity"] / 1_000_000, linewidth=1.5)
    ax1.fill_between(equity.index, equity["Equity"] / 1_000_000, equity["Equity"].cummax() / 1_000_000, alpha=0.15)
    ax1.set_title("Equity Curve", fontsize=14, fontweight="bold")
    ax1.set_ylabel("Equity (Millions)")
    ax1.grid(True, alpha=0.3)

    # Underwater
    ax2 = plt.subplot(gs[1, :], sharex=ax1)
    ax2.fill_between(equity.index, equity["Drawdown_Pct"] * 100, 0, alpha=0.6)
    ax2.set_title("Drawdown (%)", fontsize=12)
    ax2.set_ylabel("DD %")
    ax2.grid(True, alpha=0.3)

    # PnL decomposition
    ax3 = plt.subplot(gs[2, 0])
    bars = ax3.bar(["Total", "Long", "Short"], [net_profit, long_pnl, short_pnl], alpha=0.85)
    ax3.set_title("PnL Decomposition", fontsize=12)
    ax3.grid(axis="y", alpha=0.3)
    for b in bars:
        ax3.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{int(b.get_height()):,}", ha="center", va="bottom", fontsize=9)

    # PnL distribution
    ax4 = plt.subplot(gs[2, 1])
    if len(trades_df) > 0:
        sns.histplot(trades_df["PnL"], kde=True, bins=30, ax=ax4)
        ax4.axvline(0, linestyle="--", linewidth=1)
        ax4.set_title("Trade PnL Distribution", fontsize=12)
        ax4.set_xlabel("PnL per trade")
    else:
        ax4.text(0.5, 0.5, "No Trades", ha="center", va="center")

    # Stats box
    stats = "\n".join([
        f"Net Profit: {int(net_profit):,}",
        f"Max Drawdown: {mdd_pct:.2f}% ({int(mdd_amt):,})",
        "----------------------",
        f"Total Trades: {total_trades}",
        f"Win Rate: {win_rate:.2f}%",
        f"Profit Factor: {profit_factor:.2f}",
        f"Avg Win/Loss: {avg_win_loss:.2f}" if not np.isnan(avg_win_loss) else "Avg Win/Loss: NA",
    ])
    ax1.text(0.02, 0.95, stats, transform=ax1.transAxes, va="top", fontsize=10,
             bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.6))

    plt.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    print(f"[OK] Report saved: {out_path}")
