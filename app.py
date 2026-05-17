from flask import Flask, request, jsonify
from config import VERIFY_TOKEN, RECIPIENT_NUMBER
from whatsapp import enviar_mensagem, processar_webhook

app = Flask(__name__)


# rota raiz
@app.route("/")
def root():
    return "Hello World!"


# ============================================================
# WEBHOOK - VERIFICACAO (GET)
# A Meta envia um GET para validar o webhook na configuracao
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
    processar_webhook(data)
    return jsonify({"status": "ok"}), 200


# ============================================================
# ROTA DE TESTE - Enviar mensagem manualmente
# ============================================================
@app.route("/enviar", methods=["GET"])
def enviar_teste():
    resultado = enviar_mensagem(RECIPIENT_NUMBER, "Daniel")
    return jsonify(resultado)


# ============================================================
# INICIAR SERVIDOR
# ============================================================
if __name__ == "__main__":
    print("=> Servidor rodando em http://localhost:5000")
    print("=> Webhook: http://localhost:5000/webhook")
    print("=> Teste de envio: http://localhost:5000/enviar")
    app.run(debug=True, port=5000)