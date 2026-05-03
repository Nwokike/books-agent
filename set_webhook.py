import os
import httpx
import sys
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
# Adjust to your live domain when deploying
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://books-agent-production.up.render.com/webhook")

if not TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN not set.")
    sys.exit(1)

def set_webhook():
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    response = httpx.post(url, json={"url": WEBHOOK_URL})
    print(response.json())

if __name__ == "__main__":
    set_webhook()
