"""
منطق مرور فاصله‌دار (SRS) به روش جعبه‌ی لایتنر.
سطح ۰ تا ۶؛ هر سطح یه فاصله‌ی مرور مشخص داره.
"""
import datetime

LEITNER_INTERVALS = {0: 1, 1: 3, 2: 7, 3: 14, 4: 30, 5: 60, 6: 120}
MAX_LEVEL = 6
KNOWN_LEVEL = 5  # دکمه‌ی «این رو بلدم»
SESSION_LIMIT = 20
NEW_PER_SESSION = 10


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


def select_session(due_df, limit=SESSION_LIMIT, new_limit=NEW_PER_SESSION, skip=()):
    """
    از بین کلمات موعددار، یه دسته‌ی محدود انتخاب می‌کنه:
    اول عقب‌افتاده‌ترین و کم‌سطح‌ترین‌ها، بعد (تا سقف new_limit) کلمه‌های جدید.
    skip: کلمه‌هایی که تو همین نشست مرور شدن (برای جلوگیری از تکرار بخاطر کش شیت).
    """
    if due_df.empty:
        return due_df
    df = due_df[~due_df["کلمه"].isin(list(skip))].copy() if len(skip) else due_df.copy()
    if df.empty:
        return df
    raw = df["مرور_بعدی"].astype(str).str.strip() if "مرور_بعدی" in df.columns else None
    is_new = raw.eq("") if raw is not None else df["کلمه"].eq("")
    df["_lvl"] = df["سطح"].apply(_parse_level) if "سطح" in df.columns else 0
    df["_date"] = raw if raw is not None else ""
    reviews = df[~is_new].sort_values(["_date", "_lvl"])
    news = df[is_new]
    new_n = min(len(news), new_limit)
    rev_n = min(len(reviews), max(limit - new_n, 0))
    new_n = min(len(news), max(limit - rev_n, new_n))
    out = pd_concat(reviews.head(rev_n), news.head(new_n))
    return out.drop(columns=["_lvl", "_date"])


def pd_concat(a, b):
    import pandas as pd
    return pd.concat([a, b])


def compute_next_review(current_level_raw, correct, known=False):
    """
    بر اساس نتیجه‌ی مرور (درست/غلط)، سطح جدید و تاریخ مرور بعدی رو حساب می‌کنه.
    خروجی: (سطح_جدید: int, تاریخ_بعدی: "YYYY-MM-DD")
    """
    level = _parse_level(current_level_raw)
    if known:
        level = max(level, KNOWN_LEVEL)
    else:
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
