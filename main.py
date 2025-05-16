# ANDREA UNGER TRADING SYSTEM BREAK OUT OPENING RANGE
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import order_managment_candle as oemc
import chart_volume as chart
import plotly.graph_objects as go
import find_high_volume_candles as hv
import config
import os
now_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
load_dotenv()

last_100_dates_file = os.path.join('outputs', 'last_100_unique_dates.txt')

# Read the dates from the file into a list
dates = []
if os.path.exists(last_100_dates_file):
    with open(last_100_dates_file, 'r') as f:
        dates = [line.strip() for line in f.readlines()]
    print(f"✅ Loaded {len(dates)} dates from {last_100_dates_file}")

for fecha in dates:      
    print(f"\n📅 ANALIZANDO EL DIA: {fecha}")

    first_breakout_time = None
    first_breakout_price = None
    first_breakout_bool = False
    first_breakdown_time = None
    first_breakdown_price = None
    first_break_down_bool = False
    
    # Parámetros del Sistema
    #fecha = "2025-04-17"  # Fecha de inicio para el cuadradito
    hora = "15:30:00"     # Hora de inicio para el cuadradito
    lookback_min = 60    # Ventana de tiempo en minutos para el cuadradito
    entry_shift = 3     # Desplazamiento para la entrada (1 punto por encima del fractal)
    too_late_patito_negro= "16:30:00"  # Hora límite exigida para la formación del fractal patito negro para anular la entrada
    too_late_brake_fractal_pauta_plana = "16:30:00"  # Hora límite exigida para rotura del fractal patito negro para anular la entrada

    START_DATE = pd.Timestamp(fecha, tz='Europe/Madrid')
    END_DATE = pd.Timestamp(fecha, tz='Europe/Madrid')
    END_TIME = pd.Timestamp(f'{fecha} {hora}', tz='Europe/Madrid')
    START_TIME = END_TIME - pd.Timedelta(minutes=lookback_min)
    too_late_patito_negro = pd.Timestamp(f'{fecha} {too_late_patito_negro}', tz='Europe/Madrid')
    too_late_brake_fractal_pauta_plana = pd.Timestamp(f'{fecha} {too_late_patito_negro}', tz='Europe/Madrid')

    TRADING_WINDOW_TIME = (pd.Timestamp(f'{fecha} {hora}', tz='Europe/Madrid'), pd.Timestamp(f'{fecha} {too_late_patito_negro}', tz='Europe/Madrid'))

    # ====================================================
    # 📥 DESCARGA DE DATOS 
    # ====================================================
    directorio = '../DATA'
    nombre_fichero = 'export_es_2015_formatted.csv'
    ruta_completa = os.path.join(directorio, nombre_fichero)
    print("\n======================== 🔍 df  ==========================")
    df = pd.read_csv(ruta_completa)
    print('Fichero:', ruta_completa, 'importado')
    print(f"Características del Fichero Base: {df.shape}")
    # leo el vector o lista con las fechas a analizar
    # ====================================================

    # CREACIÓN DE UN SUBDATASET CON UN RANGO 
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], utc=True)  # Asegura que tiene zona horaria UTC
        df.set_index('Date', inplace=True)
    df.index = df.index.tz_convert('Europe/Madrid')
    df_subset = df[(df.index.date >= START_DATE.date()) & (df.index.date <= END_DATE.date())]

    print("\n====================== 🔍 df_subset  =====================")
    print(f"Subsegmento: Creado con {len(df_subset)} registros entre {START_DATE} y {END_DATE}")
    print(f"Característica del Subsegmento: {df_subset.shape}")


    # ====================================================
    # 💣 BUSQUEDA DEL MÁXIMO Y MÍNIMO DEL CUADRADITO 
    # ====================================================
    window_df = df[(df.index >= START_TIME) & (df.index <= END_TIME)]
    if not window_df.empty:
        y0_value = window_df['Low'].min()
        y1_value = window_df['High'].max()
    opening_range = y1_value - y0_value

    print(f"\nMínimo del Rango del Cuadradito y0_value: {y0_value}")
    print(f"Màximo del Rango del Cuadradito y1_value: {y1_value}")
    print(f"Rango Apertura del Cuadradito - opening_range: {opening_range}")

    # Filter only data after END_TIME (15:30)- BUSCAMOS ENTRAR TAN SÓLO DESPUÉS DE LAS 15:30
    after_open_df = df_subset[df_subset.index >= END_TIME] # filas después de la rotura
    breakout_rows = after_open_df[after_open_df['Close'] > y1_value] # filas por encima de la rotura y1_value
    if not breakout_rows.empty:
        first_breakout_time = breakout_rows.index[0]
        first_breakout_price = breakout_rows.iloc[0]['Close']
        first_breakout_bool = True
        print(f"⚡ High_Breakout_Range TRUE at: {first_breakout_time} with price {first_breakout_price}")

    # ====================================================
    # 💣 BUSQUEDA DE lA ROTURA DEL CUADRADITO
    # ====================================================

    # Check for low breakdown
    breakdown_rows = after_open_df[after_open_df['Close'] < y0_value]
    if not breakdown_rows.empty:
        first_breakdown_time = breakdown_rows.index[0]
        first_breakdown_price = breakdown_rows.iloc[0]['Close']
        first_break_down_bool = True
        print(f"⚡ Low_Breakdown TRUE at:  {first_breakdown_time} with price {first_breakdown_price}")
    else:
        first_break_down_bool = False
        first_breakdown_price = None
        first_breakdown_time = None

    # ====================================================
    # FIND HIGH VOLUME CANDLES
    # ====================================================

    df_high_volumen_candles = hv.df_high_volumen_candles(
        df_subset,
        TRADING_WINDOW_TIME,
        y0_value,
        y1_value,
        n=2, # Compara el volumen con el volumen medio de las dos anteriores velas
        factor=1 # Exige para True que  la vela actual tenga un volumen superior en un factor determinado un 1.1 es un 10% más de volumen
    )

    df_high_volumen_candles = df_high_volumen_candles[df_high_volumen_candles['Volumen_Alto']]

    # ====================================================
    # ORDER MANAGMENT
    # ====================================================

    df_orders = oemc.order_managment(
        df_subset,
        y0_value,
        y1_value,
        END_TIME,
        first_breakout_time,
        first_breakout_price,
        first_breakdown_time,
        first_breakdown_price
    )
    print("\n📌 Señales generadas por Order Management:")
    print(df_orders.T,"\n")

    # ====================================================
    # GRAFICACIÓN DE DATOS 
    # ====================================================
    titulo = f"Chart_{fecha}"       
    chart.graficar_precio(df_subset, too_late_patito_negro, titulo, START_TIME, END_TIME, y0_value, y1_value, first_breakout_time, first_breakout_price, first_breakdown_time, first_breakdown_price, df_high_volumen_candles, df_orders)




















































