import random
from sheets.apostas import buscar_jogos_hoje, gravar_apostas
from sheets.client import get_worksheet

# Regras de probabilidade para geração automática de placares.
# Cada faixa recebe um peso relativo; o peso é distribuído igualmente
# entre os valores da faixa (ex: faixa (0,3) com peso 90 → cada gol
# 0,1,2,3 tem peso 22.5).
REGRAS_PLACAR = {
    "mandante": [
        {"faixa": (0, 3), "peso": 100},
    ],
    "visitante": [
        {"faixa": (0, 3), "peso": 100},
    ],
}


def _gerar_gols(regras_time: list[dict]) -> int:
    opcoes = []
    pesos = []
    for regra in regras_time:
        a, b = regra["faixa"]
        tamanho = b - a + 1
        for gol in range(a, b + 1):
            opcoes.append(gol)
            pesos.append(regra["peso"] / tamanho)
    return random.choices(opcoes, weights=pesos, k=1)[0]


def gerar_apostas_automaticas() -> int:
    """Gera apostas automáticas para todos os apostadores que ainda não
    apostaram nos jogos de hoje. Retorna o número de apostas inseridas."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    jogos_hoje = buscar_jogos_hoje()
    if not jogos_hoje:
        return 0

    ids_jogos = [str(j["id_jogo"]).strip() for j in jogos_hoje]
    ids_jogos_set = set(ids_jogos)
    apostadores = get_worksheet("apostadores").get_all_records()
    todos_bets = get_worksheet("bet").get_all_records()
    now_str = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")

    apostas_novas = []
    for apostador in apostadores:
        nome = str(apostador.get("nome", "")).strip()
        familia = str(apostador.get("família", "")).strip()
        if not nome:
            continue

        ids_com_aposta = {
            str(b["id_jogo"]).strip()
            for b in todos_bets
            if str(b.get("nome", "")).strip().lower() == nome.lower()
            and str(b.get("id_jogo", "")).strip() in ids_jogos_set
        }

        for jogo in jogos_hoje:
            id_jogo = str(jogo["id_jogo"]).strip()
            if id_jogo in ids_com_aposta:
                continue

            apostas_novas.append({
                "bet_date": now_str,
                "nome": nome,
                "família": familia,
                "id_jogo": id_jogo,  # já normalizado com .strip() acima
                "time_mandante": jogo.get("time_mandante", ""),
                "time_visitante": jogo.get("time_visitante", ""),
                "mandante_x_visitante": jogo.get("mandante_x_visitante", ""),
                "gols_mandante": _gerar_gols(REGRAS_PLACAR["mandante"]),
                "gols_visitante": _gerar_gols(REGRAS_PLACAR["visitante"]),
                "situacao": "",
                "isbetdone": "sim",
                "origem": "auto",
            })

    if apostas_novas:
        gravar_apostas(apostas_novas)

    return len(apostas_novas)
