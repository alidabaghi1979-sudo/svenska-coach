"""
اتصال به Google Sheets برای ذخیره‌ی بانک کلمات، خطاها، پیشرفت و لاگ صوت.
از همون الگوی سرویس‌اکانتی استفاده می‌کنه که تو AT Journal داری.
"""
import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ستون‌های هر تب — اگه تب وجود نداشته باشه، با همین هدرها ساخته می‌شه
SHEET_TABS = {
    "ordbank": ["تاریخ", "کلمه", "معنی", "جمله", "سطح", "مرور_بعدی", "جملات_تمرینی"],
    "mina_fel": ["اولین_بار", "نوع_خطا", "غلط", "درست", "تعداد"],
    "progress": ["تاریخ", "موضوع", "درصد_فهم", "نکته"],
    "review_log": ["تاریخ", "تعداد_کارت", "تعداد_درست"],
    "coach_log": ["تاریخ", "نقش", "پیام"],
    "audio_log": ["تاریخ", "منبع", "عنوان", "مسیر_محلی", "رونوشت", "لینک_درایو"],
    # درس‌های صوتی روزانه — پایپ‌لاین daily_lesson/ می‌نویسه، اپ فقط می‌خونه.
    # (باید با LESSONS_HEADER در daily_lesson/sheets_sync.py یکی باشه)
    "lessons": ["تاریخ", "شماره", "عنوان", "موضوع", "دسته", "گرامر", "توضیح_گرامر",
                "مثال‌ها", "واژه‌ها", "متن", "لینک_درایو", "شناسه_فایل", "مدت_دقیقه",
                "تایم‌استمپ_جمله‌ها"],
    # تمرین‌های خودکارِ هر درس — پایپ‌لاین daily_lesson/ می‌نویسه، اپ فقط می‌خونه.
    # (باید با EXERCISES_HEADER در daily_lesson/sheets_sync.py یکی باشه)
    "exercises": ["شماره_درس", "تاریخ", "گرامر", "درک_مطلب", "واژگان"],
    # اسناد اسکن‌شده (نامه/متن) از تب مربی — متن و ترجمه (بدون خودِ عکس؛ اطلاعات شخصی پوشیده)
    "dokument": ["شناسه", "تاریخ", "عنوان", "نوع", "فرستنده", "متن_سوئدی", "ترجمه_فارسی",
                 "نکات", "مهلت‌ها", "واژه‌ها"],
}


@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=SCOPES
    )
    return gspread.authorize(creds)


def get_spreadsheet():
    client = get_client()
    return client.open_by_key(st.secrets["svenska_sheet_id"])


def get_or_create_tab(tab_name):
    """
    اگه تب تو شیت وجود نداشت، با هدر درست می‌سازتش.
    اگه وجود داشت ولی هدرش قدیمی‌تر از اسکیمای فعلیه (مثلاً یه ستون جدید بعداً اضافه شده)،
    فقط وقتی که هدر فعلی دقیقاً پیشوندِ هدر جدیده (یعنی چیزی جابه‌جا/حذف نشده، فقط اضافه شده)،
    هدر رو خودکار تکمیل می‌کنه — بدون دست‌زدن به داده‌های موجود.
    """
    ss = get_spreadsheet()
    expected_header = SHEET_TABS[tab_name]
    try:
        ws = ss.worksheet(tab_name)
        current_header = ws.row_values(1)
        if current_header and current_header != expected_header:
            if expected_header[: len(current_header)] == current_header:
                ws.update("A1", [expected_header])
        return ws
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=tab_name, rows=1000, cols=len(expected_header))
        ws.append_row(expected_header)
        return ws


@st.cache_data(ttl=60)
def read_tab(tab_name):
    """محتوای یه تب رو به‌صورت DataFrame برمی‌گردونه."""
    ws = get_or_create_tab(tab_name)
    records = ws.get_all_records()
    return pd.DataFrame(records) if records else pd.DataFrame(columns=SHEET_TABS[tab_name])


