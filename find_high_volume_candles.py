import pandas as pd

def df_high_volumen_candles(df, trading_window: tuple, y0_value: float, y1_value: float, n: int = 2, factor: float = 1.1):
    """
    Identifica velas con volumen alto si cumplen tres condiciones:
    1) volumen > media de las n anteriores * factor
    2) volumen > todas las n anteriores (absoluto)
    3) cierre fuera del rango [y0, y1]
    """
    df_window = df[(df.index >= trading_window[0]) & (df.index <= trading_window[1])].copy()

    # Media y máximo del volumen anterior
    df_window['Volumen_Media'] = df_window['Volumen'].rolling(window=n).mean()
    df_window['Volumen_Max_Anterior'] = df_window['Volumen'].shift(1).rolling(window=n).max()

    df_window['Volumen_Alto'] = (
        (df_window['Volumen'] > df_window['Volumen_Media'] * factor) &  # que su volumen sea superior en un factor al volumen medio de las n velas anteriores
        (df_window['Volumen'] > df_window['Volumen_Max_Anterior']) &  # en valor absoluto que su volumen sea superior al volumen de las n velas anteriores
        ((df_window['Close'] < y0_value) | (df_window['Close'] > y1_value))  # qué esté fuera del rectángulo o rango inicial
    )

    # Prevenir True en las primeras n filas

    df_window.loc[df_window.index[:n], 'Volumen_Alto'] = False
    df_window['Entry'] = df_window['Close'].apply(lambda x: 'Short' if x > y1_value else ('Long' if x < y0_value else None))

    return df_window[df_window['Volumen_Alto']]

