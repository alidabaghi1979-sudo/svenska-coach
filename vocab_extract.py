"""
گرفتن معنی و جزئیات کلمات سوئدی با Claude API:
- batch_lookup_meanings: معنی کوتاه خیلی از کلمات با هم (برای تولتیپ هاور)
- batch_lookup_details: معنی کامل + نوع کلمه + صرف فعل + چند مثال (برای کلمات انتخاب‌شده)
"""
import json

import streamlit as st
from anthropic import Anthropic

MODEL = "claude-haiku-4-5-20251001"

MEANING_BATCH_PROMPT = """این کلمه‌های سوئدی از یه متن اومدن. برای هرکدوم دو مورد بده:
- meaning: معنی فارسی خیلی کوتاه (حداکثر ۳ کلمه)
- level: سطح تقریبی CEFR این کلمه، دقیقاً یکی از این مقادیر: A1, A2, B1, B2, C1

متن: {context}

کلمات: {word_list}

فقط یه شیء JSON معتبر برگردون، کلید = دقیقاً خود کلمه (عیناً همونی که داده شده)، مقدار = یه شیء
با دو کلید meaning و level. مثال یک ورودی: "resa": {{"meaning": "سفر", "level": "A1"}}
بدون هیچ متن اضافه، بدون ```، فقط خود JSON."""

DETAIL_BATCH_PROMPT = """این کلمه‌های سوئدی، هرکدوم تو یه جمله اومدن. برای هرکدوم این اطلاعات رو بده:
- word: دقیقاً همون کلمه‌ی ورودی
- meaning: معنی فارسی کوتاه (حداکثر ۴ کلمه) دقیقاً تو همین جمله
- pos: نوع کلمه به فارسی (اسم / فعل / صفت / قید / حرف اضافه / ضمیر / حرف ربط)
- forms: اگه فعله، صرف اصلیش با فرمت "مصدر / حال / گذشته / سوپین"؛ برای بقیه‌ی انواع رشته‌ی خالی ""
- examples: دقیقاً ۲ جمله‌ی مثال دیگه (متفاوت از جمله‌ی داده‌شده) که همین کلمه توشونه، هرکدوم با ترجمه‌ی فارسی

ورودی:
{items}

فقط یه آرایه‌ی JSON معتبر برگردون، دقیقاً با این ساختار، بدون هیچ متن اضافه و بدون ```:
[{{"word": "...", "meaning": "...", "pos": "...", "forms": "...", "examples": [{{"sv": "...", "fa": "..."}}, {{"sv": "...", "fa": "..."}}]}}]"""


def _strip_code_fence(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    return text.strip()


def _extract_json(text, open_char, close_char):
    """اگه parse مستقیم شکست خورد، بین اولین و آخرین براکت رو جدا می‌کنه."""
    start = text.find(open_char)
    end = text.rfind(close_char)
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


@st.cache_resource
def get_client():
    return Anthropic(api_key=st.secrets["claude"]["api_key"])


def batch_lookup_meanings(words, context_text):
    """برای تولتیپ هاور: دیکشنری {کلمه: {"meaning":.., "level":..}} برای یه لیست کلمه."""
    if not words:
        return {}
    client = get_client()
    # سقف تعداد کلمه در هر درخواست، تا پاسخ JSON قطع نشه (صوت‌های طولانی می‌تونن ۱۰۰+ کلمه‌ی یکتا داشته باشن)
    words = words[:60]
    word_list = "، ".join(words)
    prompt = MEANING_BATCH_PROMPT.format(context=(context_text or "")[:3000], word_list=word_list)
    response = client.messages.create(
        model=MODEL, max_tokens=4000, messages=[{"role": "user", "content": prompt}]
    )
    text = _strip_code_fence(response.content[0].text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return _extract_json(text, "{", "}") or {}


def batch_lookup_details(word_sentence_pairs):
    """برای کلمات انتخاب‌شده: معنی + نوع کلمه + صرف + دو مثال دیگه."""
    if not word_sentence_pairs:
        return []
    items = "\n".join(f'- کلمه: "{w}" — جمله: "{s}"' for w, s in word_sentence_pairs)
    client = get_client()
    prompt = DETAIL_BATCH_PROMPT.format(items=items)
    response = client.messages.create(
        model=MODEL, max_tokens=1800, messages=[{"role": "user", "content": prompt}]
    )
    text = _strip_code_fence(response.content[0].text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return _extract_json(text, "[", "]") or []
