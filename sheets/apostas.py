from datetime import datetime, date
from sheets.client import get_worksheet


def buscar_apostador(telefone: str) -> dict | None:
    ws = get_worksheet("apostadores")
    for r in ws.get_all_records():
        if str(r.get("telefone", "")).strip() == str(telefone).strip():
            return r
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


def buscar_jogos_hoje() -> list[dict]:
    ws = get_worksheet("jogos")
    hoje = date.today()
    jogos = []
    for r in ws.get_all_records():
        dt = _parse_data_hora(str(r.get("data_hora", "")))
        if dt and dt.date() == hoje:
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
