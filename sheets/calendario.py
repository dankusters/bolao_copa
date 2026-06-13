from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from sheets.client import get_worksheet
from sheets.apostas import _parse_data_hora

_TZ = ZoneInfo("America/Sao_Paulo")


def buscar_calendario(dias_passados: int = 0, dias_futuros: int = 2) -> list[dict]:
    """Retorna jogos do período [-dias_passados, +dias_futuros] ordenados por data_hora."""
    ws = get_worksheet("jogos")
    hoje = datetime.now(_TZ).date()
    inicio = hoje - timedelta(days=dias_passados)
    fim = hoje + timedelta(days=dias_futuros)

    jogos = []
    for r in ws.get_all_records():
        dt = _parse_data_hora(str(r.get("data_hora", "")))
        if dt and inicio <= dt.date() <= fim:
            jogos.append({**r, "_dt": dt})

    jogos.sort(key=lambda j: j["_dt"])
    return jogos
