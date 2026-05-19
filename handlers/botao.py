from handlers.aposta import iniciar_aposta
from whatsapp.sender import enviar_texto


def handle_botao(numero: str, msg: dict):
    texto_botao = msg["button"]["text"].strip().lower()
    payload_botao = msg["button"]["payload"]
    print(f"[BTN] Botão '{texto_botao}' (payload: {payload_botao}) de {numero}")

    if "aposta" in texto_botao:
        iniciar_aposta(numero)
    elif "ranking" in texto_botao:
        enviar_texto(numero, "Ranking em breve! 🏆")
    elif "apostador" in texto_botao:
        enviar_texto(numero, "Detalhes por apostador em breve! 📊")
    elif "jogo" in texto_botao:
        enviar_texto(numero, "Detalhes por jogo em breve! ⚽")
    else:
        enviar_texto(numero, f"Botão '{texto_botao}' não reconhecido.")
