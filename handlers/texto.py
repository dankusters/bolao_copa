from handlers.aposta import handle_aposta
from handlers.detalhe_apostador import handle_detalhe_apostador
from whatsapp.sender import enviar_template


def handle_texto(numero: str, msg: dict):
    texto = msg["text"]["body"]
    print(f"[MSG] Mensagem de {numero}: {texto}")

    if handle_aposta(numero, texto):
        return
    if handle_detalhe_apostador(numero, texto):
        return

    enviar_template(numero, "Olá! Use o menu abaixo para interagir com o bolão. 👇")
