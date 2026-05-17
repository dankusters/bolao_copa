import requests
from config import ACCESS_TOKEN, API_URL


def enviar_mensagem(numero_destino: str, texto: str):
    """Envia uma mensagem usando o template 'main_bolao' via WhatsApp Cloud API."""
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "template",
        "template": {
            "name": "main_bolao",
            "language": {
                "code": "pt_BR"
            },
            "components": [
                {
                    "type": "header",
                    "parameters": [
                        {
                            "type": "image",
                            "image": {
                                "link": "https://placehold.co/400x400/png"
                            }
                        }
                    ]
                },
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": texto
                        }
                    ]
                }
            ]
        }
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"[OK] Mensagem enviada para {numero_destino}")
    else:
        print(f"[ERRO] {response.status_code}: {response.json()}")

    return response.json()


def processar_webhook(data: dict):
    """Processa os dados recebidos pelo webhook da Meta."""
    if data.get("object") != "whatsapp_business_account":
        return

    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])

            for msg in messages:
                numero_remetente = msg.get("from")
                tipo_mensagem = msg.get("type")

                if tipo_mensagem == "text":
                    texto_recebido = msg["text"]["body"]
                    print(f"[MSG] Mensagem de {numero_remetente}: {texto_recebido}")

                    # Responder automaticamente (exemplo)
                    enviar_mensagem(
                        numero_remetente,
                        f"Recebi sua mensagem: \"{texto_recebido}\""
                    )
                else:
                    print(f"[MSG] Mensagem tipo '{tipo_mensagem}' de {numero_remetente}")
