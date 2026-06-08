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
```

## Arquitetura

O fluxo de uma mensagem recebida é:

```
Meta → POST /webhook → processar_webhook() → handler por tipo → sender
```

**`whatsapp/webhook.py`** recebe o payload da Meta, extrai o tipo da mensagem (`text`, `button`, etc.) e delega para o handler correspondente. Não contém lógica de negócio.

**`handlers/texto.py`** e **`handlers/botao.py`** contêm toda a lógica condicional do bot — é aqui que crescerá a maior parte do código conforme novos fluxos forem adicionados.

**`whatsapp/sender.py`** centraliza os envios:
- `enviar_template(numero, texto)` — envia o template `main_bolao` (com imagem no header e texto no body)
- `enviar_texto(numero, texto)` — envia mensagem de texto livre (só válida dentro da janela de 24h após o usuário interagir)

**`estado.py`** mantém `aguardando_resposta: set[str]` em memória — o conjunto de números de telefone que aguardam a próxima mensagem do usuário para uma resposta contextual. **Este estado é perdido ao reiniciar o servidor.**

**`sheets/client.py`** expõe `get_worksheet(nome)` para acessar abas da planilha `tabela_copa`. Abas disponíveis: `jogos`, `bet`, `apostadores`. O ID da planilha está hardcoded na constante `FOLDER_ID`.

**`sheets/aposta_automatica.py`** gera apostas aleatórias para apostadores que não apostaram até as 12:00. A função `gerar_apostas_automaticas()` é idempotente — verifica `apostas_existentes` antes de criar, nunca duplica. As probabilidades são configuradas em `REGRAS_PLACAR` (máx 4 gols, sendo 4 com 5% de chance). Apostas automáticas são marcadas com `origem = "auto"` na aba `bet`.

**`scripts/apostas_automaticas.py`** script standalone chamado pelo cron no VPS às 15:00 UTC (12:00 Brasília). Também é chamado inline pelo handler `apostas_dia` ao primeiro acesso após as 12:00, eliminando condição de corrida com o cron.

## Variáveis de ambiente (`.env`)

```
ACCESS_TOKEN=       # Token temporário da Meta (expira em 24h — renovar no painel da Meta)
PHONE_NUMBER_ID=    # ID do número de telefone no painel da Meta
VERIFY_TOKEN=       # String livre usada para validar o webhook na Meta
RECIPIENT_NUMBER=   # Número de teste (formato: 5511999999999)
```

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
Apostas automáticas configuradas no crontab do usuário `deploy`:
```
0 15 * * * cd /home/deploy/bolao_copa && uv run python scripts/apostas_automaticas.py >> /home/deploy/bolao_apostas.log 2>&1
```
15:00 UTC = 12:00 Brasília. Ver/editar com `crontab -e` na VPS.

## Pontos de atenção

- O `ACCESS_TOKEN` da Meta expira em 24h em ambiente de teste. Sintoma: erro `401 OAuthException code 190` nos logs.
- Ao gerar nova chave do Google Sheets: atualizar `CREDENTIALS_FILE` em `sheets/client.py` e copiar o novo `.json` para a VPS via `scp` antes ou logo após o deploy.
- A trava das 12:00 em `handlers/apostas_dia.py` está **ativa em produção**. Para testes locais sem restrição de horário, chamar `gerar_apostas_automaticas()` diretamente.
- `COL_FORMULA_INICIO` em `sheets/apostas.py` deve apontar para a primeira coluna com fórmula na aba `bet`. Atualmente é 11 (coluna K = `situacao`). Se adicionar/remover colunas antes dessa posição, atualizar a constante.
- Para adicionar um novo tipo de mensagem recebida (ex: `interactive`, `location`), criar `handlers/novo_tipo.py` e registrar em `whatsapp/webhook.py`.
- Para adicionar um novo tipo de envio, adicionar função em `whatsapp/sender.py`.
