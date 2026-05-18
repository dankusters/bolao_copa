import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

filename = "bolaodacopa-496702-2ad378872f88.json"
print(filename)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name(filename, scope)

client = gspread.authorize(creds)

sheet = client.open(title = "tabela_copa", folder_id ="1NOcia_b9GPEk7qR0wp5xMYB2baE7TNTtp0XEMlWLawo").get_worksheet("jogos")

print(sheet)

data = sheet.get_all_records()

df = pd.DataFrame(data)

# print(df)


