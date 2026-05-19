import os, gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly",
          "https://www.googleapis.com/auth/drive.readonly"]
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

def read_topics(worksheet_index: int = 0):
    if not os.path.exists("service_account.json"):
        raise RuntimeError("service_account.json missing. Sheet bulk disabled.")
    creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID).get_worksheet(worksheet_index)
    rows = sh.get_all_records()
    return rows
