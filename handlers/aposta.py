from datetime import datetime
from zoneinfo import ZoneInfo
from estado import get_estado, set_estado, limpar_estado
from whatsapp.sender import enviar_texto, enviar_template, enviar_cta
from utils.flags import bandeira
from sheets.apostas import (
    buscar_apostador,
    buscar_membros_familia,
    buscar_jogos_hoje,
    apostas_existentes,
    gravar_apostas,
    nome_esta_cadastrado,
    tem_jogo_madrugada,
)


def iniciar_aposta(numero: str):
    agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
    if agora.hour >= 12:
        enviar_texto(numero, "As apostas só são aceitas até as 12:00. O robô 🤖 fará as apostas de hoje por você!")
        enviar_cta(numero)
        return

    jogos_hoje = buscar_jogos_hoje()
    if not jogos_hoje:
        enviar_texto(numero, "Hoje não temos jogos da Copa! Aguarde! ⚽")
        enviar_cta(numero)
        return

    apostador = buscar_apostador(numero)
    if not apostador:
        enviar_texto(numero, "Você não é cadastrado, sorry! Tchau 👋")
        enviar_cta(numero)
        return

    nome = apostador["nome"]
    familia = str(apostador.get("família", "")).strip()
    membros = buscar_membros_familia(familia)
    outros = [m for m in membros if m.strip().lower() != nome.strip().lower()]

    count = len(jogos_hoje)
    plural = "jogo" if count == 1 else "jogos"
    data_hoje = agora.strftime("%d/%m")

    jogos_lista = [
        f"{bandeira(j['time_mandante'])} {j['time_mandante']} x {bandeira(j['time_visitante'])} {j['time_visitante']} às {_extrair_hora(str(j['data_hora']))}"
        for j in jogos_hoje
    ]
    jogos_lista[-1] += "."
    jogos_linhas = "\n".join(jogos_lista)

    aviso = (
        f" Lembre-se que você só pode fazer uma aposta para você ou para "
        f"{', '.join(outros)} da família {familia}."
        if outros else ""
    )

    aviso_madrugada = (
        "\n\n⚠️ Os jogos de madrugada do dia seguinte são considerados apostas de hoje."
        if tem_jogo_madrugada(jogos_hoje) else ""
    )

    set_estado(numero, "aguardando_nome", {
        "apostador_nome": nome,
        "apostador_familia": familia,
        "membros_familia": membros,
        "jogos_hoje": jogos_hoje,
        "jogo_atual_idx": 0,
        "apostas": [],
    })

    enviar_texto(
        numero,
        f"Olá, {nome}!\n\n"
        f"Hoje, {data_hoje}, teremos {count} {plural}:\n\n"
        f"{jogos_linhas}{aviso_madrugada}\n\n"
        f"Escreva o nome para quem você vai fazer a aposta. Se for você mesmo, coloque o seu nome.\n\n{aviso}",
    )


_ETAPAS = {"aguardando_nome", "aguardando_gols_mandante", "aguardando_gols_visitante", "aguardando_confirmacao"}


def handle_aposta(numero: str, texto: str) -> bool:
    estado = get_estado(numero)
    if not estado or estado["etapa"] not in _ETAPAS:
        return False

    etapa = estado["etapa"]
    dados = estado["dados"]
    texto = texto.strip()

    if etapa == "aguardando_nome":
        _handle_nome(numero, texto, dados)
    elif etapa == "aguardando_gols_mandante":
        _handle_gols_mandante(numero, texto, dados)
    elif etapa == "aguardando_gols_visitante":
        _handle_gols_visitante(numero, texto, dados)
    elif etapa == "aguardando_confirmacao":
        _handle_confirmacao(numero, texto, dados)

    return True


def _handle_nome(numero: str, nome_digitado: str, dados: dict):
    membros = dados["membros_familia"]
    match = next((m for m in membros if m.strip().lower() == nome_digitado.lower()), None)

    if not match:
        if nome_esta_cadastrado(nome_digitado):
            enviar_texto(numero, "Sorry, espertinho(a), você não pode apostar por esta pessoa. 😅")
        else:
            enviar_texto(numero, "Não encontrei ninguém cadastrado com esse nome. Tente novamente.")
        limpar_estado(numero)
        enviar_template(numero)
        return

    jogos_hoje = dados["jogos_hoje"]
    ids_jogos = [j["id_jogo"] for j in jogos_hoje]
    bets = apostas_existentes(match, ids_jogos)

    if bets:
        enviar_texto(numero, f"{match} já fez aposta hoje! Sorry! 😅")
        limpar_estado(numero)
        enviar_cta(numero)
        return

    dados["nome_para_aposta"] = match
    dados["jogos_hoje"] = jogos_hoje
    dados["jogo_atual_idx"] = 0
    dados["apostas"] = []
    set_estado(numero, "aguardando_gols_mandante", dados)
    _perguntar_gols_mandante(numero, dados)


