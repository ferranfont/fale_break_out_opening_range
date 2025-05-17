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
    target_profit=15,
    stop_lost=3,
    discount_short=-0.20,
    discount_long=0.20,
    tolerancia=0.5
) -> pd.DataFrame:

    target_profit = float(target_profit)
    stop_lost = float(stop_lost)
    tolerancia = float(tolerancia)

    cols = ['Open', 'High', 'Low', 'Close']
    df_subset.loc[:, cols] = df_subset[cols].apply(pd.to_numeric, errors='coerce')

    df = df_subset[df_subset.index > END_TIME].copy()

    df['Signal'] = df['Close'].apply(
        lambda x: 'Short' if x > y1_value else ('Long' if x < y0_value else None)
    )
    signals = df[df['Signal'].notna()]

    entradas_finales = []
    pos = 0  # solo una entrada por día

    for signal_idx, signal_row in signals.iterrows():
        signal_type = signal_row['Signal']
        start_loc = df_subset.index.get_loc(signal_idx)
        rolling_df = df_subset.iloc[start_loc:].copy()

        if signal_type == 'Short':
            base_val = rolling_df.iloc[0]['High']
            comp_col = 'High'
        elif signal_type == 'Long':
            base_val = rolling_df.iloc[0]['Low']
            comp_col = 'Low'
        else:
            continue

        for i in range(1, len(rolling_df)):
            current_val = rolling_df.iloc[i][comp_col]
            current_time = rolling_df.index[i]

            if abs(current_val - base_val) <= tolerancia:
                entry_price = rolling_df.iloc[i]['Close']
                entry_time = current_time
                entradas_finales.append((entry_time, signal_type, entry_price, signal_idx))
                pos += 1
                break
            else:
                base_val = current_val

        if pos >= 1:
            break

    results = []

    for entry_time, entry_type, entry_price, signal_time in entradas_finales:
        tp = entry_price + target_profit if entry_type == 'Long' else entry_price - target_profit
        sl = entry_price - stop_lost if entry_type == 'Long' else entry_price + stop_lost
        be_active = False  # flag de trailing stop a BE

        after_entry = df_subset[df_subset.index > entry_time]
        max_fav = 0
        max_adv = 0
        exit_price = None
        exit_time = None
        outcome = None

        for idx, bar in after_entry.iterrows():
            high = bar['High']
            low = bar['Low']

            # Activar trailing stop a BE si va +5 puntos a favor
            if entry_type == 'Long':
                if high - entry_price >= 10:
                    sl = entry_price+3
                    be_active = True
                if high >= tp:
                    exit_time, exit_price, outcome = idx, tp, 'TP'
                    break
                elif low <= sl:
                    exit_time, exit_price, outcome = idx, sl, 'BE' if be_active and sl == entry_price else 'SL'
                    break
            elif entry_type == 'Short':
                if entry_price - low >= 10:
                    sl = entry_price-3
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
