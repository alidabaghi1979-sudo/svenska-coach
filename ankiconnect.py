"""
ارسال مستقیم کارت به Anki از طریق افزونه‌ی AnkiConnect (بدون دانلود/ایمپورت فایل).
پیش‌نیاز: نصب افزونه‌ی AnkiConnect تو Anki (کد 2055492159) و باز بودن خود Anki.
فقط رو نسخه‌ی محلی کار می‌کنه، چون به localhost:8765 نیاز داره.
"""
import base64
import re

import requests

ANKICONNECT_URL = "http://127.0.0.1:8765"
MODEL_NAME = "Svenska Coach Cloze v2"
DECK_NAME = "Svenska Coach::Ordförråd"


def _invoke(action, **params):
    payload = {"action": action, "version": 6, "params": params}
    resp = requests.post(ANKICONNECT_URL, json=payload, timeout=5)
    resp.raise_for_status()
    result = resp.json()
    if result.get("error"):
        raise RuntimeError(result["error"])
    return result.get("result")


def is_available():
    """چک می‌کنه Anki باز و AnkiConnect در دسترسه یا نه."""
    try:
        _invoke("version")
        return True
    except Exception:
        return False


def _ensure_deck():
    _invoke("createDeck", deck=DECK_NAME)


def _ensure_model():
    existing = _invoke("modelNames") or []
    if MODEL_NAME in existing:
        return
    _invoke(
        "createModel",
        modelName=MODEL_NAME,
        inOrderFields=["Text", "Extra", "Audio"],
        isCloze=True,
        cardTemplates=[
            {
                "Name": "Cloze",
                "Front": "{{type:cloze:Text}}<br>{{Audio}}",
                "Back": "{{cloze:Text}}<hr id='answer'>{{Extra}}<br>{{Audio}}",
            }
        ],
    )


def _make_cloze_text(sentence, word):
    pattern = re.compile(r"\b" + re.escape(word) + r"\b")
    cloze_text, n = pattern.subn(f"{{{{c1::{word}}}}}", sentence, count=1)
    if n == 0:
        cloze_text = sentence.replace(word, f"{{{{c1::{word}}}}}", 1)
    return cloze_text


def _store_audio_clip(clip_path, filename):
    with open(clip_path, "rb") as f:
        data_b64 = base64.b64encode(f.read()).decode("ascii")
    _invoke("storeMediaFile", filename=filename, data=data_b64)


def add_cards(items, sliced_audio_paths=None):
    """
    items: همون لیستی که به anki_export.build_apkg می‌دیم.
    sliced_audio_paths: دیکشنری اختیاری {word: مسیر فایل صوتی از قبل بریده‌شده}
      اگه ندی، این تابع صدا اضافه نمی‌کنه (برای سادگی، برش صدا اینجا انجام نمی‌شه).
    خروجی: تعداد کارت‌هایی که با موفقیت اضافه شدن.
    """
    if not is_available():
        raise ConnectionError("Anki باز نیست یا AnkiConnect نصب/فعال نیست.")

    _ensure_deck()
    _ensure_model()

    added = 0
    for item in items:
        cloze_text = _make_cloze_text(item["sentence"], item["word"])
        extra_lines = [f"{item.get('meaning', '')} ({item.get('pos', '')})"]
        if item.get("forms"):
            extra_lines.append(f"صرف: {item['forms']}")
        for ex in item.get("examples", []):
            extra_lines.append(f"{ex.get('sv', '')} — {ex.get('fa', '')}")
        extra = "<br>".join(line for line in extra_lines if line.strip())

        audio_field = ""
        if sliced_audio_paths and item["word"] in sliced_audio_paths:
            clip_path = sliced_audio_paths[item["word"]]
            filename = f"svenska_{item['word']}.mp3"
            try:
                _store_audio_clip(clip_path, filename)
                audio_field = f"[sound:{filename}]"
            except Exception:
                audio_field = ""

        note = {
            "deckName": DECK_NAME,
            "modelName": MODEL_NAME,
            "fields": {"Text": cloze_text, "Extra": extra, "Audio": audio_field},
            "options": {"allowDuplicate": False},
            "tags": ["svenska-coach"],
        }
        try:
            _invoke("addNote", note=note)
            added += 1
        except RuntimeError:
            # احتمالاً تکراریه یا مشکل دیگه‌ای داره؛ رد شو، بقیه رو ادامه بده
            continue

    return added
