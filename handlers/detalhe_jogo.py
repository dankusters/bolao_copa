from whatsapp.sender import enviar_texto
from sheets.detalhe_jogo import buscar_detalhe_por_jogo


def handle_detalhe_jogo(numero: str):
    detalhes = buscar_detalhe_por_jogo()

    if not detalhes:
        enviar_texto(numero, "Nenhum jogo do dia atualizado ainda. Aguarde! ⏳")
        return

    linhas = ["*Jogos já atualizados:*\n"]
    for item in detalhes:
        jogo = item["jogo"]
        apostas = item["apostas"]

        mandante = jogo["time_mandante"]
        visitante = jogo["time_visitante"]
        gm = jogo["gols_mandante"]
        gv = jogo["gols_visitante"]
        linhas.append(f"*{mandante} {gm} x {visitante} {gv}*")

        if not apostas:
            linhas.append("  Nenhuma aposta registrada para este jogo.")
        else:
            for a in apostas:
                nome = a.get("nome", "")
                gm_a = a.get("gols_mandante", "")
                gv_a = a.get("gols_visitante", "")
                pts = _to_int(a.get("pontos_totais", 0))
                plural = "ponto" if pts == 1 else "pontos"
                linhas.append(f"- {nome} apostou {mandante} {gm_a} x {visitante} {gv_a} ({pts} {plural})")

        linhas.append("")

    enviar_texto(numero, "\n".join(linhas).strip())


def _to_int(val) -> int:
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0
