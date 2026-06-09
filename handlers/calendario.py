from datetime import date
from whatsapp.sender import enviar_texto, enviar_cta
from sheets.calendario import buscar_calendario
from utils.flags import bandeira

_DIAS_PT = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def handle_calendario(numero: str):
    jogos = buscar_calendario(dias_futuros=5)

    if not jogos:
        enviar_texto(numero, "Nenhum jogo encontrado nos próximos dias.")
        enviar_cta(numero)
        return

    hoje = date.today()
    blocos = ["📅 *Jogos de hoje e dos próximos cinco dias*\n"]
    data_atual = None

    for jogo in jogos:
        dt = jogo["_dt"]
        dia = dt.date()

        if dia != data_atual:
            if data_atual is not None:
                blocos.append("")
            data_atual = dia
            dia_semana = _DIAS_PT[dia.weekday()]
            if dia == hoje:
                cabecalho_dia = f"*Hoje, {dia.strftime('%d/%m')}*"
            elif dia < hoje:
                cabecalho_dia = f"*{dia_semana}, {dia.strftime('%d/%m')}*"
            else:
                cabecalho_dia = f"*{dia_semana}, {dia.strftime('%d/%m')}*"
            blocos.append(cabecalho_dia)

        mandante = jogo.get("time_mandante", "")
        visitante = jogo.get("time_visitante", "")
        flag_m = bandeira(mandante)
        flag_v = bandeira(visitante)
        gm = str(jogo.get("gols_mandante", "")).strip()
        gv = str(jogo.get("gols_visitante", "")).strip()

        if gm and gv:
            linha = f"{flag_m} {mandante} {gm} x {gv} {visitante} {flag_v} ✅"
        else:
            hora = dt.strftime("%H:%M")
            linha = f"{flag_m} {mandante} x {visitante} {flag_v} — {hora}"

        blocos.append(linha)

    enviar_texto(numero, "\n".join(blocos))
    enviar_cta(numero)
