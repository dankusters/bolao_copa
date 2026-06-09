"""
Gera apostas automáticas para apostadores que não apostaram até o horário de corte.
Deve ser executado via cron após o horário de corte definido abaixo.

Exemplo de cron (todo dia ao meio-dia, horário de Brasília UTC-3):
  0 15 * * * cd /home/deploy/bolao_copa && uv run python scripts/apostas_automaticas.py >> /var/log/bolao_apostas.log 2>&1
"""
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sheets.aposta_automatica import gerar_apostas_automaticas

HORARIO_CORTE = 12  # hora Brasília a partir da qual apostas automáticas são geradas

agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
print(f"[{agora.strftime('%Y-%m-%d %H:%M')}] Verificando apostas automáticas...")

if agora.hour < HORARIO_CORTE:
    print(f"Antes das {HORARIO_CORTE}:00 — nada a fazer.")
    sys.exit(0)

total = gerar_apostas_automaticas()
if total:
    print(f"{total} aposta(s) automática(s) gerada(s).")
else:
    print("Nenhuma aposta faltante encontrada.")
