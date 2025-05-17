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
    target_profit=12,
    stop_lost=3,
    discount_short=-0.20,
    discount_long=0.20,
    margen=2
) -> pd.DataFrame:

    target_profit = float(target_profit)
    stop_lost = float(stop_lost)
    margen = float(margen)

    cols = ['Open', 'High', 'Low', 'Close']
    df_subset.loc[:, cols] = df_subset[cols].apply(pd.to_numeric, errors='coerce')

    df = df_subset[df_subset.index > END_TIME].copy()

    df['Signal'] = df['Close'].apply(
        lambda x: 'Short' if x > y1_value else ('Long' if x < y0_value else None)
    )
    signals = df[df['Signal'].notna()]

    entradas_finales = []
    pos = 0

    for signal_idx, signal_row in signals.iterrows():
        signal_type = signal_row['Signal']
        close_price = signal_row['Close']

        if signal_type == 'Short':
            trigger_level = close_price + margen
        elif signal_type == 'Long':
            trigger_level = close_price - margen
        else:
            continue

        after_signal = df_subset[df_subset.index > signal_idx]

        for idx, row in after_signal.iterrows():
            if signal_type == 'Short' and row['High'] >= trigger_level:
                entry_price = trigger_level
                entry_time = idx
                entradas_finales.append((entry_time, signal_type, entry_price, signal_idx, trigger_level))
                pos += 1
                break
            elif signal_type == 'Long' and row['Low'] <= trigger_level:
                entry_price = trigger_level
                entry_time = idx
                entradas_finales.append((entry_time, signal_type, entry_price, signal_idx, trigger_level))
                pos += 1
                break

        if pos >= 1:
            break

    results = []

    for entry_time, entry_type, entry_price, signal_time, trigger_level in entradas_finales:
        tp = entry_price + target_profit if entry_type == 'Long' else entry_price - target_profit
        sl = entry_price - stop_lost if entry_type == 'Long' else entry_price + stop_lost
        be_active = False

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
                if high - entry_price >= 5:
                    sl = entry_price
                    be_active = True
                if high >= tp:
                    exit_time, exit_price, outcome = idx, tp, 'TP'
                    break
                elif low <= sl:
                    exit_time, exit_price, outcome = idx, sl, 'BE' if be_active and sl == entry_price else 'SL'
                    break
            elif entry_type == 'Short':
                if entry_price - low >= 5:
                    sl = entry_price
                    be_active = True
                if low <= tp:
                    exit_time, exit_price, outcome = idx, tp, 'TP'
                    break
                elif high >= sl:
                    exit_time, exit_price, outcome = idx, sl, 'BE' if be_active and sl == entry_price else 'SL'
                    break

            max_fav = max(max_fav, high - entry_price if entry_type == 'Long' else entry_price - low)
            max_adv = max(max_adv, entry_price - low if entry_type == 'Long' else high - entry_price)

        if outcome is None and not after_entry.empty:
            last_idx = after_entry.index[-1]
            last_close = after_entry.iloc[-1]['Close']
            exit_time = last_idx
            exit_price = last_close
            outcome = 'close_at_end'

        if exit_price is None:
            continue

        duration = exit_time - entry_time
        profit = (exit_price - entry_price) if entry_type == 'Long' else (entry_price - exit_price)
        profit_currency = profit * 50

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
            'Alert_Time': signal_time,
            'Entry_Time': entry_time,
            'Entry': entry_type,
            'Entry_Price': entry_price,
            'Trigger_Level': trigger_level,
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
    os.makedirs('outputs', exist_ok=True)
    summary_file_path = os.path.join('outputs', 'summary_orders.csv')

    if os.path.exists(summary_file_path) and os.path.getsize(summary_file_path) > 0:
        existing_df = pd.read_csv(summary_file_path)
        updated_df = pd.concat([existing_df, df_orders], ignore_index=True)
        updated_df.to_csv(summary_file_path, index=False)
        print(f"✅ Archivo actualizado: {summary_file_path}")
    else:
        df_orders.to_csv(summary_file_path, index=False)
        print(f"✅ Archivo creado: {summary_file_path}")

    return df_orders
