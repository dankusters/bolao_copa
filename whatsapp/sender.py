import requests
from config import ACCESS_TOKEN, API_URL


def enviar_template(numero_destino: str):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "template",
        "template": {
            "name": "bolao_camargo",
            "language": {"code": "en"},
            "components": [
                {
                    "type": "header",
                    "parameters": [
                        {"type": "image", "image": {"link": "https://i.imgur.com/pXNmejn.jpeg"}}
                    ],
                },
            ],
        },
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"[OK] Template enviado para {numero_destino}")
    else:
        print(f"[ERRO] {response.status_code}: {response.json()}")
    return response.json()


def enviar_cta(numero_destino: str):
    enviar_texto(numero_destino, "_Digite qualquer texto para voltar ao menu inicial._")


def enviar_texto(numero_destino: str, texto: str):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "text",
        "text": {"body": texto},
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        print(f"[OK] Mensagem enviada para {numero_destino}")
    else:
        print(f"[ERRO] {response.status_code}: {response.json()}")
    return response.json()
