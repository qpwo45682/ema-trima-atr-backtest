import numpy as np
import pandas as pd


def run_custom_backtest(df, initial_capital=1000000, strategy_x=150, use_atr=False, atr_multiplier=5.0):
    """
    進場固定 ATR stop
    - stop_dist 在「進場當根」固定 (使用 ATR_Prev * multiplier)，持倉期間不再變動
    - Trailing stop 只透過 high_since_entry / low_since_entry 更新
    - 停損觸發用 OHLC 保守成交價：
        Long  : actual_exit = min(Open, stop_price)
        Short : actual_exit = max(Open, stop_price)
    - 訊號 Close 確認、下一根 Open 執行（無未來函數）
    """

    # 變數初始化
    position = 0        # 0: 空手, 1: 多單, -1: 空單
    entry_price = 0.0
    entry_time = None

    # 進場時固定下來的停損距離（本版本重點）
    fixed_stop_dist = None

    # trailing extreme（截至上一根 K棒結算後狀態）
    high_since_entry = None
    low_since_entry = None

    trades = []
    equity_curve = []
    current_equity = initial_capital

    cost_per_trade = 300  # 單邊

    # 訊號 shift：t-1 收盤確認，t 開盤執行
    df = df.copy()
    df['Signal_Long'] = df['CrossUp'].shift(1).fillna(False)
    df['Signal_Short'] = df['CrossDown'].shift(1).fillna(False)

    print(f"開始回測迴圈 ( ATR模式: {'開啟' if use_atr else '關閉'} | 固定ATR Stop: {'是' if use_atr else '否'} )...")

    for row in df.itertuples():
        current_time = row.Index

        # 0) 記錄權益
        equity_curve.append({'Date': current_time, 'Equity': current_equity})

        # 1) 強制平倉 (Time Exit)
        is_force_exit_time = (current_time.dayofweek == 1) and (15 <= current_time.day <= 21) and (current_time.hour == 13)

        if position != 0 and is_force_exit_time:
            exit_price = float(row.Close)
            raw_pnl = (exit_price - entry_price) * 200 if position == 1 else (entry_price - exit_price) * 200
            net_pnl = raw_pnl - (cost_per_trade * 2)

            trades.append({
                'Entry Time': entry_time, 'Exit Time': current_time,
                'Entry Price': float(entry_price), 'Exit Price': float(exit_price),
                'Type': 'Long' if position == 1 else 'Short',
                'Reason': 'Force Exit', 'PnL': float(net_pnl),
                'StopDist': float(fixed_stop_dist) if fixed_stop_dist is not None else np.nan
            })
            current_equity += net_pnl

            # reset
            position = 0
            entry_price = 0.0
            entry_time = None
            fixed_stop_dist = None
            high_since_entry = None
            low_since_entry = None
            continue

        # ----------------------------------------------------
        # 2) 進場與反手：一律在 Open 成交
        # ----------------------------------------------------
        if row.Signal_Long:
            # 若原本是空單 -> 先平倉
            if position == -1:
                exit_price = float(row.Open)
                raw_pnl = (entry_price - exit_price) * 200
                net_pnl = raw_pnl - (cost_per_trade * 2)

                trades.append({
                    'Entry Time': entry_time, 'Exit Time': current_time,
                    'Entry Price': float(entry_price), 'Exit Price': float(exit_price),
                    'Type': 'Short', 'Reason': 'Reversal Long', 'PnL': float(net_pnl),
                    'StopDist': float(fixed_stop_dist) if fixed_stop_dist is not None else np.nan
                })
                current_equity += net_pnl

                # reset to flat before new entry
                position = 0
                entry_price = 0.0
                entry_time = None
                fixed_stop_dist = None
                high_since_entry = None
                low_since_entry = None

            # 若空手 -> 開多
            if position == 0:
                position = 1
                entry_price = float(row.Open)
                entry_time = current_time

                # ====== 本版本重點：進場固定 stop_dist ======
                if use_atr:
                    atr_prev = float(row.ATR_Prev) if not np.isnan(row.ATR_Prev) else np.nan
                    fixed_stop_dist = float(strategy_x) if np.isnan(atr_prev) else float(atr_prev * atr_multiplier)
                else:
                    fixed_stop_dist = float(strategy_x)

                # trailing extreme 初始化：用 entry_price
                high_since_entry = float(entry_price)
                low_since_entry = None

        elif row.Signal_Short:
            # 若原本是多單 -> 先平倉
            if position == 1:
                exit_price = float(row.Open)
                raw_pnl = (exit_price - entry_price) * 200
                net_pnl = raw_pnl - (cost_per_trade * 2)

                trades.append({
                    'Entry Time': entry_time, 'Exit Time': current_time,
                    'Entry Price': float(entry_price), 'Exit Price': float(exit_price),
                    'Type': 'Long', 'Reason': 'Reversal Short', 'PnL': float(net_pnl),
                    'StopDist': float(fixed_stop_dist) if fixed_stop_dist is not None else np.nan
                })
                current_equity += net_pnl

                position = 0
                entry_price = 0.0
                entry_time = None
                fixed_stop_dist = None
                high_since_entry = None
                low_since_entry = None

            # 若空手 -> 開空
            if position == 0:
                position = -1
                entry_price = float(row.Open)
                entry_time = current_time

                # ====== 本版本重點：進場固定 stop_dist ======
                if use_atr:
                    atr_prev = float(row.ATR_Prev) if not np.isnan(row.ATR_Prev) else np.nan
                    fixed_stop_dist = float(strategy_x) if np.isnan(atr_prev) else float(atr_prev * atr_multiplier)
                else:
                    fixed_stop_dist = float(strategy_x)

                low_since_entry = float(entry_price)
                high_since_entry = None

        # ----------------------------------------------------
        # 3) 持倉管理：Trailing Stop（固定 stop_dist + 更新 extreme）
        # ----------------------------------------------------
        if position != 0:
            stop_dist = float(fixed_stop_dist)  # 固定，不隨時間漂移

            if position == 1:
                stop_price = float(high_since_entry) - stop_dist

                # 觸發停損
                if float(row.Low) <= stop_price:
                    actual_exit_price = min(float(row.Open), round(stop_price))

                    raw_pnl = (actual_exit_price - entry_price) * 200
                    net_pnl = raw_pnl - (cost_per_trade * 2)

                    trades.append({
                        'Entry Time': entry_time, 'Exit Time': current_time,
                        'Entry Price': float(entry_price), 'Exit Price': float(actual_exit_price),
                        'Type': 'Long', 'Reason': 'Trailing Stop', 'PnL': float(net_pnl),
                        'StopDist': float(stop_dist)
                    })
                    current_equity += net_pnl

                    # reset
                    position = 0
                    entry_price = 0.0
                    entry_time = None
                    fixed_stop_dist = None
                    high_since_entry = None
                    low_since_entry = None
                else:
                    # 未觸發 -> 更新 extreme（供下一根使用）
                    if float(row.High) > float(high_since_entry):
                        high_since_entry = float(row.High)

            elif position == -1:
                stop_price = float(low_since_entry) + stop_dist

                if float(row.High) >= stop_price:
                    actual_exit_price = max(float(row.Open), round(stop_price))

                    raw_pnl = (entry_price - actual_exit_price) * 200
                    net_pnl = raw_pnl - (cost_per_trade * 2)

                    trades.append({
                        'Entry Time': entry_time, 'Exit Time': current_time,
                        'Entry Price': float(entry_price), 'Exit Price': float(actual_exit_price),
                        'Type': 'Short', 'Reason': 'Trailing Stop', 'PnL': float(net_pnl),
                        'StopDist': float(stop_dist)
                    })
                    current_equity += net_pnl

                    position = 0
                    entry_price = 0.0
                    entry_time = None
                    fixed_stop_dist = None
                    high_since_entry = None
                    low_since_entry = None
                else:
                    if float(row.Low) < float(low_since_entry):
                        low_since_entry = float(row.Low)

    trades_df = pd.DataFrame(trades)
    equity_df = pd.DataFrame(equity_curve).set_index('Date')
    return trades_df, equity_df