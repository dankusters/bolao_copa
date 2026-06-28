import gspread
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = "sheets/bolaodacopa-496702-3b6367a7a6b9.json"
SPREADSHEET_NAME = "tabela_copa"
FOLDER_ID = "1NOcia_b9GPEk7qR0wp5xMYB2baE7TNTtp0XEMlWLawo"

_SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def get_worksheet(nome: str):
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, _SCOPE)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(FOLDER_ID)
    return spreadsheet.worksheet(nome)
