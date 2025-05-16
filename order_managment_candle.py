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
    target_profit=10,
    stop_lost=3,
    discount_short=-0.20,
    discount_long=20
) -> pd.DataFrame:

    # Asegura tipos válidos
    target_profit = float(target_profit)
    stop_lost = float(stop_lost)

    # Asegura que los precios sean numéricos
    cols = ['Open', 'High', 'Low', 'Close']
    df_subset[cols] = df_subset[cols].apply(pd.to_numeric, errors='coerce')

    # Usar solo datos posteriores al rango
    df = df_subset[df_subset.index > END_TIME].copy()

    # Crear etiquetas de entrada
    df['Entry'] = df['Close'].apply(
        lambda x: 'Short' if x > y1_value else ('Long' if x < y0_value else None)
    )
    df = df[df['Entry'].notna()].copy()

    entradas_finales = []
    pos = 0  # ✅ solo una entrada permitida

    for idx, row in df.iterrows():
        if pos >= 1:
            break

        entry_type = row['Entry']
        entry_price = float(row['Close'])
        entry_time = idx

        entradas_finales.append((entry_time, entry_type, entry_price))
        pos += 1

    results = []

    for entry_time, entry_type, entry_price in entradas_finales:
        if entry_type == 'Long':
            tp = entry_price + target_profit
            sl = entry_price - stop_lost
        elif entry_type == 'Short':
            tp = entry_price - target_profit
            sl = entry_price + stop_lost
        else:
            continue

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
                if high >= tp:
                    exit_time, exit_price, outcome = idx, tp, 'TP'
                    break
                elif low <= sl:
                    exit_time, exit_price, outcome = idx, sl, 'SL'
                    break
            elif entry_type == 'Short':
                if low <= tp:
                    exit_time, exit_price, outcome = idx, tp, 'TP'
                    break
                elif high >= sl:
                    exit_time, exit_price, outcome = idx, sl, 'SL'
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

        # Ruptura opuesta (opcional)
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
            'Alert_Time': entry_time,
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

    if os.path.exists(summary_file_path):
        existing_df = pd.read_csv(summary_file_path)
        updated_df = pd.concat([existing_df, df_orders], ignore_index=True)
        updated_df.to_csv(summary_file_path, index=False)
        print(f"✅ Archivo actualizado: {summary_file_path}")
    else:
        df_orders.to_csv(summary_file_path, index=False)
        print(f"✅ Archivo creado: {summary_file_path}")

    return df_orders
