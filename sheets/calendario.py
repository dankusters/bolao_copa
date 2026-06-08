from datetime import date, timedelta
from sheets.client import get_worksheet
from sheets.apostas import _parse_data_hora


def buscar_calendario(dias_passados: int = 3, dias_futuros: int = 7) -> list[dict]:
    """Retorna jogos do período [-dias_passados, +dias_futuros] ordenados por data_hora."""
    ws = get_worksheet("jogos")
    hoje = date.today()
    inicio = hoje - timedelta(days=dias_passados)
    fim = hoje + timedelta(days=dias_futuros)

    jogos = []
    for r in ws.get_all_records():
        dt = _parse_data_hora(str(r.get("data_hora", "")))
        if dt and inicio <= dt.date() <= fim:
            jogos.append({**r, "_dt": dt})

    jogos.sort(key=lambda j: j["_dt"])
    return jogos
