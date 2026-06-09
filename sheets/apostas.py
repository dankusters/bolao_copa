from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

_TZ = ZoneInfo("America/Sao_Paulo")
from sheets.client import get_worksheet


def buscar_apostador(telefone: str) -> dict | None:
    ws = get_worksheet("apostadores")
    for r in ws.get_all_records():
        if str(r.get("telefone", "")).strip() == str(telefone).strip():
            return r
    return None


def verificar_e_marcar_primeiro_acesso(telefone: str) -> str | None:
    """Retorna o nome do apostador se é o primeiro acesso (e marca a data). Retorna None caso contrário ou se não for cadastrado."""
    ws = get_worksheet("apostadores")
    cabecalhos = ws.row_values(1)
    try:
        col_pa = cabecalhos.index("primeiro_acesso") + 1
    except ValueError:
        return None

    registros = ws.get_all_records()
    for idx, r in enumerate(registros):
        if str(r.get("telefone", "")).strip() == str(telefone).strip():
            if not str(r.get("primeiro_acesso", "")).strip():
                linha = idx + 2
                ws.update_cell(linha, col_pa, datetime.now(_TZ).strftime("%d/%m/%Y %H:%M"))
                return str(r.get("nome", "")).strip()
            return None
    return None


def nome_esta_cadastrado(nome: str) -> bool:
    ws = get_worksheet("apostadores")
    return any(
        str(r.get("nome", "")).strip().lower() == nome.strip().lower()
        for r in ws.get_all_records()
    )


def buscar_membros_familia(familia: str) -> list[str]:
    ws = get_worksheet("apostadores")
    return [
        r["nome"]
        for r in ws.get_all_records()
        if str(r.get("família", "")).strip() == familia.strip()
    ]


def _data_logica_hoje() -> date:
    """Antes das 02:00 AM pertencemos ainda ao dia anterior."""
    agora = datetime.now(_TZ)
    if agora.hour < 2:
        return (agora - timedelta(days=1)).date()
    return agora.date()


def _eh_jogo_do_dia(dt: datetime) -> bool:
    """Jogos até 02:00 AM do dia seguinte contam como do dia atual."""
    dia = _data_logica_hoje()
    amanha = dia + timedelta(days=1)
    return dt.date() == dia or (dt.date() == amanha and dt.hour < 2)


def tem_jogo_madrugada(jogos: list[dict]) -> bool:
    """Retorna True se algum jogo da lista é na madrugada do dia seguinte (< 02:00 AM)."""
    dia = _data_logica_hoje()
    amanha = dia + timedelta(days=1)
    for j in jogos:
        dt = _parse_data_hora(str(j.get("data_hora", "")))
        if dt and dt.date() == amanha and dt.hour < 2:
            return True
    return False


def buscar_jogos_hoje() -> list[dict]:
    ws = get_worksheet("jogos")
    jogos = []
    for r in ws.get_all_records():
        dt = _parse_data_hora(str(r.get("data_hora", "")))
        if dt and _eh_jogo_do_dia(dt):
            jogos.append(r)
    return jogos


def apostas_existentes(nome: str, ids_jogos: list) -> list[dict]:
    ws = get_worksheet("bet")
    try:
        registros = ws.get_all_records()
    except Exception:
        return []
    ids_str = {str(i) for i in ids_jogos}
    return [
        r for r in registros
        if str(r.get("nome", "")).strip().lower() == nome.strip().lower()
        and str(r.get("id_jogo", "")).strip() in ids_str
    ]


COL_FORMULA_INICIO = 11  # coluna K (origem em J não tem fórmula)
COL_FORMULA_FIM = 17    # coluna Q (inclusive)


def gravar_apostas(apostas: list[dict]):
    ws = get_worksheet("bet")
    cabecalhos = ws.row_values(1)

    todos_valores = ws.get_all_values()
    template_row = len(todos_valores)

    linhas = [[aposta.get(col, "") for col in cabecalhos] for aposta in apostas]
    ws.append_rows(linhas)

    if template_row > 1:
        _copiar_formulas(ws, template_row, template_row + 1, template_row + len(apostas))


def _copiar_formulas(ws, origem: int, destino_inicio: int, destino_fim: int):
    ws.spreadsheet.batch_update({
        "requests": [{
            "copyPaste": {
                "source": {
                    "sheetId": ws.id,
                    "startRowIndex": origem - 1,
                    "endRowIndex": origem,
                    "startColumnIndex": COL_FORMULA_INICIO - 1,
                    "endColumnIndex": COL_FORMULA_FIM,
                },
                "destination": {
                    "sheetId": ws.id,
                    "startRowIndex": destino_inicio - 1,
                    "endRowIndex": destino_fim,
                    "startColumnIndex": COL_FORMULA_INICIO - 1,
                    "endColumnIndex": COL_FORMULA_FIM,
                },
                "pasteType": "PASTE_FORMULA",
                "pasteOrientation": "NORMAL",
            }
        }]
    })


def _parse_data_hora(s: str) -> datetime | None:
    s = s.strip()
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None
