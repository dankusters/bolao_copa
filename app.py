from flask import Flask, request, jsonify, make_response
from config import VERIFY_TOKEN, RECIPIENT_NUMBER
from whatsapp.sender import enviar_template
from whatsapp.webhook import processar_webhook

app = Flask(__name__)


# rota raiz
@app.route("/")
def root():
    return "Bolão dos Camargos - online!"


# ============================================================
# WEBHOOK - VERIFICACAO (GET)
# A Meta envia um GET para validar o webhook na configuracao
# ============================================================
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    print(f"Verificação recebida → mode={mode}, token={token}")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verificado com sucesso!")
        response = make_response(challenge, 200)
        response.headers["Content-Type"] = "text/plain"
        response.headers["ngrok-skip-browser-warning"] = "1"
        return response

    print("Falha na verificação do webhook.")
    return "Forbidden", 403


# ============================================================
# WEBHOOK - RECEBER MENSAGENS (POST)
# A Meta envia um POST toda vez que uma mensagem chega
# ============================================================
@app.route("/webhook", methods=["POST"])
def receber_mensagem():
    data = request.get_json()
    processar_webhook(data)
    return jsonify({"status": "ok"}), 200


# ============================================================
# ROTA DE TESTE - Enviar mensagem manualmente
# ============================================================
@app.route("/enviar", methods=["GET"])
def enviar_teste():
    resultado = enviar_template(RECIPIENT_NUMBER)
    return jsonify(resultado)


# ============================================================
# INICIAR SERVIDOR
# ============================================================
if __name__ == "__main__":
    print("=> Servidor rodando em http://localhost:5000")
    print("=> Webhook: http://localhost:5000/webhook")
    print("=> Teste de envio: http://localhost:5000/enviar")
    app.run(debug=True, port=5000)