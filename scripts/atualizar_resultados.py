"""
Busca resultados finalizados da Copa do Mundo na API football-data.org
e atualiza gols_mandante / gols_visitante na aba 'jogos' do Google Sheets.

Requer FOOTBALL_DATA_TOKEN no .env.

Cron recomendado (a cada 5 min, das 12h às 23h Brasília = 15h-02h UTC):
  */5 15-23,0-2 * * * cd /home/deploy/bolao_copa && uv run python scripts/atualizar_resultados.py >> /home/deploy/bolao_resultados.log 2>&1
"""
import sys
import os
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from dotenv import load_dotenv

load_dotenv(override=True)

from sheets.client import get_worksheet
from sheets.apostas import _parse_data_hora

FOOTBALL_DATA_TOKEN = os.getenv("FOOTBALL_DATA_TOKEN", "")
API_BASE = "https://api.football-data.org/v4"
COMPETITION = "WC"

# Nomes da API (inglês) → nomes na planilha (português)
NOMES_TIMES: dict[str, str] = {
    # América do Sul
    "Brazil": "Brasil",
    "Argentina": "Argentina",
    "Uruguay": "Uruguai",
    "Colombia": "Colômbia",
    "Chile": "Chile",
    "Ecuador": "Equador",
    "Peru": "Peru",
    "Paraguay": "Paraguai",
    "Venezuela": "Venezuela",
    "Bolivia": "Bolívia",
    # América do Norte e Central
    "Mexico": "México",
    "United States": "Estados Unidos",
    "Canada": "Canadá",
    "Costa Rica": "Costa Rica",
    "Honduras": "Honduras",
    "Panama": "Panamá",
    "Jamaica": "Jamaica",
    "El Salvador": "El Salvador",
    "Guatemala": "Guatemala",
    "Cuba": "Cuba",
    "Trinidad and Tobago": "Trinidad e Tobago",
    # Europa
    "France": "França",
    "Germany": "Alemanha",
    "Spain": "Espanha",
    "England": "Inglaterra",
    "Portugal": "Portugal",
    "Italy": "Itália",
    "Netherlands": "Holanda",
    "Belgium": "Bélgica",
    "Croatia": "Croácia",
    "Serbia": "Sérvia",
    "Switzerland": "Suíça",
    "Denmark": "Dinamarca",
    "Poland": "Polônia",
    "Ukraine": "Ucrânia",
    "Turkey": "Turquia",
    "Austria": "Áustria",
    "Sweden": "Suécia",
    "Norway": "Noruega",
    "Scotland": "Escócia",
    "Wales": "País de Gales",
    "Greece": "Grécia",
    "Czech Republic": "República Tcheca",
    "Czechia": "República Tcheca",
    "Slovakia": "Eslováquia",
    "Hungary": "Hungria",
    "Romania": "Romênia",
    "Slovenia": "Eslovênia",
    "Albania": "Albânia",
    "Georgia": "Geórgia",
    "Bosnia and Herzegovina": "Bósnia e Herzegovina",
    # África
    "Morocco": "Marrocos",
    "Senegal": "Senegal",
    "Nigeria": "Nigéria",
    "Cameroon": "Camarões",
    "Ivory Coast": "Costa do Marfim",
    "Côte d'Ivoire": "Costa do Marfim",
    "Ghana": "Gana",
    "Egypt": "Egito",
    "Algeria": "Argélia",
    "Tunisia": "Tunísia",
    "Mali": "Mali",
    "South Africa": "África do Sul",
    "Angola": "Angola",
    "Ethiopia": "Etiópia",
    "Tanzania": "Tanzania",
    "DR Congo": "República Democrática do Congo",
    # Ásia
    "Japan": "Japão",
    "South Korea": "Coreia do Sul",
    "Korea Republic": "Coreia do Sul",
    "IR Iran": "Irã",
    "Iran": "Irã",
    "Saudi Arabia": "Arábia Saudita",
    "Australia": "Austrália",
    "Qatar": "Catar",
    "China PR": "China",
    "China": "China",
    "India": "Índia",
    "Iraq": "Iraque",
    "Jordan": "Jordânia",
    "Uzbekistan": "Uzbequistão",
    # Oceania
    "New Zealand": "Nova Zelândia",
    "Fiji": "Fiji",
}


