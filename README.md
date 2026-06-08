# Bolão da Copa — WhatsApp Bot

Bot para gerenciamento de bolão via WhatsApp, integrado à API Cloud da Meta e Google Sheets.

---

## Visão geral

O bot recebe mensagens via webhook do WhatsApp (Meta Cloud API), processa as respostas dos participantes e registra os palpites em uma planilha do Google Sheets.

### Fluxo básico

```
Participante → WhatsApp → Meta Cloud API → Webhook (Flask) → Handlers → Google Sheets
```

---

## Estrutura do projeto

```
bolao_copa/
├── app.py                        # Servidor Flask e rotas
├── config.py                     # Leitura das variáveis de ambiente
├── estado.py                     # Estado da conversa em memória
├── whatsapp/
│   ├── sender.py                 # Funções de envio (template, texto)
│   └── webhook.py                # Recebimento e roteamento de mensagens
├── handlers/
│   ├── texto.py                  # Lógica para mensagens de texto
│   ├── botao.py                  # Lógica para cliques de botão
│   ├── aposta.py                 # Fluxo de registro de apostas
│   ├── apostas_dia.py            # Exibe apostas do dia (após 12h)
│   ├── ranking.py                # Exibe ranking individual e por família
│   └── detalhe_jogo.py           # Exibe resultado detalhado por jogo
├── sheets/
│   ├── client.py                 # Integração com Google Sheets
│   ├── apostas.py                # Leitura e gravação de apostas
│   ├── aposta_automatica.py      # Geração automática de apostas
│   ├── ranking.py                # Cálculo de pontuação e ranking
│   └── detalhe_jogo.py           # Busca apostas por jogo
├── scripts/
│   └── apostas_automaticas.py    # Script para cron (apostas automáticas)
├── utils/
│   └── flags.py                  # Emojis de bandeiras por país
├── pyproject.toml
└── .env                          # Variáveis de ambiente (não versionar)
```

---

## Pré-requisitos

