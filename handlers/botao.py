from handlers.aposta import iniciar_aposta
from handlers.apostas_dia import handle_apostas_dia
from handlers.ranking import handle_ranking, handle_ranking_familia
from handlers.detalhe_jogo import handle_detalhe_jogo
from handlers.detalhe_apostador import iniciar_detalhe_apostador
from handlers.calendario import handle_calendario
from whatsapp.sender import enviar_texto


def handle_botao(numero: str, msg: dict):
    texto_botao = msg["button"]["text"].strip().lower()
    payload_botao = msg["button"]["payload"]
    print(f"[BTN] Botão '{texto_botao}' (payload: {payload_botao}) de {numero}")

    if "apostador" in texto_botao:
        iniciar_detalhe_apostador(numero)
    elif "dia" in texto_botao:
        handle_apostas_dia(numero)
    elif "aposta" in texto_botao:
        iniciar_aposta(numero)
    elif "família" in texto_botao or "familia" in texto_botao:
        handle_ranking_familia(numero)
    elif "ranking" in texto_botao:
        handle_ranking(numero)
    elif "calend" in texto_botao:
        handle_calendario(numero)
    elif "jogo" in texto_botao:
        handle_detalhe_jogo(numero)
    else:
        enviar_texto(numero, f"Botão '{texto_botao}' não reconhecido.")
