from handlers.aposta import handle_aposta
from handlers.detalhe_apostador import handle_detalhe_apostador
from whatsapp.sender import enviar_template, enviar_texto
from sheets.apostas import verificar_e_marcar_primeiro_acesso

_REGRAS = (
    "\n\n"
    "⚽ *Apostas:*\n"
    "- individuais para cada dia de jogos e podem ser feitas até as 12:00 AM. Jogos da madrugada do dia seguinte serão considerados como \"jogos do dia\". Exemplo: Austrália e Turquia, 14/06, 01:00 AM aparecerá para apostar no dia 13/06.\n"
    "- caso o apostador não faça aposta até as 12:00 AM, o robô 🤖 criará uma aposta aleatória com limite de até 3 gols para qualquer lado.\n"
    "- qualquer adulto poderá apostar por qualquer outro apostador adulto ou criança do mesmo \"núcleo familiar\".\n\n"
    "🏆 *Pontuação:*\n"
    "- para ficar competitivo até o final, acertar a situação (vitória mandante, vitória visitante ou empate) vale 1 ponto e placar exato vale 2 pontos extras, totalizando até 3 pontos por partida.\n"
    "- na fase de eliminação, para jogos que forem para disputa de pênaltis, será pontuada a situação de empate e placar exato considerando tempo regular + prorrogação. Resultado dos pênaltis e placar dos pênaltis não serão considerados.\n\n"
    "👨‍👩‍👧‍👦 *Ranking família:*\n"
    "- soma de pontuação dividida pela quantidade de apostadores do \"núcleo familiar\"."
)


def handle_texto(numero: str, msg: dict):
    texto = msg["text"]["body"]
    print(f"[MSG] Mensagem de {numero}: {texto}")

    nome = verificar_e_marcar_primeiro_acesso(numero)
    if nome:
        enviar_texto(numero, f"Olá, {nome}! Como é seu primeiro acesso, leia atentamente as regras:{_REGRAS}")

    if handle_aposta(numero, texto):
        return
    if handle_detalhe_apostador(numero, texto):
        return

    enviar_template(numero)