def _traduzir(nome_api: str) -> str:
    return NOMES_TIMES.get(nome_api, nome_api)


def buscar_jogos_finalizados_hoje() -> list[dict]:
    hoje = date.today().isoformat()
    url = f"{API_BASE}/competitions/{COMPETITION}/matches"
    headers = {"X-Auth-Token": FOOTBALL_DATA_TOKEN}
    params = {"dateFrom": hoje, "dateTo": hoje, "status": "FINISHED"}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
    except requests.RequestException as e:
        print(f"[ERRO] Falha na requisição: {e}")
        return []

    if resp.status_code == 401:
        print("[ERRO] Token inválido ou expirado (401).")
        return []
    if resp.status_code == 429:
        print("[ERRO] Quota da API excedida (429). Tente novamente em breve.")
        return []
    if resp.status_code != 200:
        print(f"[ERRO] API retornou {resp.status_code}: {resp.text[:300]}")
        return []

    return resp.json().get("matches", [])


def atualizar_resultados():
    agora = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"[{agora}] Verificando resultados...")

    if not FOOTBALL_DATA_TOKEN:
        print("[ERRO] FOOTBALL_DATA_TOKEN não definido no .env.")
        sys.exit(1)

    jogos_api = buscar_jogos_finalizados_hoje()
    if not jogos_api:
        print("[INFO] Nenhum jogo finalizado hoje.")
        return

    ws = get_worksheet("jogos")
    cabecalhos = ws.row_values(1)
    registros = ws.get_all_records()

    try:
        col_gm = cabecalhos.index("gols_mandante") + 1
        col_gv = cabecalhos.index("gols_visitante") + 1
        col_pm = cabecalhos.index("penaltis_mandante") + 1
        col_pv = cabecalhos.index("penaltis_visitante") + 1
    except ValueError as e:
        print(f"[ERRO] Coluna não encontrada na aba 'jogos': {e}")
        return

    hoje = date.today()
    atualizados = 0

    for jogo_api in jogos_api:
        mandante_pt = _traduzir(jogo_api["homeTeam"]["name"])
        visitante_pt = _traduzir(jogo_api["awayTeam"]["name"])
        gm = jogo_api["score"]["fullTime"]["home"]
        gv = jogo_api["score"]["fullTime"]["away"]
        pm = jogo_api["score"]["penalties"]["home"]
        pv = jogo_api["score"]["penalties"]["away"]

        if gm is None or gv is None:
            print(f"[SKIP] {mandante_pt} x {visitante_pt}: placar final não disponível ainda.")
            continue

        encontrado = False
        for idx, row in enumerate(registros):
            dt = _parse_data_hora(str(row.get("data_hora", "")))
            if not dt or dt.date() != hoje:
                continue
            if (row["time_mandante"].strip() == mandante_pt and
                    row["time_visitante"].strip() == visitante_pt):
                encontrado = True
                ja_tem_gols = (str(row.get("gols_mandante", "")).strip() == str(gm) and
                               str(row.get("gols_visitante", "")).strip() == str(gv))
                ja_tem_pen = (str(row.get("penaltis_mandante", "")).strip() == (str(pm) if pm is not None else "") and
                              str(row.get("penaltis_visitante", "")).strip() == (str(pv) if pv is not None else ""))
                if ja_tem_gols and ja_tem_pen:
                    print(f"[SKIP] {mandante_pt} {gm} x {gv} {visitante_pt} já atualizado.")
                    break
                linha = idx + 2  # +1 cabeçalho, +1 índice base-1
                ws.update_cell(linha, col_gm, gm)
                ws.update_cell(linha, col_gv, gv)
                if pm is not None and pv is not None:
                    ws.update_cell(linha, col_pm, pm)
                    ws.update_cell(linha, col_pv, pv)
                    print(f"[OK] {mandante_pt} {gm} x {gv} {visitante_pt} (pen: {pm} x {pv}) atualizado.")
                else:
                    print(f"[OK] {mandante_pt} {gm} x {gv} {visitante_pt} atualizado.")
                atualizados += 1
                break

        if not encontrado:
            print(f"[MISS] '{mandante_pt}' x '{visitante_pt}' não encontrado na planilha. Verifique o mapeamento de nomes.")

    print(f"[DONE] {atualizados} jogo(s) atualizado(s).")


if __name__ == "__main__":
    atualizar_resultados()
