"""
تولید صدای لحظه‌ای (Azure TTS) برای تک‌کلمه یا جمله‌ی کوتاه سوئدی —
برای تمرین «املا» و «دیکته‌ی جمله» تو تب بانک کلمات.
صدا ذخیره‌ی دائم نمی‌شه؛ فقط تو حافظه‌ی جلسه کش می‌شه (st.cache_data).
"""
from xml.sax.saxutils import escape

import requests
import streamlit as st

DEFAULT_VOICE = "sv-SE-SofieNeural"
# صداهای مختلف برای دیالوگ‌های چندنفره (به‌ترتیب به هر گوینده‌ی جدید اختصاص داده می‌شه)
DIALOG_VOICES = ["sv-SE-SofieNeural", "sv-SE-MattiasNeural", "sv-SE-HilleviNeural", "sv-SE-NilsNeural"]


def _cfg():
    cfg = st.secrets.get("azure_tts")
    if not cfg:
        return None, None
    return cfg.get("api_key", ""), cfg.get("region", "swedencentral")


def tts_available():
    key, _ = _cfg()
    return bool(key)


def _get_token(key, region):
    token_resp = requests.post(
        f"https://{region}.api.cognitive.microsoft.com/sts/v1.0/issueToken",
        headers={"Ocp-Apim-Subscription-Key": key},
        timeout=15,
    )
    token_resp.raise_for_status()
    return token_resp.text


def _synth_ssml(ssml, key, region):
    token = _get_token(key, region)
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


@st.cache_data(ttl=24 * 3600, max_entries=300, show_spinner=False)
def synth_swedish(text, voice=DEFAULT_VOICE):
    """متن سوئدی رو به mp3 (bytes) تبدیل می‌کنه، یا None اگه کلید تنظیم نشده/خطا داد."""
    key, region = _cfg()
    if not key or not text or not str(text).strip():
        return None
    try:
        ssml = (
            '<speak version="1.0" xml:lang="sv-SE">'
            f'<voice name="{voice}">{escape(str(text).strip())}</voice>'
            "</speak>"
        )
        return _synth_ssml(ssml, key, region)
    except Exception:
        return None


@st.cache_data(ttl=24 * 3600, max_entries=150, show_spinner=False)
def synth_dialog(lines):
    """
    lines: تاپل از (speaker, text) — برای هر گوینده‌ی جدید یه صدای متفاوت اختصاص می‌ده
    (برای تمرین‌های شنیداریِ دیالوگی). یه mp3 واحد برمی‌گردونه، یا None.
    """
    key, region = _cfg()
    if not key or not lines:
        return None
    try:
        voice_map = {}
        parts = []
        for speaker, text in lines:
            text = str(text).strip()
            if not text:
                continue
            if speaker not in voice_map:
                voice_map[speaker] = DIALOG_VOICES[len(voice_map) % len(DIALOG_VOICES)]
            parts.append(f'<voice name="{voice_map[speaker]}">{escape(text)}<break time="500ms"/></voice>')
        if not parts:
            return None
        ssml = '<speak version="1.0" xml:lang="sv-SE">' + "".join(parts) + "</speak>"
        return _synth_ssml(ssml, key, region)
    except Exception:
        return None
