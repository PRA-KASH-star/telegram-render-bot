
import os
import requests
from flask import Flask

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

def send_to_owner():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    try:
        res = requests.get(url).json()
        chat_id = res['result'][0]['message']['chat']['id']
        msg_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": "✅ Bot deployed successfully on Render!"
        }
        requests.post(msg_url, data=data)
    except Exception as e:
        print("Error sending message:", e)

@app.route("/")
def home():
    send_to_owner()
    return "Telegram bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
