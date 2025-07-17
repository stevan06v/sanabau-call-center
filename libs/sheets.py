import gspread
from google.oauth2.service_account import Credentials

scopes = [
    "https://www.googleapis.com/auth/spreadsheets"
]
creds = Credentials.from_service_account_file('../credentials.json', scopes=scopes)

client = gspread.authorize(creds)

sheet_id = "1JXfj7bJ0kUceNgbTMgoSHg34_qb7Z8akd69IaB4lXvQ"

workbook = client.open_by_key(sheet_id)

