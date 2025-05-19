import os, csv, hashlib, datetime, base64, tempfile, requests
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials

# ---- Google 認証 -------------------------------------------------
cred_json = base64.b64decode(os.environ["GCP_SERVICE_KEY"])
with tempfile.NamedTemporaryFile(delete=False) as fp:
    fp.write(cred_json)
    key_path = fp.name

scope = ["https://www.googleapis.com/auth/spreadsheets"]
gc = gspread.authorize(Credentials.from_service_account_file(key_path, scopes=scope))

sh = gc.open_by_key(os.environ["SPREADSHEET_ID"])
ws = sh.worksheet(os.environ["WORKSHEET_NAME"])   # タブ名が一致していること！

records = ws.get_all_records()      # A1 行目 = ヘッダ必須
row_map = {r["企業名"]: i + 2 for i, r in enumerate(records)}        # 2 行目から
cur_hash = {r["企業名"]: ws.cell(i + 2, 26).value for i, r in enumerate(records)}  # Z 列

# ---- URL 巡回 ----------------------------------------------------
with open("urls.csv", newline="", encoding="utf-8") as f:
    rdr = csv.DictReader(f)
    for item in rdr:
        name, url = item["company"], item["url"]
        html = requests.get(url, timeout=15).text
        body = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        new_hash = hashlib.sha256(body.encode()).hexdigest()

        if new_hash != cur_hash.get(name):
            row = row_map[name]
            today = datetime.date.today().isoformat()
            prev = ws.cell(row, 4).value or ""
            ws.update(f"C{row}:E{row}", [[today, f"{prev} / 更新検知 {today}", new_hash]])
            print(f"[{name}] UPDATED")
        else:
            print(f"[{name}] no change")
