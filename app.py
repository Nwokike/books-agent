import os
import sys
from dotenv import load_dotenv

# Load env variables from root directory first
load_dotenv()

# We need the telegram framework from ADK
from google.adk.ui.telegram import (
    TelegramBotClient,
    TelegramFrameworkConfig,
    create_telegram_bot_app
)
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService

from orchestrator.agent import root_agent

if not os.environ.get("TELEGRAM_BOT_TOKEN"):
    print("WARNING: TELEGRAM_BOT_TOKEN is not set.")

config = TelegramFrameworkConfig(
    client=TelegramBotClient(
        bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
    ),
    runner=Runner(
        app_name="books-agent",
        agent=root_agent,
        session_service=InMemorySessionService(),
    ),
    server_address="0.0.0.0",
    server_port=8082,  # Running on 8082 to avoid conflicts with ArchiveAgent (8080) and NotesAgent (8081)
    webhook_path="/webhook",
)

app = create_telegram_bot_app(config)

if __name__ == "__main__":
    import uvicorn
    # Use standard Uvicorn config for polling or webhook dev
    uvicorn.run(app, host="0.0.0.0", port=8082)
