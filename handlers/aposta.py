from datetime import datetime
from estado import get_estado, set_estado, limpar_estado
from whatsapp.sender import enviar_texto, enviar_template
from sheets.apostas import (
    buscar_apostador,
    buscar_membros_familia,
    buscar_jogos_hoje,
    apostas_existentes,
    gravar_apostas,
)


def iniciar_aposta(numero: str):
    agora = datetime.now()
    if agora.hour >= 23 and agora.minute >= 59:  # TODO: restaurar para hour >= 12 no deploy
        enviar_texto(numero, "Já passou das 12:00, não dá mais para apostar. Aguarde até amanhã!")
        return

    jogos_hoje = buscar_jogos_hoje()
    if not jogos_hoje:
        enviar_texto(numero, "Hoje não temos jogos da Copa! Aguarde! ⚽")
        return

    apostador = buscar_apostador(numero)
    if not apostador:
        enviar_texto(numero, "Você não é cadastrado, sorry! Tchau 👋")
        return

    nome = apostador["nome"]
    familia = str(apostador.get("família", "")).strip()
    membros = buscar_membros_familia(familia)
    outros = [m for m in membros if m.strip().lower() != nome.strip().lower()]

    count = len(jogos_hoje)
    plural = "jogo" if count == 1 else "jogos"
    jogos_str = "; ".join(
        f"{j['mandante_x_visitante']} às {_extrair_hora(str(j['data_hora']))}"
        for j in jogos_hoje
    )

    aviso = (
        f" Lembre-se que você só pode fazer uma aposta para você ou para "
        f"{', '.join(outros)} da família {familia}."
        if outros else ""
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
        f"Hoje teremos {count} {plural}: {jogos_str}.\n\n"
        f"Olá, {nome}! Escreva o nome para quem você vai fazer a aposta. "
        f"Se for você mesmo, coloque seu nome.{aviso}",
    )


def handle_aposta(numero: str, texto: str) -> bool:
    estado = get_estado(numero)
    if not estado:
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
        enviar_texto(numero, "Sorry, espertinho(a), você não pode apostar por esta pessoa. 😅")
        limpar_estado(numero)
        return

    jogos_hoje = dados["jogos_hoje"]
    ids_jogos = [j["id_jogo"] for j in jogos_hoje]
    bets = apostas_existentes(match, ids_jogos)

    if bets:
        enviar_texto(numero, f"{match} já fez aposta hoje! Sorry! 😅")
        limpar_estado(numero)
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
    enviar_texto(
        numero,
        f"Jogo {idx + 1}/{total}: {jogo['mandante_x_visitante']} "
        f"às {_extrair_hora(str(jogo['data_hora']))}\n"
        f"Quantos gols *{jogo['time_mandante']}* irá marcar?",
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
    enviar_texto(numero, f"Quantos gols *{jogo['time_visitante']}* irá marcar?")


def _handle_gols_visitante(numero: str, texto: str, dados: dict):
    gols = _validar_gols(texto)
    if gols is None:
        enviar_texto(
            numero,
            "Escreva números inteiros! Texto ou qualquer número maior que 10 não são permitidos, comece de novo.",
        )
        jogo = dados["jogos_hoje"][dados["jogo_atual_idx"]]
        enviar_texto(numero, f"Quantos gols *{jogo['time_visitante']}* irá marcar?")
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
    else:
        limpar_estado(numero)
        enviar_texto(numero, "Vamos começar tudo de novo!")
        enviar_template(numero, "Olá! Use o menu abaixo para interagir com o bolão. 👇")


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
