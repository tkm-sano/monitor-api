import os, csv, hashlib, datetime, base64, tempfile, requests, json
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials

# --- Google 認証 ---
cred_json = base64.b64decode(os.environ["GCP_SERVICE_KEY"])
with tempfile.NamedTemporaryFile(delete=False) as fp:
    fp.write(cred_json)
    sa_file = fp.name

scope = ["https://www.googleapis.com/auth/spreadsheets"]
gc = gspread.authorize(Credentials.from_service_account_file(sa_file, scopes=scope))
sh = gc.open_by_key(os.environ["1PllPj6Jh51_9u5-3sLJXEgWjuXwQIXg004Bh9EUcWe8"])
ws = sh.worksheet(os.environ["新卒採用トラッカー（初期版）"])

records = ws.get_all_records()
row_map = {r["企業名"]: i + 2 for i, r in enumerate(records)}  # 2 行目～
current_hash = {r["企業名"]: ws.cell(i + 2, 26).value for i, r in enumerate(records)}

# --- URL 巡回 ---
for name, url in csv.reader(open("urls.csv")):
    if name == "company":
        continue
    html = requests.get(url, timeout=15).text
    body = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    new = hashlib.sha256(body.encode()).hexdigest()
    if new != current_hash.get(name):
        row = row_map[name]
        today = datetime.date.today().isoformat()
        prev = ws.cell(row, 4).value or ""
        ws.update(f"C{row}:E{row}", [[today, f"{prev} / 更新検知 {today}", new]])
        print(f"[{name}] UPDATED")
    else:
        print(f"[{name}] no change")