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
    "ordbank": ["تاریخ", "کلمه", "معنی", "جمله", "سطح", "مرور_بعدی"],
    "mina_fel": ["اولین_بار", "نوع_خطا", "غلط", "درست", "تعداد"],
    "progress": ["تاریخ", "موضوع", "درصد_فهم", "نکته"],
    "audio_log": ["تاریخ", "منبع", "عنوان", "مسیر_محلی", "رونوشت", "لینک_درایو"],
    # درس‌های صوتی روزانه — پایپ‌لاین daily_lesson/ می‌نویسه، اپ فقط می‌خونه.
    # (باید با LESSONS_HEADER در daily_lesson/sheets_sync.py یکی باشه)
    "lessons": ["تاریخ", "شماره", "عنوان", "موضوع", "دسته", "گرامر", "توضیح_گرامر",
                "مثال‌ها", "واژه‌ها", "متن", "لینک_درایو", "شناسه_فایل", "مدت_دقیقه"],
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


@st.cache_data(ttl=20)
def read_tab(tab_name):
    """محتوای یه تب رو به‌صورت DataFrame برمی‌گردونه."""
    ws = get_or_create_tab(tab_name)
    records = ws.get_all_records()
    return pd.DataFrame(records) if records else pd.DataFrame(columns=SHEET_TABS[tab_name])


def append_row(tab_name, row_values):
    """یه ردیف جدید به انتهای تب اضافه می‌کنه."""
    ws = get_or_create_tab(tab_name)
    ws.append_row(row_values)
    read_tab.clear()


def overwrite_tab(tab_name, df):
    """کل محتوای تب رو با دیتافریم ویرایش‌شده جایگزین می‌کنه (بعد از st.data_editor)."""
    ws = get_or_create_tab(tab_name)
    ws.clear()
    ws.append_row(SHEET_TABS[tab_name])
    if not df.empty:
        ws.append_rows(df.astype(str).values.tolist())
    read_tab.clear()


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
    read_tab.clear()
    return True
