import gspread
from google.oauth2.service_account import Credentials
import os
from keys import WORKSHEET

scopes = [
    "https://www.googleapis.com/auth/spreadsheets"
]

DIR = os.path.dirname(__file__)  # directory of sheets.py
creds = Credentials.from_service_account_file(
    os.path.join(DIR, '../credentials.json'),
    scopes=scopes
)
client = gspread.authorize(creds)

sheet_id = "1JXfj7bJ0kUceNgbTMgoSHg34_qb7Z8akd69IaB4lXvQ"

workbook = client.open_by_key(sheet_id)

sheet = workbook.worksheet(WORKSHEET)


def get_records_from_worksheet(worksheet_name) -> list:
    lead_records = sheet.get_all_records()
    print(lead_records)
    return lead_records

