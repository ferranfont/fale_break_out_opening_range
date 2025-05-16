import os
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def graficar_precio(df, too_late_patito_negro, titulo, START_TIME, END_TIME, y0_value, y1_value, first_breakout_time=None, first_breakout_price=None, first_breakdown_time=None, first_breakdown_price=None, high_volume_df=None, df_orders=None):
    if df.empty or not all(col in df.columns for col in ['Open', 'High', 'Low', 'Close']):
        print("❌ DataFrame vacío o faltan columnas OHLC.")
        return

    os.makedirs("charts", exist_ok=True)

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], utc=True)
        df.set_index('Date', inplace=True)
    df.index = df.index.tz_convert('Europe/Madrid')

    expansion = 0.38
    y1_expansion = y1_value + (y1_value - y0_value) * expansion
    y0_expansion = y0_value - (y1_value - y0_value) * expansion
    opening_range = y1_value - y0_value
    midpoint = (y1_value+y0_value)/2
    stop_line_high = y1_value + opening_range * 0.90  # Stop en función del rango de la apertura menos un factor
    stop_line_low = y0_value - opening_range * 0.90   # Stop en función del rango de la apertura menos un factor

    y0_hotspot = y0_expansion + opening_range * 0.20 # hotspot relativo al rango de la pre apertura
    y1_hotspot = y1_expansion - opening_range * 0.20 # hotspot relativo al rango de la pre apertura

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.805, 0.20],
        vertical_spacing=0,
        subplot_titles=(titulo, '')
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        increasing=dict(line=dict(color='black'), fillcolor='rgba(57, 255, 20, 0.5)'),
        decreasing=dict(line=dict(color='black'), fillcolor='red'),
        hoverinfo='none'
    ), row=1, col=1)

    if 'Volumen' in df.columns:
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['Volumen'],
            marker_color='blue',
            opacity=0.5,
            hoverinfo='skip',
            name='Volumen'
        ), row=2, col=1)

    # Shapes
    fig.add_shape(type="rect", x0=START_TIME, x1=END_TIME, y0=y0_value, y1=y1_value,  # cuadradito de apertura
                  xref='x', yref='y1', line=dict(color='lightblue', width=1),
                  fillcolor='rgba(173, 216, 230, 0.5)', layer='below')

    fig.add_shape(type="rect", x0=END_TIME, x1=too_late_patito_negro, y0=y0_expansion, y1=y1_expansion, # cuadradito tras la apertura
                  xref='x', yref='y1', line=dict(color='rgba(210, 255, 210, 0.5)', width=1),
                  fillcolor='rgba(210, 255, 210, 0.5)', layer='below')
    
    fig.add_shape(type="rect", x0=END_TIME, x1=too_late_patito_negro, y0=y0_expansion, y1=y0_hotspot, #hotpsot inferior
                  xref='x', yref='y1', line=dict(color='green', width=0),
                  fillcolor='rgba(0, 128, 0, 0.4)', layer='below')
    
    fig.add_shape(type="rect", x0=END_TIME, x1=too_late_patito_negro, y0=y1_hotspot, y1=y1_expansion, #hotspot superior
                  xref='x', yref='y1', line=dict(color='green', width=0),
                  fillcolor='rgba(0, 128, 0, 0.4)', layer='below')

    fig.add_shape(type="line", x0=END_TIME, x1=END_TIME, y0=0, y1=1,
                  xref="x", yref="paper", line=dict(color="blue", width=1), opacity=0.5)

    fig.add_shape(type="line", x0=too_late_patito_negro, x1=too_late_patito_negro, y0=0, y1=1,
                  xref="x", yref="paper", line=dict(color="grey", width=1), opacity=0.5)
    
    fig.add_shape(type="line", x0=END_TIME, x1=too_late_patito_negro, y0=midpoint, y1=midpoint,  # linea midpoint del rango de pre apertura
                  xref="x", yref="y1", line=dict(color="black", width=1), opacity=0.6) 
    
    fig.add_shape(type="line", x0=END_TIME, x1=too_late_patito_negro, y0=stop_line_high, y1=stop_line_high, # linea stop superior
                  xref="x", yref="y1", line=dict(color="red", width=1), opacity=0.7)  
    
    fig.add_shape(type="line", x0=END_TIME, x1=too_late_patito_negro, y0=stop_line_low, y1=stop_line_low, # linea stop inferior
                  xref="x", yref="y1", line=dict(color="red", width=1), opacity=0.7)  


    if first_breakout_time and first_breakout_price:
        fig.add_trace(go.Scatter(
            x=[first_breakout_time],
            y=[first_breakout_price+1],
            mode='markers',
            marker=dict(color='orange', size=10, symbol='diamond'),
            name='First Breakout'
        ), row=1, col=1)

    if first_breakdown_time and first_breakdown_price:
        fig.add_trace(go.Scatter(
            x=[first_breakdown_time],
            y=[first_breakdown_price-1],
            mode='markers',
            marker=dict(color='orange', size=10, symbol='diamond'),
            name='First Breakdown'
        ), row=1, col=1)
    
    if high_volume_df is not None and not high_volume_df.empty:
        fig.add_trace(go.Scatter(
            x=high_volume_df.index,
            y=high_volume_df['Close']-1,
            mode='markers',
            marker=dict(symbol='circle', color='blue', size=10),
            name='High Volume Candles'
        ), row=1, col=1)

    if df_orders is not None and not df_orders.empty:   # establece las salidas
        fig.add_trace(go.Scatter(
            x=df_orders['Exit_Time'],
            y=df_orders['Exit_Price'],
            mode='markers',
            marker=dict(color='red', size=12, symbol='x'),
            name='Exit Orders'
        ), row=1, col=1)

    if df_orders is not None and not df_orders.empty:   # establece las salidas
        fig.add_trace(go.Scatter(
            x=df_orders['Entry_Time'],
            y=df_orders['Entry_Price'],
            mode='markers',
            marker=dict(color='lime', size=14, symbol='star'), # establece las entradas
            name='Exit Orders'
        ), row=1, col=1)

    if df_orders is not None and not df_orders.empty:
        for _, row in df_orders.iterrows():
            fig.add_trace(go.Scatter(
                x=[row['Entry_Time'], row['Exit_Time']],
                y=[row['Entry_Price'], row['Exit_Price']],
                mode='lines',
                line=dict(color='gray', width=1, dash='dot'),
                name='Entry to Exit'
            ), row=1, col=1)

    fig.update_layout(
        dragmode='pan',
        title=titulo,
        xaxis=dict(showgrid=False, showline=True, linewidth=1, linecolor='lightgrey', mirror=True),
        yaxis=dict(title="Precio", showgrid=False, showline=True, linewidth=1, linecolor='lightgrey', mirror=True),
        xaxis2=dict(showgrid=False, showline=True, linewidth=1, linecolor='lightgrey', mirror=False),
        yaxis2=dict(title="", showgrid=False, showline=True, linewidth=1, linecolor='lightgrey', mirror=True),
        xaxis_rangeslider_visible=False,
        width=1600,
        height=int(1500 * 0.6),
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(size=12, color="black"),
        plot_bgcolor='rgba(255,255,255,0.05)',
        paper_bgcolor='rgba(240,240,240,0.6)'
    )

    fig.update_traces(showlegend=False)
    config = dict(scrollZoom=True)

    output_file = f'charts/{titulo}.html'
    fig.write_html(output_file, config=config)
    print(f"📁 Gráfico interactivo guardado como {output_file}")

    import webbrowser
    webbrowser.open('file://' + os.path.realpath(output_file))
