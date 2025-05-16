import pandas as pd
import os

def order_managment(
    df_subset: pd.DataFrame,
    y0_value: float,
    y1_value: float,
    END_TIME,
    first_breakout_time: pd.Timestamp,
    first_breakout_price: float,
    first_breakdown_time: pd.Timestamp,
    first_breakdown_price: float,
    df_high_volumen_candles: pd.DataFrame,
    target_profit: float = 15,
    stop_lost: float = 15,
    discount_short: float = -0.20,
    discount_long: float = 20
) -> pd.DataFrame:

    # ================== CALCULOS BASE ======================
    expansion = 0.38
    y1_expansion = y1_value + (y1_value - y0_value) * expansion
    y0_expansion = y0_value - (y1_value - y0_value) * expansion
    opening_range = y1_value - y0_value
    midpoint = (y1_value + y0_value) / 2

    stop_line_high = y1_value + opening_range * 0.90
    stop_line_low = y0_value - opening_range * 0.90

    stop_lost_short = stop_line_high
    stop_lost_long = stop_line_low

    print("Midpoint:", midpoint)

    df = df_high_volumen_candles.copy()
    df['Entry'] = df['Close'].apply(
        lambda x: 'Short' if x > y1_value else ('Long' if x < y0_value else None)
    )
    df = df[df['Entry'].notna()].copy()
    df['Entry_Price'] = df['Close']

    results = []

    for entry_time, row in df.iterrows():
        entry_price = row['Entry_Price']
        entry_type = row['Entry']

        tp = midpoint
        sl = stop_lost_long if entry_type == 'Long' else stop_lost_short

        after_entry = df_subset[df_subset.index > entry_time]
        max_fav = 0
        max_adv = 0
        exit_price = None
        exit_time = None
        outcome = None

        for idx, bar in after_entry.iterrows():
            high = bar['High']
            low = bar['Low']

            if entry_type == 'Long':
                current_profit = high - entry_price
                current_drawdown = entry_price - low
                if high >= tp:
                    exit_time, exit_price, outcome = idx, tp, 'TP'
                    break
                elif low <= sl:
                    exit_time, exit_price, outcome = idx, sl, 'SL'
                    break

            elif entry_type == 'Short':
                current_profit = entry_price - low
                current_drawdown = high - entry_price
                if low <= tp:
                    exit_time, exit_price, outcome = idx, tp, 'TP'
                    break
                elif high >= sl:
                    exit_time, exit_price, outcome = idx, sl, 'SL'
                    break

            max_fav = max(max_fav, current_profit)
            max_adv = max(max_adv, current_drawdown)

        if outcome is None and not after_entry.empty:
            last_idx = after_entry.index[-1]
            last_close = after_entry.iloc[-1]['Close']
            exit_time = last_idx
            exit_price = last_close
            outcome = 'close_at_end'
            if entry_type == 'Long':
                max_fav = max(max_fav, after_entry['High'].max() - entry_price)
                max_adv = max(max_adv, entry_price - after_entry['Low'].min())
            elif entry_type == 'Short':
                max_fav = max(max_fav, entry_price - after_entry['Low'].min())
                max_adv = max(max_adv, after_entry['High'].max() - entry_price)

        duration = exit_time - entry_time if exit_time else None
        profit = (exit_price - entry_price) if entry_type == 'Long' else (entry_price - exit_price)
        instrument_value = 50
        profit_currency = profit * instrument_value

        # ========== Breakout/Discount Check ==========
        pre_entry_window = df_subset[(df_subset.index > END_TIME) & (df_subset.index < entry_time)]
        break_label = False
        break_d_label = False

        if not pre_entry_window.empty:
            range_size = y1_value - y0_value
            if entry_type == 'Long':
                break_label = pre_entry_window['High'].gt(y1_value).any()
                y1_discount = y1_value - range_size * abs(discount_short)
                break_d_label = pre_entry_window['High'].gt(y1_discount).any()
            elif entry_type == 'Short':
                break_label = pre_entry_window['Low'].lt(y0_value).any()
                y0_discount = y0_value + discount_long
                break_d_label = pre_entry_window['Low'].lt(y0_discount).any()

        results.append({
            'Entry_Time': entry_time,
            'Entry': entry_type,
            'Entry_Price': entry_price,
            'TP': tp,
            'SL': sl,
            'Exit_Time': exit_time,
            'Exit_Price': exit_price,
            'Outcome': outcome,
            'Duration': duration,
            'Profit': profit,
            'Profit_$': profit_currency,
            'MFE_points': max_fav,
            'MAE_points': max_adv,
            'break_oposite': break_label,
            'break_D_oposite': break_d_label
        })

    df_orders = pd.DataFrame(results)

    # ===== Guardar resultados =====
    os.makedirs('outputs', exist_ok=True)
    summary_file_path = os.path.join('outputs', 'summary_orders.csv')

    if os.path.exists(summary_file_path):
        existing_df = pd.read_csv(summary_file_path)
        updated_df = pd.concat([existing_df, df_orders], ignore_index=True)
        updated_df.to_csv(summary_file_path, index=False)
        print(f"✅ Archivo actualizado: {summary_file_path}")
    else:
        df_orders.to_csv(summary_file_path, index=False)
        print(f"✅ Archivo creado: {summary_file_path}")

    return df_orders



