from handlers.aposta import handle_aposta
from handlers.detalhe_apostador import handle_detalhe_apostador
from handlers.regras import REGRAS
from whatsapp.sender import enviar_template, enviar_texto
from sheets.apostas import verificar_e_marcar_primeiro_acesso


def handle_texto(numero: str, msg: dict):
    texto = msg["text"]["body"]
    print(f"[MSG] Mensagem de {numero}: {texto}")

    nome = verificar_e_marcar_primeiro_acesso(numero)
    if nome:
        enviar_texto(numero, f"Olá, {nome}! Como é seu primeiro acesso, leia atentamente as regras:{REGRAS}")

    if handle_aposta(numero, texto):
        return
    if handle_detalhe_apostador(numero, texto):
        return

    enviar_template(numero)
