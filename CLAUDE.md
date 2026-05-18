# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projeto

Bot de bolão da Copa do Mundo via WhatsApp, usando Meta Cloud API + Flask + Google Sheets. Em ambiente de desenvolvimento local, o ngrok expõe o servidor Flask para a internet, permitindo que a Meta entregue eventos de webhook.

## Comandos

```bash
# Instalar dependências
uv sync

# Rodar o servidor Flask
uv run python app.py

# Expor localmente via ngrok (terminal separado)
ngrok http 5000

# Verificar planilha Google Sheets
uv run python sheets/teste_gsheets.py

# Listar templates WhatsApp disponíveis
uv run python check_templates.py
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

## Variáveis de ambiente (`.env`)

```
ACCESS_TOKEN=       # Token temporário da Meta (expira em 24h — renovar no painel da Meta)
PHONE_NUMBER_ID=    # ID do número de telefone no painel da Meta
VERIFY_TOKEN=       # String livre usada para validar o webhook na Meta
RECIPIENT_NUMBER=   # Número de teste (formato: 5511999999999)
```

## Credenciais Google Sheets

O arquivo `sheets/bolaodacopa-496702-2ad378872f88.json` (conta de serviço) deve estar dentro da pasta `sheets/`. Não é versionado. Para obter: Google Cloud Console → conta de serviço → baixar chave JSON → compartilhar a planilha com o e-mail da conta de serviço.

## Pontos de atenção

- O `ACCESS_TOKEN` da Meta expira em 24h em ambiente de teste. Sintoma: erro `401 OAuthException code 190` nos logs.
- O ngrok gera uma nova URL a cada reinicialização. Atualizar em: Meta for Developers → WhatsApp → Configuration → Webhook → Edit.
- Para adicionar um novo tipo de mensagem recebida (ex: `interactive`, `location`), criar `handlers/novo_tipo.py` e registrar em `whatsapp/webhook.py`.
- Para adicionar um novo tipo de envio, adicionar função em `whatsapp/sender.py`.
