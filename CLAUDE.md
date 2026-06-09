# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projeto

Bot de bolão da Copa do Mundo via WhatsApp, usando Meta Cloud API + Flask + Google Sheets. Em ambiente de desenvolvimento local, o ngrok expõe o servidor Flask para a internet, permitindo que a Meta entregue eventos de webhook.

## Comandos

```bash
# Instalar dependências
uv sync

# Rodar o servidor Flask (desenvolvimento local)
uv run python app.py

# Verificar planilha Google Sheets
uv run python sheets/teste_gsheets.py

# Listar templates WhatsApp disponíveis
uv run python check_templates.py

# Gerar apostas automáticas manualmente (sem trava de horário)
uv run python -c "from sheets.aposta_automatica import gerar_apostas_automaticas; print(gerar_apostas_automaticas())"

# Ver logs da VPS
ssh -i ~/.ssh/bolao_deploy deploy@2.25.131.88 "journalctl -u bolao --no-pager -n 50"
ssh -i ~/.ssh/bolao_deploy deploy@2.25.131.88 "tail -20 /home/deploy/bolao_apostas.log"
ssh -i ~/.ssh/bolao_deploy deploy@2.25.131.88 "tail -20 /home/deploy/bolao_resultados.log"

# Testar atualização de resultados manualmente
uv run python scripts/atualizar_resultados.py
```

## Arquitetura

O fluxo de uma mensagem recebida é:

```
Meta → POST /webhook → thread background → processar_webhook() → handler por tipo → sender
```

**`app.py`** recebe o POST da Meta, dispara `processar_webhook()` em uma **background thread** e retorna `200` imediatamente. Isso evita que a Meta reenvie o webhook por timeout (>20s) em operações pesadas como geração de apostas automáticas.

**`whatsapp/webhook.py`** recebe o payload da Meta, extrai o tipo da mensagem (`text`, `button`, etc.) e delega para o handler correspondente. Não contém lógica de negócio.

**`handlers/texto.py`** e **`handlers/botao.py`** contêm toda a lógica condicional do bot — é aqui que crescerá a maior parte do código conforme novos fluxos forem adicionados. `handlers/texto.py` verifica primeiro acesso (coluna `primeiro_acesso` na aba `apostadores`) e envia as regras do bolão na primeira interação.

**`handlers/regras.py`** centraliza o texto das regras do bolão (constante `REGRAS`) e o handler `handle_regras()`. Importado por `handlers/texto.py` (primeiro acesso) e `handlers/botao.py` (botão "Regras").

**`whatsapp/sender.py`** centraliza os envios:
- `enviar_template(numero, texto)` — envia o template `main_bolao` (com imagem no header e texto no body)
- `enviar_texto(numero, texto)` — envia mensagem de texto livre (só válida dentro da janela de 24h após o usuário interagir)
- `enviar_cta(numero)` — envia mensagem padrão de call-to-action ("Digite qualquer texto para voltar ao menu inicial"). Deve ser chamada ao final de todo handler que encerra o fluxo sem enviar o template.

**`estado.py`** mantém `aguardando_resposta: set[str]` em memória — o conjunto de números de telefone que aguardam a próxima mensagem do usuário para uma resposta contextual. **Este estado é perdido ao reiniciar o servidor.**

**`sheets/client.py`** expõe `get_worksheet(nome)` para acessar abas da planilha `tabela_copa`. Abas disponíveis: `jogos`, `bet`, `apostadores`. O ID da planilha está hardcoded na constante `FOLDER_ID`.

**`sheets/apostas.py`** contém helpers críticos de tempo:
- `_data_logica_hoje()` — retorna a data lógica do dia. Antes das 02:00 AM (Brasília), pertencemos ainda ao dia anterior.
- `_eh_jogo_do_dia(dt)` — retorna True para jogos na data lógica de hoje OU na madrugada do dia seguinte (< 02:00 AM). **Todos os checks de "jogos do dia" usam este helper.**
- `tem_jogo_madrugada(jogos)` — True se algum jogo da lista é na madrugada do dia seguinte.
- `verificar_e_marcar_primeiro_acesso(telefone)` — retorna o nome do apostador se é o primeiro acesso (e grava a data na coluna `primeiro_acesso`), None caso contrário.
- **Todos os checks de horário usam `ZoneInfo("America/Sao_Paulo")` explicitamente** — o servidor VPS roda em UTC.

**`sheets/aposta_automatica.py`** gera apostas aleatórias para apostadores que não apostaram até as 12:00 PM. A função `gerar_apostas_automaticas()` é idempotente — carrega a aba `bet` **uma única vez** e filtra em memória para evitar quota 429 do Google Sheets. Máximo de 3 gols por time. Apostas automáticas são marcadas com `origem = "auto"` na aba `bet`.

**`scripts/apostas_automaticas.py`** script standalone chamado pelo cron no VPS às 15:00 UTC (12:00 PM Brasília). Também é chamado inline pelo handler `apostas_dia` ao primeiro acesso após as 12:00 PM, eliminando condição de corrida com o cron.

