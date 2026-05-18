from estado import aguardando_resposta
from whatsapp.sender import enviar_texto


def handle_botao(numero: str, msg: dict):
    texto_botao = msg["button"]["text"]
    payload_botao = msg["button"]["payload"]
    print(f"[BTN] Botão '{texto_botao}' (payload: {payload_botao}) de {numero}")

    enviar_texto(numero, "Você fez uma aposta!")
    aguardando_resposta.add(numero)