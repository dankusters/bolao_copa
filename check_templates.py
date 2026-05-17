"""Script para listar templates disponiveis na WABA."""
import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

token = os.getenv("ACCESS_TOKEN")
phone_id = os.getenv("PHONE_NUMBER_ID")

# 1. Buscar o WABA ID a partir do Phone Number ID
r1 = requests.get(
    f"https://graph.facebook.com/v25.0/{phone_id}",
    params={"fields": "id,display_phone_number,verified_name"},
    headers={"Authorization": f"Bearer {token}"},
)
print("=== Info do Telefone ===")
print(r1.json())

# 2. Buscar WABA ID
r2 = requests.get(
    f"https://graph.facebook.com/v25.0/{phone_id}",
    params={"fields": "whatsapp_business_account"},
    headers={"Authorization": f"Bearer {token}"},
)
print("\n=== WABA ID ===")
data = r2.json()
print(data)

# Se encontrou WABA, listar templates
if "whatsapp_business_account" in data:
    waba_id = data["whatsapp_business_account"]["id"]
    r3 = requests.get(
        f"https://graph.facebook.com/v25.0/{waba_id}/message_templates",
        params={"fields": "name,language,status", "limit": 50},
        headers={"Authorization": f"Bearer {token}"},
    )
    print("\n=== Templates Disponiveis ===")
    templates = r3.json()
    if "data" in templates:
        for t in templates["data"]:
            print(f"  - {t['name']} ({t['language']}) - {t['status']}")
    else:
        print(templates)