**`scripts/atualizar_resultados.py`** script standalone que consulta a API `football-data.org` (competição `WC`) e atualiza `gols_mandante`/`gols_visitante`/`penaltis_mandante`/`penaltis_visitante` na aba `jogos` para jogos finalizados no dia. Requer `FOOTBALL_DATA_TOKEN` no `.env`. As colunas de pênaltis só são gravadas quando o jogo foi a pênaltis (`score.penalties` não nulo na API). O dicionário `NOMES_TIMES` dentro do script mapeia nomes em inglês (API) para português (planilha) — se aparecer `[MISS]` nos logs, adicionar a entrada faltante lá.

**`handlers/calendario.py`** + **`sheets/calendario.py`** exibem jogos de hoje e dos próximos **5 dias** com horário ou placar (se já encerrado), acionados pelo botão "Ver calendário de jogos e resultados".

**`handlers/apostas_dia.py`** exibe apostas do dia (após 12:00 PM Brasília). Chama `gerar_apostas_automaticas()` antes de exibir — idempotente, garante que apostas faltantes sejam criadas mesmo se o cron falhar. Exibe aviso de madrugada quando aplicável.

**`handlers/aposta.py`** gerencia o fluxo de apostas manuais. Trava às 12:00 PM (Brasília) — apostas não são aceitas após este horário.

**`handlers/detalhe_apostador.py`** exibe as últimas 10 apostas de um apostador com total de pontos no bolão, total de placares acertados e total de situações acertadas (calculados sobre o histórico completo).

**`handlers/detalhe_jogo.py`** + **`sheets/detalhe_jogo.py`** exibem os **últimos 6 jogos atualizados** (sem filtro de dia) com todas as apostas e pontuações.

**`handlers/ranking.py`** + **`sheets/ranking.py`** exibem ranking geral e por família. Em ambos os rankings: desempate por placares na mosca; em caso de empate em pontos **e** placares, os nomes/famílias aparecem na mesma posição.

**`handlers/aposta.py`** verifica existência de jogos do dia **antes** da trava de 12:00 PM — assim, dias sem jogos exibem mensagem correta independente do horário.

## Variáveis de ambiente (`.env`)

```
ACCESS_TOKEN=           # Token temporário da Meta (expira em 24h — renovar no painel da Meta)
PHONE_NUMBER_ID=        # ID do número de telefone no painel da Meta
VERIFY_TOKEN=           # String livre usada para validar o webhook na Meta
RECIPIENT_NUMBER=       # Número de teste (formato: 5511999999999)
FOOTBALL_DATA_TOKEN=    # Token da API football-data.org (gratuito, não expira)
```

## Planilha Google Sheets — estrutura

### Aba `apostadores`
Colunas relevantes: `nome`, `telefone`, `família`, `primeiro_acesso`.
- `primeiro_acesso`: preenchido automaticamente com data/hora (Brasília) na primeira interação via WhatsApp. Deve existir na planilha para o recurso de boas-vindas funcionar.

### Aba `jogos`
Colunas relevantes: `id_jogo`, `data_hora`, `time_mandante`, `time_visitante`, `mandante_x_visitante`, `gols_mandante`, `gols_visitante`, `penaltis_mandante`, `penaltis_visitante`.
- `penaltis_mandante`/`penaltis_visitante`: preenchidos pelo script de atualização de resultados apenas quando o jogo foi a pênaltis.

### Aba `bet`
Colunas relevantes: `bet_date`, `nome`, `família`, `id_jogo`, `time_mandante`, `time_visitante`, `mandante_x_visitante`, `gols_mandante`, `gols_visitante`, `situacao`, `isbetdone`, `ponto_placar`, `ponto_situacao`, `pontos_totais`, `origem`.
- `COL_FORMULA_INICIO` em `sheets/apostas.py` deve apontar para a primeira coluna com fórmula. Atualmente é 11 (coluna K = `situacao`). Se adicionar/remover colunas antes dessa posição, atualizar a constante.

## Credenciais Google Sheets

O arquivo de credenciais (conta de serviço) deve estar dentro da pasta `sheets/`. Não é versionado. O nome exato do arquivo está definido em `sheets/client.py` na constante `CREDENTIALS_FILE` — atualizar quando gerar uma nova chave.

Para obter: Google Cloud Console → projeto `bolaodacopa-496702` → IAM e administrador → Contas de serviço → Chaves → Adicionar chave → JSON. Após baixar, copiar para `sheets/` e atualizar `CREDENTIALS_FILE` em `client.py`. Copiar também para a VPS via `scp` (ver seção abaixo).

## Deploy (VPS Hostinger)

O servidor de produção é um VPS na Hostinger:
- **IP:** `2.25.131.88`
- **Domínio:** `https://bolaodoscamargos.shop`
- **Usuário deploy:** `deploy` em `/home/deploy/bolao_copa`
- **Webhook Meta:** `https://bolaodoscamargos.shop/webhook`

