
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from indicators import calculate_indicators
from data_loader import load_data
from screener import run_screener
from alerts import check_alerts
from telegram_bot import send_telegram_alert
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="TradingView Clone", layout="wide")

st.title("ðŸ“Š TradingView Clone with Screener + Telegram Alerts")

# Sidebar for input
asset = st.sidebar.selectbox("Select Asset", ["BTC/USD", "ETH/USD", "XAU/USD", "EUR/USD", "AAPL", "TSLA"])
timeframe = st.sidebar.selectbox("Timeframe", ["1min", "5min", "15min"])
show_signals = st.sidebar.checkbox("Show Alerts Only", value=False)

api_key = os.getenv("TWELVE_DATA_API_KEY")

if not api_key:
    st.warning("Please set your Twelve Data API key in the .env file.")
else:
    with st.spinner("Loading data..."):
        df = load_data(asset, timeframe, api_key)
        if df is not None and not df.empty:
            df = calculate_indicators(df)

            # Plot chart
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Candles'
            ))

            fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], mode='lines', name='EMA 20'))
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], mode='lines', name='EMA 50'))
            fig.update_layout(title=f"{asset} - {timeframe}", xaxis_rangeslider_visible=False)

            st.plotly_chart(fig, use_container_width=True)

            # Screener Results
            if st.button("Run Screener"):
                results = run_screener(df, asset)
                if not results.empty:
                    st.success("Screener found signals:")
                    st.dataframe(results)
                    if st.button("Send to Telegram"):
                        msg = f"Screener Signal for {asset} - {timeframe}\n{results.to_string(index=False)}"
                        send_telegram_alert(msg)
                else:
                    st.info("No matching conditions found.")

            # Alerts
            alerts = check_alerts(df)
            if alerts and show_signals:
                st.error(f"âš ï¸ Alert Triggered: {alerts}")
                if st.button("Send Alert to Telegram"):
                    send_telegram_alert(f"âš ï¸ Alert for {asset} - {timeframe}: {alerts}")
        else:
            st.warning("No data returned. Check your API key and asset symbol.")
