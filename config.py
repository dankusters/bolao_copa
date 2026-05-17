import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Credenciais Meta / WhatsApp Cloud API
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
RECIPIENT_NUMBER = os.getenv("RECIPIENT_NUMBER")

# API
API_VERSION = "v25.0"
API_URL = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"
