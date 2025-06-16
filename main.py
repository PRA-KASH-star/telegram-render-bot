import requests
import pandas as pd
import time
from datetime import datetime
import pytz
import os

# Telegram setup
TELEGRAM_TOKEN = "PASTE_YOUR_TELEGRAM_TOKEN_HERE"
CHAT_ID = "PASTE_YOUR_CHAT_ID_HERE"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)

def compute_rsi(data, period=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def fetch_binance_data(symbol="BTCUSDT", interval="5m", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close',
        'volume', 'close_time', 'quote_asset_volume',
        'number_of_trades', 'taker_buy_base_asset_volume',
        'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df[['open', 'high', 'low', 'close']] = df[['open', 'high', 'low', 'close']].astype(float)
    return df

def generate_signal(df):
    df['EMA5'] = df['close'].ewm(span=5).mean()
    df['EMA20'] = df['close'].ewm(span=20).mean()
    df['RSI'] = compute_rsi(df)
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    signal = None
    reason = []

    if latest['RSI'] < 30:
        signal = "CALL"
        reason.append("RSI Oversold (<30)")
    elif latest['RSI'] > 70:
        signal = "PUT"
        reason.append("RSI Overbought (>70)")

    if latest['EMA5'] > latest['EMA20']:
        if signal == "CALL":
            reason.append("EMA Bullish Confirmed")
        elif signal is None:
            signal = "CALL"
            reason.append("EMA Bullish (5 > 20)")
    elif latest['EMA5'] < latest['EMA20']:
        if signal == "PUT":
            reason.append("EMA Bearish Confirmed")
        elif signal is None:
            signal = "PUT"
            reason.append("EMA Bearish (5 < 20)")

    if latest['close'] > latest['open'] and prev['close'] < prev['open']:
        if signal == "CALL":
            reason.append("Bullish Engulfing Confirmed")
    elif latest['close'] < latest['open'] and prev['close'] > prev['open']:
        if signal == "PUT":
            reason.append("Bearish Engulfing Confirmed")

    return signal, reason

def run_bot():
    ist = pytz.timezone("Asia/Kolkata")
    while True:
        try:
            df = fetch_binance_data()
            signal, reasons = generate_signal(df)
            now = datetime.now(ist).strftime("%I:%M %p")
            if signal:
                message = f"🕒 {now} IST\\n📊 SIGNAL: {signal}\\n💡 Reason: " + ", ".join(reasons)
            else:
                message = f"🕒 {now} IST\\n⚠️ No strong signal detected."
            send_telegram(message)
            print("Signal sent:", message)
        except Exception as e:
            print("Error:", e)
        time.sleep(300)  # 5 min wait

run_bot()
