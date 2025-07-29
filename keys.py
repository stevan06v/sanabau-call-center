from dotenv import load_dotenv
import os

load_dotenv()

VAPI_API_TOKEN = os.getenv("VAPI_API_TOKEN")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
SHEETS_WEBHOOK_URL = os.getenv("SHEETS_WEBHOOK_URL")
SHEETS_GID = os.getenv("SHEETS_GID")