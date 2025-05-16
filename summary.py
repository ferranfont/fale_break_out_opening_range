import pandas as pd
import numpy as np
import os

# Load the summary output
summary_file_path = os.path.join('outputs', 'summary_orders.csv')

if os.path.exists(summary_file_path):
    summary = pd.read_csv(summary_file_path)
    print("✅ Summary file loaded.")
else:
    raise FileNotFoundError(f"⚠️ Summary file not found at: {summary_file_path}")

# Ensure numeric columns
summary['Profit'] = pd.to_numeric(summary['Profit'], errors='coerce')
summary['MAE_points'] = pd.to_numeric(summary['MAE_points'], errors='coerce')
summary['MFE_points'] = pd.to_numeric(summary['MFE_points'], errors='coerce')

# Remove rows with NaN profit
summary = summary.dropna(subset=['Profit'])

# Basic counts
total_trades = len(summary)
winning_trades = summary[summary['Profit'] > 0]
losing_trades = summary[summary['Profit'] < 0]

# Ratios
win_rate = len(winning_trades) / total_trades if total_trades else 0
loss_rate = len(losing_trades) / total_trades if total_trades else 0

# Averages
average_profit = winning_trades['Profit'].mean() if not winning_trades.empty else 0
average_loss = losing_trades['Profit'].mean() if not losing_trades.empty else 0  # Negative value

total_profit = summary['Profit'].sum()
expectancy = (average_profit * win_rate) + (average_loss * loss_rate)

# MAE and MFE averages
average_mae = summary['MAE_points'].mean()
average_mfe = summary['MFE_points'].mean()

# Sharpe and Sortino Ratios
returns = summary['Profit']
mean_return = returns.mean()
std_dev = returns.std()
downside_std = returns[returns < 0].std()
risk_free_rate = 0  # assuming 0 for simplicity

sharpe_ratio = (mean_return - risk_free_rate) / std_dev if std_dev else np.nan
sortino_ratio = (mean_return - risk_free_rate) / downside_std if downside_std else np.nan

# Print results
print(f"\n========= PERFORMANCE METRICS =========")
print(f"Total Trades: {total_trades}")
print(f"Total Profit: {total_profit:.2f}")
print(f"Win Rate: {win_rate * 100:.2f}%")
print(f"Loss Rate: {loss_rate * 100:.2f}%")
print(f"Average Profit per Winning Trade: {average_profit:.2f}")
print(f"Average Loss per Losing Trade: {average_loss:.2f}")
print(f"Expectancy (per trade): {expectancy:.2f}")
print(f"Average MAE (points): {average_mae:.2f}")
print(f"Average MFE (points): {average_mfe:.2f}")
print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
print(f"Sortino Ratio: {sortino_ratio:.2f}")
print(f"======================================")

correlation_matrix = summary[['SL', 'break_oposite', 'break_D_oposite']].corr()
print("\n========= CORRELATION WITH TP HIT =========")
print(correlation_matrix['SL'])
