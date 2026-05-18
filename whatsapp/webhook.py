from handlers.texto import handle_texto
from handlers.botao import handle_botao


def processar_webhook(data: dict):
    if data.get("object") != "whatsapp_business_account":
        return

    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])

            for msg in messages:
                numero_remetente = msg.get("from")
                tipo_mensagem = msg.get("type")

                if tipo_mensagem == "text":
                    handle_texto(numero_remetente, msg)
                elif tipo_mensagem == "button":
                    handle_botao(numero_remetente, msg)
                else:
                    print(f"[MSG] Mensagem tipo '{tipo_mensagem}' de {numero_remetente}")