def _perguntar_gols_mandante(numero: str, dados: dict):
    idx = dados["jogo_atual_idx"]
    total = len(dados["jogos_hoje"])
    jogo = dados["jogos_hoje"][idx]
    mandante = jogo["time_mandante"]
    visitante = jogo["time_visitante"]
    enviar_texto(
        numero,
        f"Jogo {idx + 1}/{total}: {bandeira(mandante)} {mandante} x {bandeira(visitante)} {visitante}\n"
        f"Quantos gols o {bandeira(mandante)} {mandante} irá marcar?",
    )


def _handle_gols_mandante(numero: str, texto: str, dados: dict):
    gols = _validar_gols(texto)
    if gols is None:
        enviar_texto(
            numero,
            "Escreva números inteiros! Texto ou qualquer número maior que 10 não são permitidos, comece de novo.",
        )
        _perguntar_gols_mandante(numero, dados)
        return

    dados["gols_mandante_temp"] = gols
    set_estado(numero, "aguardando_gols_visitante", dados)
    jogo = dados["jogos_hoje"][dados["jogo_atual_idx"]]
    visitante = jogo["time_visitante"]
    enviar_texto(numero, f"Quantos gols o {bandeira(visitante)} {visitante} irá marcar?")


def _handle_gols_visitante(numero: str, texto: str, dados: dict):
    gols = _validar_gols(texto)
    if gols is None:
        enviar_texto(
            numero,
            "Escreva números inteiros! Texto ou qualquer número maior que 10 não são permitidos, comece de novo.",
        )
        jogo = dados["jogos_hoje"][dados["jogo_atual_idx"]]
        visitante = jogo["time_visitante"]
        enviar_texto(numero, f"Quantos gols o {bandeira(visitante)} {visitante} irá marcar?")
        return

    jogo = dados["jogos_hoje"][dados["jogo_atual_idx"]]
    dados["apostas"].append({
        "id_jogo": jogo["id_jogo"],
        "time_mandante": jogo["time_mandante"],
        "time_visitante": jogo["time_visitante"],
        "mandante_x_visitante": jogo["mandante_x_visitante"],
        "gols_mandante": dados.pop("gols_mandante_temp"),
        "gols_visitante": gols,
    })

    idx = dados["jogo_atual_idx"]
    if idx + 1 < len(dados["jogos_hoje"]):
        dados["jogo_atual_idx"] = idx + 1
        set_estado(numero, "aguardando_gols_mandante", dados)
        _perguntar_gols_mandante(numero, dados)
    else:
        set_estado(numero, "aguardando_confirmacao", dados)
        _mostrar_resumo(numero, dados)


def _mostrar_resumo(numero: str, dados: dict):
    nome = dados["nome_para_aposta"]
    linhas = [f"*Resumo das apostas para {nome}:*\n"]
    for a in dados["apostas"]:
        linhas.append(f"• {a['mandante_x_visitante']}: {a['gols_mandante']} x {a['gols_visitante']}")
    linhas.append("\nDigite *sim* para confirmar ou qualquer outra coisa para recomeçar.")
    enviar_texto(numero, "\n".join(linhas))


def _handle_confirmacao(numero: str, texto: str, dados: dict):
    if texto.lower() == "sim":
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        nome = dados["nome_para_aposta"]
        rows = [
            {
                "bet_date": now_str,
                "nome": nome,
                "família": dados["apostador_familia"],
                "id_jogo": a["id_jogo"],
                "time_mandante": a["time_mandante"],
                "time_visitante": a["time_visitante"],
                "mandante_x_visitante": a["mandante_x_visitante"],
                "gols_mandante": a["gols_mandante"],
                "gols_visitante": a["gols_visitante"],
                "situacao": "",
                "isbetdone": "sim",
                "ponto_placar": "",
                "ponto_situacao": "",
                "pontos_totais": "",
            }
            for a in dados["apostas"]
        ]
        gravar_apostas(rows)
        limpar_estado(numero)
        enviar_texto(numero, f"Apostas de *{nome}* registradas com sucesso! Boa sorte! 🏆")
        enviar_cta(numero)
    else:
        limpar_estado(numero)
        enviar_texto(numero, "Vamos começar tudo de novo!")
        enviar_template(numero)


def _validar_gols(texto: str) -> int | None:
    try:
        n = int(texto)
        if 0 <= n <= 10:
            return n
    except ValueError:
        pass
    return None


def _extrair_hora(data_hora_str: str) -> str:
    s = data_hora_str.strip()
    try:
        return datetime.fromisoformat(s).strftime("%H:%M")
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).strftime("%H:%M")
        except ValueError:
            continue
    return data_hora_str
