"""
Verifica a aba 'lembretes' da planilha e envia mensagens agendadas.
Deve ser executado a cada minuto via cron:
  * * * * * cd /home/deploy/bolao_copa && ~/.local/bin/uv run python scripts/enviar_lembretes.py >> /home/deploy/bolao_lembretes.log 2>&1

Campos da aba 'lembretes':
  data_hora    — data/hora do disparo (formato: DD/MM/YYYY HH:MM)
  mensagem     — texto a enviar
  destinatario — "todos", "familia:NomeFamilia" ou "sem_aposta"
  enviado      — marcado com "sim" após o envio
"""
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sheets.client import get_worksheet
from sheets.apostas import _parse_data_hora, buscar_jogos_hoje
from whatsapp.sender import enviar_texto

_TZ = ZoneInfo("America/Sao_Paulo")


def _get_destinatarios(regra: str) -> list[str]:
    """Retorna lista de telefones com base na regra de destinatário."""
    ws_ap = get_worksheet("apostadores")
    apostadores = ws_ap.get_all_records()

    regra = regra.strip().lower()

    if regra == "todos":
        return [
            str(r["telefone"]).strip()
            for r in apostadores
            if str(r.get("telefone", "")).strip()
        ]

    if regra.startswith("familia:"):
        familia_alvo = regra.split(":", 1)[1].strip()
        return [
            str(r["telefone"]).strip()
            for r in apostadores
            if str(r.get("família", "")).strip().lower() == familia_alvo.lower()
            and str(r.get("telefone", "")).strip()
        ]

    if regra == "sem_aposta":
        jogos_hoje = buscar_jogos_hoje()
        if not jogos_hoje:
            return []
        ids_jogos = [str(j["id_jogo"]) for j in jogos_hoje]
        ids_jogos_set = set(ids_jogos)

        ws_bet = get_worksheet("bet")
        todos_bets = ws_bet.get_all_records()
        nomes_com_aposta = {
            str(b.get("nome", "")).strip().lower()
            for b in todos_bets
            if str(b.get("id_jogo", "")).strip() in ids_jogos_set
        }

        return [
            str(r["telefone"]).strip()
            for r in apostadores
            if str(r.get("telefone", "")).strip()
            and str(r.get("nome", "")).strip().lower() not in nomes_com_aposta
        ]

    print(f"[WARN] Regra de destinatário não reconhecida: '{regra}'")
    return []


def enviar_lembretes():
    agora = datetime.now(_TZ)
    print(f"[{agora.strftime('%Y-%m-%d %H:%M')}] Verificando lembretes...")

    ws = get_worksheet("lembretes")
    cabecalhos = ws.row_values(1)

    try:
        col_enviado = cabecalhos.index("enviado") + 1
    except ValueError:
        print("[ERRO] Coluna 'enviado' não encontrada na aba 'lembretes'.")
        return

    registros = ws.get_all_records()
    enviados = 0

    for idx, r in enumerate(registros):
        if str(r.get("enviado", "")).strip().lower() == "sim":
            continue

        data_hora_str = str(r.get("data_hora", "")).strip()
        dt = _parse_data_hora(data_hora_str)
        if not dt:
            print(f"[SKIP] Linha {idx + 2}: data_hora inválida '{data_hora_str}'.")
            continue

        # Torna dt timezone-aware em Brasília se necessário
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_TZ)

        if dt > agora:
            continue

        mensagem = str(r.get("mensagem", "")).strip()
        if not mensagem:
            print(f"[SKIP] Linha {idx + 2}: mensagem vazia.")
            continue

        destinatario = str(r.get("destinatario", "")).strip()
        telefones = _get_destinatarios(destinatario)

        if not telefones:
            print(f"[SKIP] Linha {idx + 2}: nenhum destinatário encontrado para '{destinatario}'.")
            ws.update_cell(idx + 2, col_enviado, "sim")
            continue

        print(f"[INFO] Enviando lembrete '{data_hora_str}' para {len(telefones)} destinatário(s)...")
        for tel in telefones:
            try:
                enviar_texto(tel, mensagem)
            except Exception as e:
                print(f"[ERRO] Falha ao enviar para {tel}: {e}")

        ws.update_cell(idx + 2, col_enviado, "sim")
        enviados += 1
        print(f"[OK] Lembrete da linha {idx + 2} enviado e marcado.")

    if enviados == 0:
        print("[INFO] Nenhum lembrete pendente.")


if __name__ == "__main__":
    enviar_lembretes()
