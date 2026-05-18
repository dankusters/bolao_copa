import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

filename = "sheets/bolaodacopa-496702-2ad378872f88.json"
print(filename)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name(filename, scope)

client = gspread.authorize(creds)

sheet = client.open_by_key("1NOcia_b9GPEk7qR0wp5xMYB2baE7TNTtp0XEMlWLawo").worksheet("jogos")

print(sheet)

data = sheet.get_all_records()

df = pd.DataFrame(data)

print(df)


