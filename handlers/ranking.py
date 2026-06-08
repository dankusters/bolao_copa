from whatsapp.sender import enviar_texto, enviar_cta
from sheets.ranking import buscar_ranking, buscar_ranking_familia
from sheets.apostas import _parse_data_hora
from utils.flags import bandeira


def _formatar_ultimo_jogo(jogo: dict) -> str:
    dt = _parse_data_hora(str(jogo.get("data_hora", "")))
    if dt:
        hora = dt.strftime("%Hh%M")
        data = dt.strftime("%d/%m/%y")
    else:
        hora = str(jogo.get("data_hora", ""))
        data = ""
    mandante = jogo.get("time_mandante", "")
    visitante = jogo.get("time_visitante", "")
    nome_jogo = f"{bandeira(mandante)} {mandante} x {bandeira(visitante)} {visitante}".strip()
    sufixo = f" do dia {data}" if data else ""
    return f"Último jogo atualizado: {nome_jogo} das {hora}{sufixo}. Aguarde novas atualizações"


def handle_ranking_familia(numero: str):
    ranking, ultima_atualizacao = buscar_ranking_familia()

    if ultima_atualizacao:
        cabecalho = _formatar_ultimo_jogo(ultima_atualizacao) + "\n"
    else:
        cabecalho = "Nenhum jogo encerrado ainda.\n"

    linhas = [cabecalho, "*Ranking por Família:*\n"]
    for i, r in enumerate(ranking, 1):
        linhas.append(f"{i}. {r['nome']} - {_formatar_linha(r)}")

    enviar_texto(numero, "\n".join(linhas))
    enviar_cta(numero)


def handle_ranking(numero: str):
    ranking, ultima_atualizacao = buscar_ranking()

    if ultima_atualizacao:
        cabecalho = _formatar_ultimo_jogo(ultima_atualizacao) + "\n"
    else:
        cabecalho = "Nenhum jogo encerrado ainda.\n"

    linhas = [cabecalho, "*Ranking do Bolão 🏆:*\n"]
    for i, r in enumerate(ranking, 1):
        pontos = r["pontos"]
        mosca = r["placar_mosca"]
        resultado = r["resultado"]
        pontos_str = str(int(pontos)) if pontos == int(pontos) else str(pontos)
        plural_pts = "ponto" if pontos == 1 else "pontos"
        linhas.append(f"*{i}. {r['nome']} - {pontos_str} {plural_pts}*")
        partes = []
        if mosca > 0:
            partes.append(f"{mosca} {'placar na mosca' if mosca == 1 else 'placares na mosca'}")
        if resultado > 0:
            partes.append(f"{resultado} {'situação' if resultado == 1 else 'situações'}")
        if partes:
            linhas.append(f"- acertou {' e '.join(partes)}")
        linhas.append("")

    enviar_texto(numero, "\n".join(linhas))
    enviar_cta(numero)


def _formatar_linha(r: dict) -> str:
    pontos = r["pontos"]
    mosca = r["placar_mosca"]
    resultado = r["resultado"]
    pontos_str = str(int(pontos)) if pontos == int(pontos) else str(pontos)
    plural_pts = "ponto" if pontos == 1 else "pontos"

    if mosca == 0 and resultado == 0:
        return f"total {pontos_str} {plural_pts}"

    partes = []
    if mosca > 0:
        partes.append(f"{mosca} {'placar na mosca' if mosca == 1 else 'placares na mosca'}")
    if resultado > 0:
        partes.append(f"{resultado} {'situação' if resultado == 1 else 'situações'}")

    return f"total {pontos_str} {plural_pts} (acertou {' e '.join(partes)})"
