from whatsapp.sender import enviar_texto
from sheets.ranking import buscar_ranking, buscar_ranking_familia
from sheets.apostas import _parse_data_hora


def _formatar_ultimo_jogo(jogo: dict) -> str:
    dt = _parse_data_hora(str(jogo.get("data_hora", "")))
    if dt:
        hora = dt.strftime("%Hh%M")
        data = dt.strftime("%d/%m/%y")
    else:
        hora = str(jogo.get("data_hora", ""))
        data = ""
    nome_jogo = jogo.get("mandante_x_visitante", "")
    sufixo = f" do dia {data}" if data else ""
    return f"Último jogo atualizado: {nome_jogo} das {hora}{sufixo}. Aguarde atualizações"


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


def handle_ranking(numero: str):
    ranking, ultima_atualizacao = buscar_ranking()

    if ultima_atualizacao:
        cabecalho = _formatar_ultimo_jogo(ultima_atualizacao) + "\n"
    else:
        cabecalho = "Nenhum jogo encerrado ainda.\n"

    linhas = [cabecalho, "*Ranking do Bolão:*\n"]
    for i, r in enumerate(ranking, 1):
        linhas.append(f"{i}. {r['nome']} - {_formatar_linha(r)}")

    enviar_texto(numero, "\n".join(linhas))


def _formatar_linha(r: dict) -> str:
    pontos = r["pontos"]
    mosca = r["placar_mosca"]
    resultado = r["resultado"]
    plural_pts = "ponto" if pontos == 1 else "pontos"

    if mosca == 0 and resultado == 0:
        return f"total {pontos} {plural_pts}"

    partes = []
    if mosca > 0:
        partes.append(f"{mosca} {'placar na mosca' if mosca == 1 else 'placares na mosca'}")
    if resultado > 0:
        partes.append(f"{resultado} {'resultado' if resultado == 1 else 'resultados'}")

    return f"total {pontos} {plural_pts} (acertou {' e '.join(partes)})"
