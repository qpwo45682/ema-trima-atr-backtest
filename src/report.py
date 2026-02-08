import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns


def analyze_performance(trades_df, equity_df, initial_capital=500000):
    # 設定繪圖風格
    plt.style.use('bmh')
    fig = plt.figure(figsize=(9, 12))
    gs = gridspec.GridSpec(3, 2, height_ratios=[2, 1, 1])
    
    # ---------------------------------------------------------
    # 1. 數據計算
    # ---------------------------------------------------------
    # 權益曲線數據
    equity_df['Drawdown'] = equity_df['Equity'] - equity_df['Equity'].cummax()
    equity_df['Drawdown_Pct'] = equity_df['Drawdown'] / equity_df['Equity'].cummax()
    
    # 交易統計
    if len(trades_df) > 0:
        total_trades = len(trades_df)
        win_trades = trades_df[trades_df['PnL'] > 0]
        loss_trades = trades_df[trades_df['PnL'] <= 0]
        
        gross_profit = win_trades['PnL'].sum()
        gross_loss = abs(loss_trades['PnL'].sum())
        net_profit = trades_df['PnL'].sum()
        
        avg_win = win_trades['PnL'].mean() if len(win_trades) > 0 else 0
        avg_loss = abs(loss_trades['PnL'].mean()) if len(loss_trades) > 0 else 0
        
        win_rate = len(win_trades) / total_trades * 100
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else np.inf
        avg_win_loss_ratio = avg_win / avg_loss if avg_loss != 0 else 0
        
        long_trades = trades_df[trades_df['Type'] == 'Long']
        short_trades = trades_df[trades_df['Type'] == 'Short']
        
        long_pnl = long_trades['PnL'].sum()
        short_pnl = short_trades['PnL'].sum()
    else:
        # 防呆
        total_trades = 0
        win_rate = 0
        profit_factor = 0
        net_profit = 0
        long_pnl = 0
        short_pnl = 0

    # 計算年化回報與 MDD
    total_return = (equity_df['Equity'].iloc[-1] - initial_capital) / initial_capital * 100
    mdd_pct = equity_df['Drawdown_Pct'].min() * 100
    mdd_amount = equity_df['Drawdown'].min()
    
    # ---------------------------------------------------------
    # 2. 繪圖 - A: 權益曲線 (Equity Curve)
    # ---------------------------------------------------------
    ax1 = plt.subplot(gs[0, :])
    ax1.plot(equity_df.index, equity_df['Equity']/1000000, color='#1f77b4', linewidth=1.5) #, label='Strategy Equity'
    ax1.set_title('權益曲線', fontsize=14, fontweight='bold')
    ax1.set_ylabel('累積損益（百萬）')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # 標記 MDD 區間
    ax1.fill_between(equity_df.index, equity_df['Equity']/1000000, equity_df['Equity'].cummax()/1000000, 
                     color='red', alpha=0.1, label='Drawdown Area')

    # ---------------------------------------------------------
    # 3. 繪圖 - B: 水下圖 (Underwater Plot - Drawdown)
    # ---------------------------------------------------------
    ax2 = plt.subplot(gs[1, :], sharex=ax1)
    ax2.fill_between(equity_df.index, equity_df['Drawdown_Pct'] * 100, 0, color='#d62728', alpha=0.6)
    ax2.set_title('Drawdown (%)', fontsize=12)
    ax2.set_ylabel('Drawdown %')
    ax2.set_ylim([min(equity_df['Drawdown_Pct']*100)*1.1, 1])
    ax2.grid(True, alpha=0.3)

    # ---------------------------------------------------------
    # 4. 繪圖 - C: 多空損益比較 (Long vs Short)
    # ---------------------------------------------------------
    ax3 = plt.subplot(gs[2, 0])
    bars = ax3.bar(['Total', 'Long Only', 'Short Only'], 
                   [net_profit, long_pnl, short_pnl], 
                   color=['#2ca02c', '#1f77b4', '#ff7f0e'], alpha=0.8)
    ax3.set_title('PnL Decomposition (Long vs Short)', fontsize=12)
    ax3.set_ylabel('損益')
    ax3.grid(axis='y', alpha=0.3)
    
    # 在 Bar 上標示數字
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                 f'{int(height):,}', ha='center', va='bottom' if height > 0 else 'top', fontsize=10)

    # ---------------------------------------------------------
    # 5. 繪圖 - D: 盈虧分佈直方圖 (PnL Histogram)
    # ---------------------------------------------------------
    ax4 = plt.subplot(gs[2, 1])
    if len(trades_df) > 0:
        sns.histplot(trades_df['PnL'], kde=True, ax=ax4, color='purple', bins=30)
        ax4.axvline(0, color='black', linestyle='--', linewidth=1)
        ax4.set_title('Trade PnL Distribution', fontsize=12)
        ax4.set_xlabel('PnL per Trade')
    else:
        ax4.text(0.5, 0.5, 'No Trades', ha='center')

    # ---------------------------------------------------------
    # 6. 關鍵統計數據文字框
    # ---------------------------------------------------------
    text_str = '\n'.join((
        f'Net Profit: ${int(net_profit):,}',
        f'Max Drawdown: {mdd_pct:.2f}% (${int(mdd_amount):,})',
        f'---------------------------',
        f'Total Trades: {total_trades}',
        f'Win Rate: {win_rate:.2f}%',
        f'Profit Factor: {profit_factor:.2f}',
        f'Avg Win/Loss: {avg_win_loss_ratio:.2f}'
    ))
    
    # 將數據框放在圖表最右上方或另外顯示
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax1.text(0.02, 0.95, text_str, transform=ax1.transAxes, fontsize=10,
             verticalalignment='top', bbox=props) #text_str, "Equity Curve"

    plt.tight_layout()
    plt.savefig('Strategy_Performance_Report.png', dpi=300) # 存成高解析度圖片
    plt.show()