def append_row(tab_name, row_values):
    """یه ردیف جدید به انتهای تب اضافه می‌کنه."""
    ws = get_or_create_tab(tab_name)
    ws.append_row(row_values)
    read_tab.clear(tab_name)


def append_rows(tab_name, rows):
    """چند ردیف رو یک‌جا (یک درخواست API) به انتهای تب اضافه می‌کنه."""
    if not rows:
        return
    ws = get_or_create_tab(tab_name)
    ws.append_rows(rows, value_input_option="RAW")
    read_tab.clear(tab_name)


def overwrite_tab(tab_name, df):
    """کل محتوای تب رو با دیتافریم ویرایش‌شده جایگزین می‌کنه (بعد از st.data_editor)."""
    ws = get_or_create_tab(tab_name)
    ws.clear()
    ws.append_row(SHEET_TABS[tab_name])
    if not df.empty:
        ws.append_rows(df.astype(str).values.tolist())
    read_tab.clear(tab_name)


def batch_update_by_match(tab_name, match_col, items):
    """
    چند ردیف رو یک‌جا آپدیت می‌کنه (تعداد درخواست‌های API ثابت و کم).
    items: لیستی از (مقدار_تطبیق, {ستون: مقدار}). خروجی: تعداد ردیف‌های آپدیت‌شده.
    """
    if not items:
        return 0
    ws = get_or_create_tab(tab_name)
    header = ws.row_values(1)
    if match_col not in header:
        return 0
    match_idx = header.index(match_col) + 1
    col_vals = ws.col_values(match_idx)
    row_of = {}
    for r, v in enumerate(col_vals, start=1):
        if r > 1 and v not in row_of:
            row_of[v] = r
    data = []
    for match_val, updates in items:
        row = row_of.get(str(match_val))
        if not row:
            continue
        for col_name, value in updates.items():
            if col_name in header:
                data.append({
                    "range": gspread.utils.rowcol_to_a1(row, header.index(col_name) + 1),
                    "values": [[value]],
                })
    if data:
        ws.batch_update(data)
    read_tab.clear(tab_name)
    return len(data)


def update_cells_by_match(tab_name, match_col, match_val, updates: dict):
    """
    یه ردیف رو با تطبیق مقدار یه ستون (مثلاً کلمه) پیدا می‌کنه و فقط
    ستون‌های داده‌شده تو updates رو آپدیت می‌کنه — بدون دست‌زدن به بقیه‌ی ردیف.
    خروجی: True اگه پیدا و آپدیت شد، False اگه پیدا نشد.
    """
    ws = get_or_create_tab(tab_name)
    header = ws.row_values(1)
    if match_col not in header:
        return False
    match_col_idx = header.index(match_col) + 1
    cell = ws.find(str(match_val), in_column=match_col_idx)
    if cell is None:
        return False
    for col_name, value in updates.items():
        if col_name in header:
            col_idx = header.index(col_name) + 1
            ws.update_cell(cell.row, col_idx, value)
    read_tab.clear(tab_name)
    return True


def increment_review_log(date_str, add_cards, add_correct):
    """
    شمارنده‌ی روزانه‌ی مرور (تب review_log): اگه ردیف امروز هست، تعدادها رو بهش اضافه می‌کنه؛
    وگرنه ردیف جدید می‌سازه. هر بار که چند کارت تو شیت ذخیره می‌شه صدا زده می‌شه.
    """
    ws = get_or_create_tab("review_log")
    dates = ws.col_values(1)
    row = None
    for r in range(len(dates), 1, -1):  # از آخر به اول؛ ردیف ۱ هدره
        if str(dates[r - 1]).strip()[:10] == date_str:
            row = r
            break
    if row is None:
        ws.append_row([date_str, int(add_cards), int(add_correct)])
    else:
        old = ws.row_values(row)
        def _num(i):
            try:
                return int(float(old[i]))
            except (IndexError, ValueError):
                return 0
        ws.update(range_name=f"B{row}:C{row}", values=[[_num(1) + int(add_cards), _num(2) + int(add_correct)]])
    read_tab.clear("review_log")
