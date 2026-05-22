import unicodedata
from estado import get_estado, set_estado, limpar_estado
from whatsapp.sender import enviar_texto
from utils.flags import bandeira
from sheets.detalhe_apostador import buscar_nomes_apostadores, buscar_extrato_apostador

ETAPA = "aguardando_nome_apostador"


def iniciar_detalhe_apostador(numero: str):
    set_estado(numero, ETAPA, {})
    enviar_texto(numero, "Aqui você pode consultar as últimas apostas e os acertos de qualquer apostador. Escreva o nome de quem deseja ver os resultados:")


def handle_detalhe_apostador(numero: str, texto: str) -> bool:
    estado = get_estado(numero)
    if not estado or estado["etapa"] != ETAPA:
        return False

    nomes = buscar_nomes_apostadores()
    match = next((n for n in nomes if _normalizar(n) == _normalizar(texto)), None)
    limpar_estado(numero)

    if not match:
        enviar_texto(numero, "Esse nome não foi encontrado. Tente novamente clicando no botão.")
        return True

    extrato = buscar_extrato_apostador(match)

    if not extrato:
        enviar_texto(numero, f"{match} ainda não tem apostas em jogos atualizados.")
        return True

    total = sum(_to_int(item["bet"].get("pontos_totais", 0)) for item in extrato)
    exibir = extrato[-10:]

    linhas = [f"*Apostas de {match}:*"]
    if len(extrato) > 10:
        linhas.append(f"_(exibindo as últimas {len(exibir)} de {len(extrato)} apostas)_")

    for item in exibir:
        b = item["bet"]
        j = item["jogo"]
        mandante = j["time_mandante"]
        visitante = j["time_visitante"]
        pts = _to_int(b.get("pontos_totais", 0))
        plural_pts = "ponto" if pts == 1 else "pontos"
        placar_txt = "acertou placar" if _to_int(b.get("ponto_placar", 0)) > 0 else "errou placar"
        situacao_txt = "acertou situação" if _to_int(b.get("ponto_situacao", 0)) > 0 else "errou situação"
        nome_m = f"{bandeira(mandante)} {mandante}".strip()
        nome_v = f"{bandeira(visitante)} {visitante}".strip()
        linhas.append(f"\n{nome_m} {j['gols_mandante']} x {nome_v} {j['gols_visitante']}")
        linhas.append(f"fez {pts} {plural_pts}, {placar_txt} e {situacao_txt}")

    linhas.append(f"\nTotal de pontos até última atualização: {total}")
    enviar_texto(numero, "\n".join(linhas))
    return True


def _normalizar(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s.lower().strip())
        if unicodedata.category(c) != "Mn"
    )


def _to_int(val) -> int:
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0
