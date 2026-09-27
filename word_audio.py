"""
تولید صدای لحظه‌ای (Azure TTS) برای تک‌کلمه یا جمله‌ی کوتاه سوئدی —
برای تمرین «املا» و «دیکته‌ی جمله» تو تب بانک کلمات.
صدا ذخیره‌ی دائم نمی‌شه؛ فقط تو حافظه‌ی جلسه کش می‌شه (st.cache_data).
"""
from xml.sax.saxutils import escape

import requests
import streamlit as st

DEFAULT_VOICE = "sv-SE-SofieNeural"


def _cfg():
    cfg = st.secrets.get("azure_tts")
    if not cfg:
        return None, None
    return cfg.get("api_key", ""), cfg.get("region", "swedencentral")


def tts_available():
    key, _ = _cfg()
    return bool(key)


@st.cache_data(ttl=24 * 3600, max_entries=300, show_spinner=False)
def synth_swedish(text, voice=DEFAULT_VOICE):
    """متن سوئدی رو به mp3 (bytes) تبدیل می‌کنه، یا None اگه کلید تنظیم نشده/خطا داد."""
    key, region = _cfg()
    if not key or not text or not str(text).strip():
        return None
    try:
        token_resp = requests.post(
            f"https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken",
            headers={"Ocp-Apim-Subscription-Key": key},
            timeout=15,
        )
        token_resp.raise_for_status()
        token = token_resp.text

        ssml = (
            '<speak version="1.0" xml:lang="sv-SE">'
            f'<voice name="{voice}">{escape(str(text).strip())}</voice>'
            "</speak>"
        )
        resp = requests.post(
            f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": "audio-16khz-64kbitrate-mono-mp3",
                "User-Agent": "svenska-coach",
            },
            data=ssml.encode("utf-8"),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None
