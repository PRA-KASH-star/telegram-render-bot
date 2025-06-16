
from flask import Flask
import requests
import os

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)

@app.route("/")
def home():
    send_telegram_message("🔔 Render App started successfully!")
    return "Telegram Bot Running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
