"""
منطق مرور فاصله‌دار (SRS) به روش جعبه‌ی لایتنر.
سطح ۰ تا ۴؛ هر سطح یه فاصله‌ی مرور مشخص داره.
"""
import datetime

LEITNER_INTERVALS = {0: 1, 1: 3, 2: 7, 3: 14, 4: 30}
MAX_LEVEL = 4


def _parse_level(raw):
    try:
        return max(0, min(int(raw), MAX_LEVEL))
    except (ValueError, TypeError):
        return 0


def _is_due(next_review_raw, today):
    if next_review_raw is None or str(next_review_raw).strip() == "":
        return True  # کلمه‌ی جدید که هنوز مرور نشده
    try:
        return datetime.datetime.strptime(str(next_review_raw), "%Y-%m-%d").date() <= today
    except ValueError:
        return True  # فرمت نامعتبر رو هم due در نظر بگیر تا کلمه گم نشه


def get_due_words(vocab_df):
    """ردیف‌هایی از بانک کلمات که امروز باید مرور بشن رو برمی‌گردونه."""
    if vocab_df.empty or "مرور_بعدی" not in vocab_df.columns:
        return vocab_df
    today = datetime.date.today()
    mask = vocab_df["مرور_بعدی"].apply(lambda v: _is_due(v, today))
    return vocab_df[mask]


def compute_next_review(current_level_raw, correct):
    """
    بر اساس نتیجه‌ی مرور (درست/غلط)، سطح جدید و تاریخ مرور بعدی رو حساب می‌کنه.
    خروجی: (سطح_جدید: int, تاریخ_بعدی: "YYYY-MM-DD")
    """
    level = _parse_level(current_level_raw)
    level = min(level + 1, MAX_LEVEL) if correct else 0
    days_ahead = LEITNER_INTERVALS[level]
    next_date = datetime.date.today() + datetime.timedelta(days=days_ahead)
    return level, next_date.isoformat()


# ─────────────────────────── حالت‌های سه‌گانه‌ی مرور ───────────────────────────
import random
import re

REVIEW_MODES = ["sv2fa", "fa2sv", "dictation"]


def pick_mode():
    """یکی از سه حالت مرور رو تصادفی انتخاب می‌کنه (برای هر کارت جداگانه)."""
    return random.choice(REVIEW_MODES)


def normalize_word_answer(raw):
    """
    برای مقایسه‌ی جواب تایپی با ستون «کلمه»: حروف بزرگ/کوچک و فاصله‌ی اضافه رو
    نادیده می‌گیره، پیشوند en/ett/att و بخش پرانتزی (صرف/جمع) رو کنار می‌ذاره،
    ولی به خود حروف å/ä/ö حساسه (چون هدف تست املاست).
    """
    s = str(raw or "").strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"^(en|ett|att)\s+", "", s)
    s = s.split("(")[0].strip()
    return s


def check_word_answer(user_input, correct_word):
    return normalize_word_answer(user_input) == normalize_word_answer(correct_word)
