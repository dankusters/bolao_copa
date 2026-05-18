from estado import aguardando_resposta
from whatsapp.sender import enviar_template, enviar_texto


def handle_texto(numero: str, msg: dict):
    texto = msg["text"]["body"]
    print(f"[MSG] Mensagem de {numero}: {texto}")

    if numero in aguardando_resposta:
        aguardando_resposta.discard(numero)
        if texto.strip().lower() == "rafael":
            enviar_texto(numero, "Acertou!")
        else:
            enviar_texto(numero, "Errou!")
    else:
        enviar_template(numero, f"Recebi sua mensagem: \"{texto}\"")
