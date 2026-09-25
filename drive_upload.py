"""
آپلود فایل صوتی به Google Drive تا از هر دستگاهی (از جمله گوشی، نسخه‌ی ابری) قابل پخش باشه.
فقط نسخه‌ی محلی — از همون سرویس‌اکانتی استفاده می‌کنه که برای Google Sheets داری.
پیش‌نیاز: pip install google-api-python-client
"""
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/drive"]


@st.cache_resource
def _get_drive_service():
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def upload_audio_and_get_link(file_path, filename):
    """
    فایل صوتی رو تو Google Drive آپلود می‌کنه، با لینک برای همه قابل‌خوندنش می‌کنه،
    و یه لینک مستقیم پخش برمی‌گردونه. اگه هر مرحله شکست بخوره، رشته‌ی خالی برمی‌گردونه
    (نباید کل فرآیند دریافت صوت رو متوقف کنه).
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
    except Exception:
        return ""