- Python **3.14+**
- Gerenciador de pacotes **uv**
- Conta no [Meta for Developers](https://developers.facebook.com) com app de WhatsApp configurado
- Conta Google com acesso à planilha do bolão
- **ngrok** (para expor o servidor local durante o desenvolvimento)

---

## Configuração — Linux

### 1. Instalar uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

### 2. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd bolao_copa
```

### 3. Instalar dependências

```bash
uv sync
```

### 4. Configurar variáveis de ambiente

Crie o arquivo `.env` na raiz do projeto:

```bash
nano .env
```

Preencha com os valores corretos (veja a seção [Variáveis de ambiente](#variáveis-de-ambiente)).

### 5. Adicionar credenciais do Google Sheets

Coloque o arquivo `.json` da conta de serviço do Google na raiz do projeto (o nome deve corresponder ao definido em `sheets/client.py`).

### 6. Instalar e configurar ngrok

```bash
# Instalar
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Autenticar (token em https://dashboard.ngrok.com)
ngrok config add-authtoken <seu_token_ngrok>
```

---

## Configuração — Windows

### 1. Instalar uv

Abra o PowerShell como administrador e execute:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Feche e reabra o terminal após a instalação.

### 2. Clonar o repositório

```powershell
git clone <url-do-repositorio>
cd bolao_copa
```

### 3. Instalar dependências

```powershell
uv sync
```

### 4. Configurar variáveis de ambiente

Crie o arquivo `.env` na raiz do projeto (pode usar o Bloco de Notas ou VS Code):

```
ACCESS_TOKEN=<seu_valor>
PHONE_NUMBER_ID=<seu_valor>
VERIFY_TOKEN=<seu_valor>
RECIPIENT_NUMBER=<seu_valor>
```

### 5. Adicionar credenciais do Google Sheets

Coloque o arquivo `.json` da conta de serviço do Google na raiz do projeto.

### 6. Instalar ngrok

Baixe o instalador em [ngrok.com/download](https://ngrok.com/download) e siga as instruções.

Após instalar, autentique no PowerShell:

```powershell
ngrok config add-authtoken <seu_token_ngrok>
```

---

## Variáveis de ambiente

| Variável          | Onde encontrar                                                                    |
|-------------------|-----------------------------------------------------------------------------------|
| `ACCESS_TOKEN`    | Meta for Developers → seu app → WhatsApp → API Setup → Temporary access token    |
| `PHONE_NUMBER_ID` | Meta for Developers → seu app → WhatsApp → API Setup → Phone number ID           |
| `VERIFY_TOKEN`    | Valor livre definido por você, usado na verificação do webhook                    |
| `RECIPIENT_NUMBER`| Número de teste no formato internacional sem `+` (ex: `5511999999999`)           |

> O `ACCESS_TOKEN` temporário expira em **24 horas**. Para produção, gere um token de longa duração via Business Manager.

---

## Rodando o projeto

### Terminal 1 — Servidor Flask

```bash
uv run python app.py
```

O servidor sobe em `http://localhost:5000`.

### Terminal 2 — ngrok

```bash
ngrok http 5000
```

O ngrok gera uma URL pública (ex: `https://abc123.ngrok-free.app`). Copie essa URL.

---

## Configurando o webhook na Meta

1. Acesse [Meta for Developers](https://developers.facebook.com) → seu app → **WhatsApp → Configuration**
2. Em **Webhook**, clique em **Edit**
3. Preencha:
   - **Callback URL**: `https://<sua-url-ngrok>/webhook`
   - **Verify Token**: o mesmo valor definido em `VERIFY_TOKEN` no `.env`
4. Clique em **Verify and Save**
5. Em **Webhook fields**, ative o campo **messages**

---

## Rotas disponíveis

| Método | Rota       | Descrição                                       |
|--------|------------|-------------------------------------------------|
| GET    | `/`        | Health check                                    |
| GET    | `/webhook` | Verificação do webhook pela Meta                |
| POST   | `/webhook` | Recebimento de mensagens                        |
| GET    | `/enviar`  | Envia mensagem de teste para `RECIPIENT_NUMBER` |

---

## Google Sheets

O projeto usa uma conta de serviço do Google para acessar a planilha. Para configurar:

1. No [Google Cloud Console](https://console.cloud.google.com), crie um projeto e ative as APIs **Google Sheets** e **Google Drive**
2. Crie uma **conta de serviço** e baixe o arquivo de credenciais `.json`
3. Coloque o `.json` na raiz do projeto
4. Compartilhe a planilha com o e-mail da conta de serviço (com permissão de editor)
5. Confirme que o nome do arquivo `.json`, o nome da planilha e o `folder_id` em `sheets/client.py` estão corretos

---

## Apostas automáticas

Participantes que não apostarem até as 12:00 do dia do jogo recebem apostas geradas automaticamente com placares aleatórios baseados em probabilidades reais de futebol (máx. 4 gols, sendo 4 com apenas 5% de chance). As apostas automáticas são marcadas com `origem = "auto"` na planilha e exibidas com o emoji 🤖 no bot.

A geração ocorre:
- **Ao vivo**, quando qualquer usuário clica "ver apostas do dia" após as 12:00
- **Via cron** no VPS às 15:00 UTC (12:00 Brasília), como rede de segurança

As probabilidades são configuráveis em `sheets/aposta_automatica.py` → `REGRAS_PLACAR`.

---

## Observações importantes

- O arquivo `.env` e o `.json` de credenciais do Google **nunca devem ser versionados** (já estão no `.gitignore`)
- O estado da conversa (`estado.py`) é mantido em memória: reiniciar o servidor limpa o estado de todos os usuários
- Ao gerar nova chave do Google Sheets, atualizar `CREDENTIALS_FILE` em `sheets/client.py` e copiar o `.json` para a VPS