### Stack de produção
- **gunicorn** serve o Flask app (2 workers, porta 5000)
- **nginx** faz reverse proxy para o gunicorn
- **systemd** mantém o serviço `bolao` sempre ativo (`sudo systemctl restart bolao`)
- **Let's Encrypt** gerencia o SSL (renovação automática via certbot)

### Deploy automático
Qualquer push na branch `main` dispara o workflow `.github/workflows/deploy.yml` via GitHub Actions, que:
1. SSH no VPS como `deploy`
2. `git pull origin main`
3. `uv sync --frozen`
4. `sudo systemctl restart bolao`

O GitHub Actions ocasionalmente falha por timeout de SSH — neste caso, rodar o deploy manualmente via SSH resolve.

### Arquivos sensíveis no VPS (não versionados)
Estes arquivos existem apenas no VPS e nas máquinas locais — nunca no git:
- `/home/deploy/bolao_copa/.env`
- `/home/deploy/bolao_copa/sheets/bolaodacopa-496702-*.json` (credenciais Google)

Para copiar da máquina local para o VPS:
```bash
scp -i ~/.ssh/bolao_deploy .env deploy@2.25.131.88:/home/deploy/bolao_copa/.env
scp -i ~/.ssh/bolao_deploy sheets/bolaodacopa-496702-*.json deploy@2.25.131.88:/home/deploy/bolao_copa/sheets/
```

### SSH — múltiplas máquinas de desenvolvimento
O `authorized_keys` da VPS aceita múltiplas chaves (uma por linha). Cada máquina de desenvolvimento pode ter sua própria chave `~/.ssh/bolao_deploy` adicionada via painel da Hostinger (hpanel.hostinger.com → VPS → Terminal).

O secret `VPS_SSH_KEY` no GitHub (usado pelo CI/CD) é independente das chaves locais — não alterar ao adicionar nova máquina.

### Cron no VPS
Crontab do usuário `deploy` (ver/editar com `crontab -e` na VPS):
```
# Apostas automáticas — 15:00 UTC = 12:00 PM Brasília
0 15 * * * cd /home/deploy/bolao_copa && ~/.local/bin/uv run python scripts/apostas_automaticas.py >> /home/deploy/bolao_apostas.log 2>&1

# Atualização de resultados — a cada 5 min entre 15h-02h UTC (12h-23h Brasília)
*/5 15-23,0-2 * * * cd /home/deploy/bolao_copa && ~/.local/bin/uv run python scripts/atualizar_resultados.py >> /home/deploy/bolao_resultados.log 2>&1
```

**Importante:** usar sempre `~/.local/bin/uv` (caminho completo) — o cron não herda o PATH do usuário e `uv` não é encontrado sem o caminho absoluto.

Logs: `tail -20 /home/deploy/bolao_apostas.log` e `tail -20 /home/deploy/bolao_resultados.log`

## Pontos de atenção

- O `ACCESS_TOKEN` da Meta expira em 24h em ambiente de teste. Sintoma: erro `401 OAuthException code 190` nos logs.
- Ao gerar nova chave do Google Sheets: atualizar `CREDENTIALS_FILE` em `sheets/client.py` e copiar o novo `.json` para a VPS via `scp` antes ou logo após o deploy.
- **Timezone:** o servidor VPS roda em UTC. Todos os checks de horário (12:00 PM, 02:00 AM) devem usar `datetime.now(ZoneInfo("America/Sao_Paulo"))` — nunca `datetime.now()` sem timezone.
- **Dia lógico:** jogos até 02:00 AM do dia seguinte são considerados "jogos de hoje". Usar sempre `_eh_jogo_do_dia(dt)` de `sheets/apostas.py` para este filtro.
- **Quota Google Sheets:** evitar múltiplas leituras da mesma aba em loops. Carregar os dados uma vez e filtrar em memória. A API permite ~60 leituras/minuto.
- **Webhook assíncrono:** o `processar_webhook()` roda em background thread. O Flask retorna 200 imediatamente para evitar retries da Meta. Efeito colateral: exceções no handler não retornam HTTP 500 — monitorar via `journalctl`.
- A trava das 12:00 PM em `handlers/aposta.py` e `handlers/apostas_dia.py` está **ativa em produção**. Para testes locais sem restrição de horário, chamar `gerar_apostas_automaticas()` diretamente.
- Para adicionar um novo tipo de mensagem recebida (ex: `interactive`, `location`), criar `handlers/novo_tipo.py` e registrar em `whatsapp/webhook.py`.
- Para adicionar um novo tipo de envio, adicionar função em `whatsapp/sender.py`.
- Todo handler que encerra o fluxo sem chamar `enviar_template()` deve chamar `enviar_cta()` ao final — padrão estabelecido em todos os handlers existentes.
- Se `atualizar_resultados.py` logar `[MISS]` para algum time, adicionar a entrada no dicionário `NOMES_TIMES` dentro do próprio script.
