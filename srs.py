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

REVIEW_MODES = ["sv2fa", "fa2sv", "dictation", "cloze", "sdict"]
WORD_MODES = ["sv2fa", "fa2sv", "dictation"]
SENTENCE_SHARE = 0.7  # سهم حالت‌های مبتنی بر جمله‌ی پنهان


def card_sentences(card):
    """جمله‌های سوئدی کارت: اول «جملات_تمرینی» (پنهان‌ها)، بعد خط اول «جمله»."""
    import json as _json
    out = []
    try:
        out = [x for x in _json.loads(card.get("جملات_تمرینی") or "[]") if x]
    except (ValueError, TypeError):
        pass
    lines = [l.strip() for l in str(card.get("جمله") or "").split("\n") if l.strip()]
    if lines and lines[0] not in out:
        out.append(lines[0])
    return out


def pick_mode(card=None):
    """
    ۷۰٪ حالت‌های مبتنی بر جمله (جای‌خالی / دیکته‌ی جمله)، ۳۰٪ حالت‌های کلمه‌ای.
    اگه کارت جمله نداشته باشه، حتماً حالت کلمه‌ای میاد.
    """
    if card is not None and card_sentences(card) and random.random() < SENTENCE_SHARE:
        if cloze_data(card) and random.random() < 0.5:
            return "cloze"
        return "sdict"
    return random.choice(WORD_MODES)


def sentence_translation(card, sentence):
    """ترجمه‌ی فارسی جمله: فقط وقتی جمله همون جمله‌ی نمونه‌ی ستون «جمله» باشه؛ وگرنه معنی کلمه."""
    lines = [l.strip() for l in str(card.get("جمله") or "").split("\n") if l.strip()]
    if len(lines) > 1 and lines[0] == sentence and not lines[1].startswith("(درس"):
        return lines[1], True
    return str(card.get("معنی") or ""), False


def normalize_sentence(text):
    t = re.sub(r"[^\w\såäöÅÄÖ]", "", str(text or "").lower())
    return re.sub(r"\s+", " ", t).strip()


def word_forms(word_field):
    """«skicka (skickar, skickade, skickat)» → ['skicka','skickar','skickade','skickat']"""
    raw = str(word_field or "").strip()
    base = normalize_word_answer(raw)
    forms = [base] if base else []
    m = re.search(r"\(([^)]*)\)", raw)
    if m:
        for part in m.group(1).split(","):
            f = re.sub(r"^(en|ett|att)\s+", "", part.strip().lower())
            if f and f not in forms:
                forms.append(f)
    # passiv/deponens: skicka → skickas, skickar → skickas ...
    forms += [f + "s" for f in list(forms) if not f.endswith("s") and f + "s" not in forms]
    return forms


def cloze_data(card):
    """
    (جمله‌ی_با_جای‌خالی, فرم‌های_درست, راهنمای_فارسی, جمله‌ی_کامل) یا None.
    جمله از «جملات_تمرینی» (یا خط اول «جمله») میاد؛ ترجمه از خط دوم «جمله» یا «معنی».
    """
    import json as _json
    forms = word_forms(card.get("کلمه", ""))
    if not forms:
        return None
    sentences = []
    try:
        sentences = [x for x in _json.loads(card.get("جملات_تمرینی") or "[]") if x]
    except (ValueError, TypeError):
        pass
    lines = [l.strip() for l in str(card.get("جمله") or "").split("\n") if l.strip()]
    if lines and lines[0] not in sentences:
        sentences.append(lines[0])
    fa_line = lines[1] if len(lines) > 1 and not lines[1].startswith("(درس") else ""
    random.shuffle(sentences)
    pattern = re.compile(
        r"(?<!\w)(" + "|".join(re.escape(f) for f in sorted(forms, key=len, reverse=True)) + r")(?!\w)",
        re.IGNORECASE,
    )
    for sent in sentences:
        if pattern.search(sent):
            # ترجمه‌ی فارسی فقط وقتی درسته که جمله همون جمله‌ی نمونه باشه
            hint = fa_line if (fa_line and lines and sent == lines[0]) else str(card.get("معنی") or "")
            return pattern.sub("_____", sent, count=1), forms, hint, sent
    return None


def check_cloze_answer(user_input, forms):
    u = normalize_word_answer(user_input)
    return any(u == normalize_word_answer(f) for f in forms)


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
