import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv(override=True)

app = Flask(__name__)

# ============================================================
# CONFIGURAÇÃO
# ============================================================
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
API_VERSION = "v25.0"
API_URL = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"


# rota raiz
@app.route("/")
def root():
    return "Hello World!"

# ============================================================
# ENVIAR MENSAGEM DE TEXTO
# ============================================================
def enviar_mensagem(numero_destino: str, texto: str):
    """Envia uma mensagem de texto simples via WhatsApp Cloud API."""
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {
                "code": "en_US",
                "policy": "deterministic"
            }
        }
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        print(f"[OK] Mensagem enviada para {numero_destino}")
    else:
        print(f"[ERRO] {response.status_code}: {response.json()}")

    return response.json()


# ============================================================
# WEBHOOK - VERIFICAÇÃO (GET)
# A Meta envia um GET para validar o webhook na configuração
# ============================================================
@app.route("/webhook", methods=["GET"])
def verificar_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("[OK] Webhook verificado com sucesso!")
        return challenge, 200
    else:
        print("[ERRO] Falha na verificacao do webhook")
        return "Forbidden", 403


# ============================================================
# WEBHOOK - RECEBER MENSAGENS (POST)
# A Meta envia um POST toda vez que uma mensagem chega
# ============================================================
@app.route("/webhook", methods=["POST"])
def receber_mensagem():
    data = request.get_json()

    # Verificar se é uma notificação válida do WhatsApp
    if data.get("object") == "whatsapp_business_account":
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

    return jsonify({"status": "ok"}), 200


# ============================================================
# ROTA DE TESTE - Enviar mensagem manualmente
# ============================================================
@app.route("/enviar", methods=["GET"])
def enviar_teste():
    numero = os.getenv("RECIPIENT_NUMBER")
    resultado = enviar_mensagem(numero, "Ola! Mensagem de teste do Bolao da Copa!")
    return jsonify(resultado)


# ============================================================
# INICIAR SERVIDOR
# ============================================================
if __name__ == "__main__":
    print("=> Servidor rodando em http://localhost:5000")
    print("=> Webhook: http://localhost:5000/webhook")
    print("=> Teste de envio: http://localhost:5000/enviar")
    app.run(debug=True, port=5000, use_reloader=False)