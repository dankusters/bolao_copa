from handlers.aposta import iniciar_aposta
from handlers.ranking import handle_ranking
from handlers.detalhe_jogo import handle_detalhe_jogo
from handlers.detalhe_apostador import iniciar_detalhe_apostador
from whatsapp.sender import enviar_texto


def handle_botao(numero: str, msg: dict):
    texto_botao = msg["button"]["text"].strip().lower()
    payload_botao = msg["button"]["payload"]
    print(f"[BTN] Botão '{texto_botao}' (payload: {payload_botao}) de {numero}")

    if "apostador" in texto_botao:
        iniciar_detalhe_apostador(numero)
    elif "aposta" in texto_botao:
        iniciar_aposta(numero)
    elif "ranking" in texto_botao:
        handle_ranking(numero)
    elif "jogo" in texto_botao:
        handle_detalhe_jogo(numero)
    else:
        enviar_texto(numero, f"Botão '{texto_botao}' não reconhecido.")
