from datetime import datetime
from zoneinfo import ZoneInfo
from whatsapp.sender import enviar_texto, enviar_cta
from sheets.detalhe_jogo import buscar_apostas_do_dia
from sheets.apostas import _parse_data_hora, tem_jogo_madrugada
from sheets.aposta_automatica import gerar_apostas_automaticas
from utils.flags import bandeira


def handle_apostas_dia(numero: str):
    if datetime.now(ZoneInfo("America/Sao_Paulo")).hour < 12:
        enviar_texto(numero, "Apressadinho(a), as apostas só são reveladas depois das 12:00.")
        enviar_cta(numero)
        return

    enviar_texto(numero, "Atualizando apostas, aguarde um instante... ⏳")
    gerar_apostas_automaticas()

    detalhes = buscar_apostas_do_dia()

    if not detalhes:
        enviar_texto(numero, "Hoje não há jogos programados.")
        enviar_cta(numero)
        return

    jogos = [item["jogo"] for item in detalhes]
    blocos = []
    if tem_jogo_madrugada(jogos):
        blocos.append("⚠️ Os jogos de madrugada do dia seguinte são considerados apostas de hoje.")

    for item in detalhes:
        jogo = item["jogo"]
        apostas = item["apostas"]

        dt = _parse_data_hora(str(jogo.get("data_hora", "")))
        data_hora = dt.strftime("%d/%m às %H:%M") if dt else str(jogo.get("data_hora", ""))

        mandante = jogo.get("time_mandante", "")
        visitante = jogo.get("time_visitante", "")
        flag_m = bandeira(mandante)
        flag_v = bandeira(visitante)
        cabecalho_m = f"{flag_m} {mandante}".strip()
        cabecalho_v = f"{flag_v} {visitante}".strip()

        linhas = [f"*{cabecalho_m} x {cabecalho_v}, {data_hora}*", ""]
        if not apostas:
            linhas.append("Nenhuma aposta registrada.")
        else:
            for a in apostas:
                robo = " 🤖" if a.get("origem") == "auto" else ""
                linhas.append(f"{a.get('nome', '')}{robo} {a.get('gols_mandante', '')} x {a.get('gols_visitante', '')}")

        blocos.append("\n".join(linhas))

    enviar_texto(numero, "\n\n".join(blocos))
    enviar_cta(numero)
