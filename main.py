
import requests
import pandas as pd
import time
from datetime import datetime
import pytz
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload)

def compute_rsi(data, period=14):
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def fetch_binance_data(symbol="BTCUSDT", interval="5m", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
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
    signal, reason = None, []

    if latest['RSI'] < 30:
        signal, reason = "CALL", ["RSI Oversold (<30)"]
    elif latest['RSI'] > 70:
        signal, reason = "PUT", ["RSI Overbought (>70)"]

    if latest['EMA5'] > latest['EMA20']:
        if signal == "CALL": reason.append("EMA Bullish Confirmed")
        elif not signal: signal, reason = "CALL", ["EMA Bullish (5 > 20)"]
    elif latest['EMA5'] < latest['EMA20']:
        if signal == "PUT": reason.append("EMA Bearish Confirmed")
        elif not signal: signal, reason = "PUT", ["EMA Bearish (5 < 20)"]

    if latest['close'] > latest['open'] and prev['close'] < prev['open']:
        if signal == "CALL": reason.append("Bullish Engulfing Confirmed")
    elif latest['close'] < latest['open'] and prev['close'] > prev['open']:
        if signal == "PUT": reason.append("Bearish Engulfing Confirmed")

    return signal, reason

def run_bot():
    ist = pytz.timezone("Asia/Kolkata")
    while True:
        try:
            df = fetch_binance_data()
            signal, reasons = generate_signal(df)
            now = datetime.now(ist).strftime("%I:%M %p")
            if signal:
                msg = f"🕒 {now} IST\n📊 SIGNAL: {signal}\n💡 Reason: " + ", ".join(reasons)
            else:
                msg = f"🕒 {now} IST\n⚠️ No strong signal."
            send_telegram(msg)
            print("Signal sent:", msg)
        except Exception as e:
            print("Error:", e)
        time.sleep(300)

run_bot()
