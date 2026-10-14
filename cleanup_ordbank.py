"""
یه‌بار اجرا می‌شه: بانک کلمات (تب ordbank) رو فقط به واژه‌های
آخرین درس روزانه (تب lessons) محدود می‌کنه — بقیه‌ی کلمات قدیمی حذف می‌شن.
اجرا: python cleanup_ordbank.py
"""
import json
import sys

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

secrets = tomllib.loads(open(".streamlit/secrets.toml", encoding="utf-8").read())
creds = Credentials.from_service_account_info(secrets["gcp_service_account"], scopes=SCOPES)
gc = gspread.authorize(creds)
sh = gc.open_by_key(secrets["svenska_sheet_id"])

lessons_ws = sh.worksheet("lessons")
lesson_rows = lessons_ws.get_all_records()
if not lesson_rows:
    print("هیچ درسی تو تب lessons نیست.")
    sys.exit(1)

# آخرین درس = بیشترین شماره
last = max(lesson_rows, key=lambda r: int(r.get("شماره") or 0))
words_raw = last.get("واژه‌ها", "")
try:
    vocab = json.loads(words_raw) if words_raw else []
except json.JSONDecodeError:
    vocab = []
keep_words = {str(v.get("word", "")).strip().lower() for v in vocab if v.get("word")}

print(f"آخرین درس: #{last.get('شماره')} — {last.get('عنوان')} ({last.get('تاریخ')})")
print(f"واژه‌های این درس ({len(keep_words)}): {', '.join(sorted(keep_words))}")

ordbank_ws = sh.worksheet("ordbank")
header = ordbank_ws.row_values(1)
rows = ordbank_ws.get_all_records()
kept_rows = [r for r in rows if str(r.get("کلمه", "")).strip().lower() in keep_words]
removed = len(rows) - len(kept_rows)

print(f"\nاز {len(rows)} کلمه‌ی فعلی بانک، {len(kept_rows)} تا نگه داشته می‌شه و {removed} تا حذف می‌شه.")
confirm = input("مطمئنی؟ برای ادامه Y رو بزن و Enter: ").strip().lower()
if confirm != "y":
    print("لغو شد، چیزی تغییر نکرد.")
    sys.exit(0)

ordbank_ws.clear()
ordbank_ws.append_row(header)
if kept_rows:
    ordbank_ws.append_rows(
        [[r.get(h, "") for h in header] for r in kept_rows],
        value_input_option="RAW",
    )

print("✅ انجام شد.")
