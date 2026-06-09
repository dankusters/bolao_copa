from whatsapp.sender import enviar_texto, enviar_cta
from sheets.detalhe_jogo import buscar_detalhe_por_jogo
from utils.flags import bandeira


def handle_detalhe_jogo(numero: str):
    detalhes = buscar_detalhe_por_jogo()

    if not detalhes:
        enviar_texto(numero, "Nenhum jogo do dia atualizado ainda. Aguarde! ⏳")
        enviar_cta(numero)
        return

    linhas = ["*Últimos 6 jogos atualizados:*\n"]
    for item in detalhes:
        jogo = item["jogo"]
        apostas = item["apostas"]

        mandante = jogo["time_mandante"]
        visitante = jogo["time_visitante"]
        gm = jogo["gols_mandante"]
        gv = jogo["gols_visitante"]
        flag_m = bandeira(mandante)
        flag_v = bandeira(visitante)
        linhas.append(f"*{flag_m} {mandante} {gm} x {gv} {visitante} {flag_v}*")
        linhas.append("")

        if not apostas:
            linhas.append("  Nenhuma aposta registrada para este jogo.")
        else:
            for a in apostas:
                nome = a.get("nome", "")
                gm_a = a.get("gols_mandante", "")
                gv_a = a.get("gols_visitante", "")
                pts = _to_int(a.get("pontos_totais", 0))
                plural = "ponto" if pts == 1 else "pontos"
                linhas.append(f"- {nome} apostou {mandante} {gm_a} x {gv_a} {visitante} ({pts} {plural})")

        linhas.append("")

    enviar_texto(numero, "\n".join(linhas).strip())
    enviar_cta(numero)


def _to_int(val) -> int:
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0
