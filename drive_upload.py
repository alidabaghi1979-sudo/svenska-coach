"""
آپلود فایل صوتی به Google Drive شخصی خودت (با OAuth، نه سرویس‌اکانت) تا از هر
دستگاهی از جمله گوشی (نسخه‌ی ابری) قابل پخش باشه.

چرا OAuth و نه سرویس‌اکانت: سرویس‌اکانت‌ها اصلاً فضای ذخیره‌سازی Drive شخصی ندارن
(محدودیت خود گوگل، نه باگ ما) و آپلود باهاشون شکست می‌خوره. با OAuth، فایل‌ها تو
Drive خود Ali با فضای واقعی ذخیره می‌شن.

پیش‌نیاز یک‌بار: oauth_setup.py رو اجرا کن و مقادیر [gdrive_oauth] رو تو secrets.toml بذار.
پیش‌نیاز کتابخونه: pip install google-api-python-client
"""
import streamlit as st
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]


@st.cache_resource
def _get_drive_service():
    oauth = st.secrets["gdrive_oauth"]
    creds = Credentials(
        token=None,
        refresh_token=oauth["refresh_token"],
        client_id=oauth["client_id"],
        client_secret=oauth["client_secret"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    creds.refresh(Request())  # توکن دسترسی تازه بگیر (refresh_token همیشه معتبر می‌مونه)
    return build("drive", "v3", credentials=creds)


def upload_audio_and_get_link(file_path, filename):
    """
    فایل صوتی رو تو Drive شخصی آپلود می‌کنه، با لینک برای همه قابل‌خوندنش می‌کنه،
    و یه لینک مستقیم پخش برمی‌گردونه. اگه شکست بخوره، رشته‌ی خالی برمی‌گردونه
    (نباید کل فرآیند دریافت صوت رو متوقف کنه) — ولی خطا رو هم چاپ می‌کنه تا گم نشه.
    """
    try:
        service = _get_drive_service()
        file_metadata = {"name": filename}
        media = MediaFileUpload(file_path, mimetype="audio/mpeg", resumable=False)
        uploaded = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
        file_id = uploaded["id"]

        service.permissions().create(
            fileId=file_id, body={"role": "reader", "type": "anyone"}
        ).execute()

        return f"https://drive.google.com/uc?export=download&id={file_id}"
    except Exception as e:
        print(f"✗ خطا در آپلود به Drive: {e}")
        return ""
