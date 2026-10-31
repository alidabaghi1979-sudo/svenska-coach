"""
مربی هوش مصنوعی سوئدی داخل اپ — پشتیبانی از هم Claude (Anthropic) هم Gemini (Google).
"""
import json
import re

import streamlit as st
from anthropic import Anthropic
from google import genai
from google.genai import types

MODEL = "claude-haiku-4-5-20251001"  # پیش‌فرض

AVAILABLE_MODELS = {
    "claude-haiku-4-5-20251001": {"provider": "anthropic", "label": "⚡ Claude Haiku (سریع/ارزون)"},
    "claude-sonnet-5": {"provider": "anthropic", "label": "⚖️ Claude Sonnet (متعادل)"},
    "claude-opus-5-5": {"provider": "anthropic", "label": "🎯 Claude Opus (بهترین کیفیت Claude)"},
    "gemini-3.1-flash-lite": {"provider": "google", "label": "⚡ Gemini Flash-Lite (سریع/ارزون)"},
    "gemini-3-flash-preview": {"provider": "google", "label": "⚖️ Gemini Flash (متعادل)"},
    "gemini-3.1-pro-preview": {"provider": "google", "label": "🎯 Gemini Pro (بهترین کیفیت Gemini)"},
}

SYSTEM_PROMPT_TEMPLATE = """تو کوچ شخصی شنیداری و مکالمه‌ی زبان سوئدی من (Ali) هستی. سطح فعلی من A2 است (هم شنیداری هم مکالمه).
همیشه به فارسی توضیح بده، مگر وقتی داریم مکالمه‌ی سوئدی تمرین می‌کنیم.
لحنت صبور و ملایمه؛ خطاها رو کوتاه و مثبت اصلاح کن، بیشتر از ۲ تا ۳ اصلاح در هر پاسخ نده تا انگیزه‌م کم نشه.

تمرکز جلسه‌ی امروز: {focus}
{work_context}
کلماتی که اخیراً یاد گرفتم (برای ارجاع و استفاده‌ی طبیعی، نه تکرار الکی):
{vocab_context}

خطاهای تکراری من که باید موقع اصلاح بهشون توجه ویژه کنی:
{mistakes_context}
{past_context}"""

# سناریوها و واژگان محیط کار (هتل، تجهیزات، شیفت، آشپزخانه) — فقط روزهایی که
# تمرکز جلسه «واژگان کاری / مصاحبه»ست به پرامپت مربی اضافه می‌شه.
WORK_SCENARIOS_FA = """
بانک سناریو و واژگان محیط کار برای نقش‌آفرینی امروز — از این‌ها به‌طور طبیعی
و متناسب با جریان مکالمه استفاده کن (نه یک‌جا ریختن همه‌شون):

🏨 هتل و پذیرش (reception):
incheckning/utcheckning (ورود/خروج مهمان)، boka ett rum (رزرو اتاق)،
Rummet är inte klart än (اتاق هنوز آماده نیست)، en klagomål (شکایت)،
Kan jag hjälpa dig med något? (کاری از دستم برمیاد؟)

🧹 نظافت و تجهیزات (städning / utrustning):
en dammsugare (جاروبرقی)، byta lakan (تعویض ملحفه)، utrustningen är trasig
(تجهیزات خرابه)، beställa nya förbrukningsvaror (سفارش لوازم مصرفی جدید)

🕐 مدیریت شیفت (skifthantering):
ett skiftbyte (تعویض شیفت)، schemat för nästa vecka (برنامه‌ی هفته‌ی بعد)،
Kan du ta mitt pass på lördag? (می‌تونی شیفت شنبه‌م رو بگیری؟)،
en rast (استراحت کوتاه)

🍳 عملیات آشپزخانه (köksdrift):
hygienregler (قوانین بهداشتی)، en allergi (حساسیت غذایی)، laga mat enligt
recept (طبخ طبق دستور پخت)، diska (ظرف‌شویی)، fylla på kylen (پر کردن یخچال)

مصاحبه‌ی کاری (jobbintervju):
Berätta om dig själv (خودت رو معرفی کن)، Varför vill du jobba här؟ (چرا می‌خوای
اینجا کار کنی؟)، styrkor och svagheter (نقاط قوت و ضعف)
"""


def build_system_prompt(focus, vocab_df, mistakes_df, work_day=False, past_context_df=None):
    if not vocab_df.empty and "کلمه" in vocab_df.columns:
        vocab_lines = "، ".join(vocab_df["کلمه"].astype(str).tail(15).tolist())
    else:
        vocab_lines = "هنوز کلمه‌ای ثبت نشده"

    if not mistakes_df.empty and {"نوع_خطا", "غلط", "درست"}.issubset(mistakes_df.columns):
        mistakes_lines = "\n".join(
            f"- {row['نوع_خطا']}: به‌جای «{row['غلط']}» باید «{row['درست']}»"
            for _, row in mistakes_df.tail(10).iterrows()
        )
    else:
        mistakes_lines = "هنوز خطایی ثبت نشده"

    work_context = WORK_SCENARIOS_FA if work_day else ""
    past_context = format_past_context(past_context_df)

    return SYSTEM_PROMPT_TEMPLATE.format(
        focus=focus, work_context=work_context,
        vocab_context=vocab_lines, mistakes_context=mistakes_lines,
        past_context=past_context,
    )


def format_past_context(past_context_df, max_rows=16):
    """
    آخرین رد و بدل‌های گفتگوی مربی (از تب coach_log) رو به یه بلوک خلاصه‌ی متنی
    تبدیل می‌کنه تا مربی از جلسه‌های قبلی خبر داشته باشه (حافظه‌ی بلندمدت).
    """
    if past_context_df is None or past_context_df.empty:
        return ""
    tail = past_context_df.tail(max_rows)
    lines = []
    for _, row in tail.iterrows():
        role = "من" if str(row.get("نقش", "")) == "user" else "مربی"
        text = str(row.get("پیام", "")).strip()
        if text:
            lines.append(f"- {role}: {text}")
    if not lines:
        return ""
    return (
        "\nخلاصه‌ی آخرین گفتگوهامون تو جلسه‌های قبلی:\n" + "\n".join(lines) + "\n"
        "⚠️ مهم: این خلاصه رو واقعاً بخون و بهش توجه کن. اگه می‌بینی قبلاً یه تمرین، "
        "نقش‌آفرینی یا موضوع خاصی رو با هم کار کردیم، دقیقاً همون‌ رو از اول پیشنهاد نده — "
        "یا جلوتر ببرش (سخت‌ترش کن، یه چرخش جدید بهش بده)، یا سراغ یه کلمه/گرامر/سناریوی "
        "متفاوت برو. تکرار عین همون تمرین قبلی حوصله‌م رو سر می‌بره.\n"
    )


@st.cache_resource
def get_anthropic_client():
    return Anthropic(api_key=st.secrets["claude"]["api_key"])


def translate_word(word):
    """ترجمه و تحلیل سریع یه کلمه/عبارت سوئدی (برای افزودن دستی به بانک کلمات)."""
    client = get_anthropic_client()
    prompt = (
        f'کلمه یا عبارت زیر رو تحلیل کن: "{word}"\n'
        "(ممکنه سوئدی باشه یا فارسی؛ اگه فارسی بود، معادل سوئدی‌اش رو پیدا کن و کل تحلیل رو برای همون کلمه‌ی سوئدی بده.)\n"
        "فقط یک JSON خام (بدون ```‌ و بدون توضیح اضافه) با دقیقاً این کلیدها برگردون:\n"
        '{"word": "شکل استاندارد به‌همراه فرم‌های صرفی اگه فعل یا اسم باشه، مثل '
        '\'boka (bokar, bokade, bokat)\' یا \'en bil (bilar)\'، وگرنه خودِ کلمه", '
        '"translation_fa": "معنی فارسیِ کوتاه", '
        '"word_class": "یکی از: substantiv, verb, adjektiv, fras", '
        '"example_sentence_sv": "یک جمله‌ی ساده‌ی سوئدی با همین کلمه", '
        '"example_sentence_fa": "ترجمه‌ی فارسیِ همون جمله"}'
    )
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    text_blocks = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
    text = "".join(text_blocks).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    return json.loads(text)


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=st.secrets["gemini"]["api_key"])


def ask_coach(chat_history, system_prompt, model=None):
    """chat_history: لیستی از {"role": "user"/"assistant", "content": "..."}"""
    model = model or MODEL
    provider = AVAILABLE_MODELS.get(model, {}).get("provider", "anthropic")

    if provider == "google":
        client = get_gemini_client()
        contents = [
            {
                "role": "model" if m["role"] == "assistant" else "user",
                "parts": [{"text": m["content"]}],
            }
            for m in chat_history
        ]
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt, max_output_tokens=1000
            ),
        )
        return response.text

    # پیش‌فرض: Anthropic
    client = get_anthropic_client()
    api_messages = [{"role": m["role"], "content": m["content"]} for m in chat_history]
    response = client.messages.create(
        model=model,
        max_tokens=1000,
        system=system_prompt,
        messages=api_messages,
    )
    text_blocks = [b.text for b in response.content if getattr(b, "type", None) == "text"]
    return "".join(text_blocks) if text_blocks else ""


# ---------------- تشخیص و ثبت خودکار خطاهای گرامری ----------------
_LATIN_WORDS = re.compile(r"[A-Za-zÅÄÖåäöÉé]{2,}")
MISTAKE_TYPES = ["گرامر", "حرف اضافه", "ترتیب کلمات", "املا", "واژگان"]


def extract_mistakes(user_text, prev_assistant=""):
    """
    جمله‌های سوئدیِ پیام کاربر رو بررسی می‌کنه و خطاهای واقعی رو برمی‌گردونه:
    [{"type": ..., "wrong": ..., "right": ...}]. برای پیام‌های فارسی یا بی‌خطا لیست خالیه.
    با Claude Haiku (ارزون) انجام می‌شه؛ هر خطایی تو این مرحله چت رو خراب نمی‌کنه.
    """
    if len(_LATIN_WORDS.findall(user_text or "")) < 2:
        return []
    client = get_anthropic_client()
    prompt = (
        "تو یه معلم سوئدی هستی. متن زیر پیامیه که یه زبان‌آموز فارسی‌زبان (سطح A2) تو چت نوشته. "
        "فقط بخش‌های سوئدی رو بررسی کن (فارسی رو نادیده بگیر).\n"
        + (f"پیام قبلی مربی (فقط برای فهمیدن زمینه): {prev_assistant[:600]}\n" if prev_assistant else "")
        + f'\nپیام زبان‌آموز:\n"""{user_text[:1200]}"""\n\n'
        "فقط خطاهای واقعی گرامری، حرف اضافه، ترتیب کلمات، املا یا انتخاب واژه رو پیدا کن. "
        "غلط‌های تایپی جزئی، نقطه‌گذاری و حروف بزرگ/کوچک رو نادیده بگیر. حداکثر ۳ خطا، مهم‌ترینا. "
        "اگه خطایی نیست لیست خالی بده. فقط یک JSON خام (بدون ``` و بدون توضیح) با این شکل برگردون:\n"
        '{"mistakes": [{"type": "یکی از: ' + "، ".join(MISTAKE_TYPES) + '", '
        '"wrong": "بخش کوتاه غلط دقیقاً از متن (عبارت یا جمله‌ی کوتاه)", '
        '"right": "شکل درست همون بخش"}]}'
    )
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001", max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    items = json.loads(text).get("mistakes", [])
    out = []
    for m in items[:3]:
        wrong = str(m.get("wrong", "")).strip()
        right = str(m.get("right", "")).strip()
        kind = str(m.get("type", "")).strip()
        if wrong and right and wrong.lower() != right.lower():
            out.append({"type": kind if kind in MISTAKE_TYPES else "گرامر", "wrong": wrong, "right": right})
    return out


def log_mistakes(sh, mistakes, today):
    """به تب mina_fel اضافه می‌کنه؛ اگه همون خطا (غلط+درست) قبلاً ثبت شده، فقط «تعداد» رو یکی زیاد می‌کنه."""
    df = sh.read_tab("mina_fel")
    for m in mistakes:
        count = None
        if not df.empty and {"غلط", "درست", "تعداد"}.issubset(df.columns):
            hit = df[(df["غلط"].astype(str) == m["wrong"]) & (df["درست"].astype(str) == m["right"])]
            if not hit.empty:
                try:
                    count = int(float(hit.iloc[0]["تعداد"]))
                except (ValueError, TypeError):
                    count = 1
        if count is not None:
            sh.update_cells_by_match("mina_fel", "غلط", m["wrong"], {"تعداد": count + 1})
        else:
            sh.append_row("mina_fel", [today, m["type"], m["wrong"], m["right"], 1])



# ---------------- تماس مقاوم با Gemini: تلاش مجدد + مدل جایگزین ----------------
FALLBACK_MODEL = "gemini-3.1-flash-lite"


def gemini_generate(model, contents, config, fallback=FALLBACK_MODEL, retries=3):
    """
    generate_content با تلاش مجدد روی خطای شلوغی (503/500/UNAVAILABLE) و در آخر مدل جایگزین.
    خطای تموم‌شدن سهمیه (429) بدون انتظار مستقیم می‌ره سراغ مدل جایگزین.
    اگه همه شکست بخورن، یه پیام فارسی ساده می‌ده.
    """
    import time
    client = get_gemini_client()
    last = None
    for mdl in [model] + ([fallback] if fallback and fallback != model else []):
        for attempt in range(retries):
            try:
                return client.models.generate_content(model=mdl, contents=contents, config=config)
            except Exception as exc:  # noqa: BLE001
                last = exc
                msg = str(exc)
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    break  # سهمیه‌ی همین مدل تموم شده؛ مدل بعدی
                if any(k in msg for k in ("503", "500", "UNAVAILABLE", "INTERNAL", "overloaded", "high demand")):
                    time.sleep(2 * (attempt + 1))
                    continue
                raise  # خطای دیگه (مثلاً ورودی نامعتبر): همون رو نشون بده
    msg = str(last)
    if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
        raise RuntimeError("سهمیه‌ی Gemini تموم شده — چند ساعت بعد (یا فردا) دوباره امتحان کن.") from last
    raise RuntimeError("سرور Gemini الان شلوغه — چند دقیقه بعد دوباره امتحان کن.") from last


# ---------------- ورودی صوتی: صدا → متن با Gemini ----------------
TRANSCRIBE_MODEL = "gemini-3-flash-preview"


def transcribe_audio(audio_bytes, mime_type="audio/wav"):
    """
    صدای ضبط‌شده (احتمالاً سوئدی، گاهی با کلمه‌های فارسی) رو به متن تبدیل می‌کنه.
    فقط خودِ متن رو برمی‌گردونه؛ اگه چیزی شنیده نشه، رشته‌ی خالی.
    """
    prompt = (
        "این یه ضبط صوتی کوتاه از یه زبان‌آموز فارسی‌زبانه که سوئدی صحبت می‌کنه "
        "(ممکنه چند کلمه‌ی فارسی هم وسطش باشه). دقیقاً همون چیزی که گفته شده رو "
        "کلمه‌به‌کلمه بنویس — غلط‌های گرامری گوینده رو اصلاح نکن. سوئدی رو با الفبای لاتین "
        "و فارسی رو با الفبای فارسی بنویس. فقط متن رو برگردون، بدون توضیح و بدون گیومه. "
        "اگه صدای قابل‌فهمی نیست، رشته‌ی خالی برگردون."
    )
    resp = gemini_generate(
        TRANSCRIBE_MODEL,
        [types.Part.from_bytes(data=audio_bytes, mime_type=mime_type), prompt],
        types.GenerateContentConfig(max_output_tokens=500),
    )
    return (resp.text or "").strip().strip('"')


# ---------------- اسکن سند: عکس نامه/متن → خواندن + ترجمه ----------------
DOC_MODEL = "gemini-3-flash-preview"
MAX_IMAGE_SIDE = 2000


def prepare_image(raw, mime_type="image/jpeg"):
    """
    عکس گوشی رو برای ارسال آماده می‌کنه: چرخش درست (EXIF)، کوچیک‌کردن تا ~۲۰۰۰ پیکسل،
    و تبدیل به JPEG. اگه Pillow نصب نباشه، همون عکس اصلی برمی‌گرده.
    خروجی: (bytes, mime_type)
    """
    try:
        import io
        from PIL import Image, ImageOps
    except ImportError:
        return raw, mime_type or "image/jpeg"
    try:
        img = Image.open(io.BytesIO(raw))
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return raw, mime_type or "image/jpeg"


DOC_PROMPT = """این یک یا چند عکس از یک نامه/سند/برگه/تابلو به زبان سوئدیه (صفحه‌ها به ترتیب‌ان). 
متن رو با دقت بخون و فقط یک JSON خام (بدون ```) با دقیقاً این کلیدها برگردون:
{
 "title": "عنوان کوتاه فارسی یا سوئدی برای سند (مثلاً «نامه‌ی Skatteverket درباره‌ی تغییر آدرس»)",
 "doc_type": "نوع سند به فارسی (نامه‌ی رسمی، قبض، قرارداد، آگهی، منو، تابلو، ...)",
 "sender": "فرستنده/سازمان اگه مشخصه، وگرنه رشته‌ی خالی",
 "swedish_text": "متن کامل و دقیق سوئدی، با همون ترتیب و پاراگراف‌بندی (خط جدید = \\n)",
 "translation_fa": "ترجمه‌ی روان و دقیق فارسی کل متن، پاراگراف به پاراگراف",
 "key_points": ["۳ تا ۶ نکته‌ی مهم به فارسی"],
 "deadlines": [{"what": "کاری که باید بشه یا مبلغ/موضوع (فارسی)", "when": "مهلت یا تاریخ دقیق از متن"}],
 "vocabulary": [{"word": "کلمه یا عبارت مهم سوئدی (شکل پایه + فرم‌های صرفی اگه فعل/اسمه، مثل 'boka (bokar, bokade, bokat)' یا 'en bil (bilar)')", "translation_fa": "معنی کوتاه فارسی", "word_class": "substantiv/verb/adjektiv/fras", "example_sentence_sv": "جمله‌ی نمونه از خود سند (یا ساده‌شده‌اش)", "example_sentence_fa": "ترجمه‌ی جمله"}],
 "warnings": ["هشدار اگه چیزی ناخوانا بود یا مطمئن نیستی، وگرنه لیست خالی"]
}
قوانین:
- vocabulary: ۸ تا ۱۵ کلمه‌ی مفیدِ سطح A2–B1 (کلمه‌های خیلی ساده یا اسم‌های خاص نیاد).
- اطلاعات شخصی رو تو *همه‌ی* فیلدها با ••• جایگزین کن: شماره‌ی شخصی (personnummer)، شماره‌ی حساب/کارت/OCR/پرداخت، رمزها، نام و آدرس گیرنده (کل بلوک آدرس: c/o، خیابان، کد پستی و شهرِ گیرنده)، شماره‌تلفن و ایمیل. ولی نام سازمان‌ها، آدرس سازمان‌ها (مثلاً جایی که باید مدارک رو بفرستم)، تاریخ‌ها و مبلغ‌ها بمونن.
- اگه بخشی ناخوانا بود حدس نزن؛ بنویس [ناخوانا] و تو warnings بیار.
- فقط JSON برگردون."""


def read_document(images):
    """
    images: لیستی از (bytes, mime_type). عکس‌ها رو با Gemini می‌خونه و ترجمه می‌کنه.
    خروجی: دیکشنری با کلیدهای title, doc_type, sender, swedish_text, translation_fa,
    key_points, deadlines, vocabulary, warnings.
    """
    parts = []
    for raw, mime in images:
        data, mt = prepare_image(raw, mime)
        parts.append(types.Part.from_bytes(data=data, mime_type=mt))
    parts.append(DOC_PROMPT)
    resp = gemini_generate(
        DOC_MODEL, parts,
        types.GenerateContentConfig(response_mime_type="application/json", max_output_tokens=8000),
    )
    text = (resp.text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    doc = json.loads(text)
    for k in ("key_points", "deadlines", "vocabulary", "warnings"):
        if not isinstance(doc.get(k), list):
            doc[k] = []
    return mask_doc(doc)


# --- پوشاندن اطلاعات شخصی (شبکه‌ی ایمنی روی خروجی مدل؛ قبل از نمایش و ذخیره) ---
_DIG = "[0-9\u06f0-\u06f9]"  # رقم انگلیسی یا فارسی
_MASK_PATTERNS = [
    re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),  # ایمیل
    re.compile(r"(?im)^(\s*c/o\s+).+$"),  # خط «c/o نام»
    re.compile(r"(نزد\s*:\s*)[^\n]+"),  # «نزد: نام» تو ترجمه
    re.compile(rf"(?<!{_DIG})(?:{_DIG}{{6}}|{_DIG}{{8}})[-+]?{_DIG}{{4}}(?!{_DIG})"),  # شماره‌ی شخصی
    re.compile(rf"(?<!{_DIG})(?:\+46[ \-]?|[0\u06f0]){_DIG}(?:[ \-]?{_DIG}){{6,10}}(?!{_DIG})"),  # تلفن
]


def mask_sensitive(text):
    out = str(text or "")
    for pat in _MASK_PATTERNS:
        if pat.groups:
            out = pat.sub(lambda m: m.group(1) + "•••", out)
        else:
            out = pat.sub("•••", out)
    return out


def mask_doc(doc):
    for k in ("title", "sender", "swedish_text", "translation_fa"):
        if k in doc:
            doc[k] = mask_sensitive(doc[k])
    doc["key_points"] = [mask_sensitive(p) for p in doc.get("key_points", [])]
    for d in doc.get("deadlines", []):
        if isinstance(d, dict):
            d["what"] = mask_sensitive(d.get("what", ""))
            d["when"] = mask_sensitive(d.get("when", ""))
    for v in doc.get("vocabulary", []):
        if isinstance(v, dict):
            for k in ("example_sentence_sv", "example_sentence_fa"):
                if k in v:
                    v[k] = mask_sensitive(v[k])
    return doc


# --- ذخیره‌ی سند تو شیت (تب dokument) و حافظه‌ی مربی ---
_CELL_LIMIT = 45000  # سقف سلول گوگل‌شیت ۵۰هزار کاراکتره


def doc_to_row(doc, doc_id, today):
    j = lambda x: json.dumps(x, ensure_ascii=False)
    return [
        doc_id, today, str(doc.get("title", ""))[:200], str(doc.get("doc_type", ""))[:100],
        str(doc.get("sender", ""))[:100],
        str(doc.get("swedish_text", ""))[:_CELL_LIMIT], str(doc.get("translation_fa", ""))[:_CELL_LIMIT],
        j(doc.get("key_points", []))[:_CELL_LIMIT], j(doc.get("deadlines", []))[:_CELL_LIMIT],
        j(doc.get("vocabulary", []))[:_CELL_LIMIT],
    ]


def _loads(raw):
    try:
        v = json.loads(raw) if raw else []
        return v if isinstance(v, list) else []
    except Exception:
        return []


def row_to_doc(row):
    return {
        "id": row.get("شناسه", ""),
        "title": row.get("عنوان", ""), "doc_type": row.get("نوع", ""), "sender": row.get("فرستنده", ""),
        "swedish_text": row.get("متن_سوئدی", ""), "translation_fa": row.get("ترجمه_فارسی", ""),
        "key_points": _loads(row.get("نکات")), "deadlines": _loads(row.get("مهلت‌ها")),
        "vocabulary": _loads(row.get("واژه‌ها")), "warnings": [],
    }


def next_doc_id(docs_df):
    try:
        ids = [int(x) for x in docs_df["شناسه"] if str(x).strip().isdigit()]
        return (max(ids) + 1) if ids else 1
    except Exception:
        return 1


def document_context(active_doc, docs_df, recent=5):
    """بلوکی برای system prompt مربی: اسناد اخیر (خلاصه) + سند فعالِ این جلسه (کامل)."""
    parts = []
    if docs_df is not None and not docs_df.empty and "عنوان" in docs_df.columns:
        lines = []
        for _, r in docs_df.tail(recent).iterrows():
            pts = "؛ ".join(str(p) for p in _loads(r.get("نکات"))[:3])
            lines.append(f"- ({r.get('تاریخ', '')}) {r.get('عنوان', '')} [{r.get('نوع', '')}]: {pts}")
        parts.append("\nاسناد/نامه‌های سوئدی که اخیراً اسکن کردم (خلاصه):\n" + "\n".join(lines))
    if active_doc:
        parts.append(
            "\nسند فعال این جلسه — اگه درباره‌ش سؤال پرسیدم، از همین متن جواب بده؛ برای تمرین، "
            "از همین متن و واژه‌هاش سؤال و مکالمه بساز. ترجمه کمکیه؛ درباره‌ی مهلت‌ها و مبلغ‌ها "
            "همیشه یادآوری کن با متن اصلی چک کنم.\n"
            f"عنوان: {active_doc.get('title', '')}\n"
            f"متن سوئدی:\n{str(active_doc.get('swedish_text', ''))[:6000]}\n"
            f"ترجمه:\n{str(active_doc.get('translation_fa', ''))[:6000]}\n"
        )
    return "\n".join(parts)


def format_document_md(doc):
    """سند خوانده‌شده رو به یک پیام مارک‌داون خوانا برای چت تبدیل می‌کنه."""
    out = [f"### 📄 {doc.get('title') or 'سند'}"]
    meta = " · ".join(x for x in [doc.get("doc_type"), doc.get("sender")] if x)
    if meta:
        out.append(f"*{meta}*")
    if doc.get("deadlines"):
        out.append("**⏰ مهلت‌ها / کارهای لازم:**\n" + "\n".join(
            f"- {d.get('what', '')} — **{d.get('when', '')}**" for d in doc["deadlines"]))
    if doc.get("key_points"):
        out.append("**نکات مهم:**\n" + "\n".join(f"- {p}" for p in doc["key_points"]))
    out.append("**ترجمه:**\n\n" + str(doc.get("translation_fa", "")))
    out.append("**متن سوئدی:**\n\n" + str(doc.get("swedish_text", "")))
    if doc.get("vocabulary"):
        out.append("**واژه‌های کلیدی:**\n" + "\n".join(
            f"- **{v.get('word', '')}** — {v.get('translation_fa', '')}" for v in doc["vocabulary"]))
    if doc.get("warnings"):
        out.append("⚠️ " + " · ".join(doc["warnings"]))
    out.append("_ترجمه‌ی کمکیه؛ برای نامه‌های مهم (مالیات، بیمه، مهاجرت، قرارداد) مهلت‌ها و مبلغ‌ها رو با متن اصلی چک کن._")
    return "\n\n".join(out)


# ---------------- تمرین از روی سند + افزودن واژه‌ها به Ordbank ----------------
DOC_EXERCISE_PROMPT = """بر اساس متن سوئدی سند زیر برای یک زبان‌آموز فارسی‌زبان (سطح A2–B1) تمرین بساز و فقط یک JSON خام (بدون ```) با این کلیدها برگردون:
{{
 "grammar": [{{"sentence_sv": "جمله‌ی سوئدی از متن (یا الهام‌گرفته از آن) با یک جای خالی ___", "options": ["۴ گزینه‌ی سوئدی"], "correct_index": 0, "explanation_fa": "توضیح کوتاه فارسی چرا این گزینه درسته"}}],
 "comprehension": [{{"question_sv": "سؤال ساده‌ی سوئدی درباره‌ی محتوای سند", "options": ["۴ گزینه‌ی ساده‌ی سوئدی"], "correct_index": 0, "explanation_fa": "توضیح کوتاه فارسی با اشاره به بخش مرتبط متن"}}]
}}
قوانین:
- دقیقاً {n_grammar} سؤال گرامر (صرف فعل، حرف اضافه، en/ett، شکل معرفه، ترتیب کلمات، ... از همون چیزی که تو متن هست) و دقیقاً {n_comp} سؤال درک مطلب.
- هر سؤال دقیقاً ۴ گزینه دارد و فقط یکی کاملاً درست است؛ گزینه‌های غلط باید قابل قبول ولی قطعاً غلط باشند.
- correct_index شماره‌ی گزینه‌ی درست (۰ تا ۳).
- فقط از اطلاعات خود سند استفاده کن، اطلاعات شخصی (••• ) رو تو سؤال‌ها نیار.
- فقط JSON برگردون.

عنوان سند: {title}
متن سوئدی:
{text}
"""


def _shuffle_question(q):
    """گزینه‌ها رو بُر می‌زنه و correct_index رو درست نگه می‌داره؛ اگه سؤال معیوبه None."""
    import random
    opts = q.get("options")
    ci = q.get("correct_index")
    if not isinstance(opts, list) or len(opts) != 4 or not isinstance(ci, int) or not 0 <= ci < 4:
        return None
    if len({str(o).strip() for o in opts}) != 4:
        return None
    right = opts[ci]
    shuffled = opts[:]
    random.shuffle(shuffled)
    q = dict(q)
    q["options"] = shuffled
    q["correct_index"] = shuffled.index(right)
    return q


def make_doc_exercises(doc, n_grammar=6, n_comp=5):
    """
    تمرین گرامر/درک مطلب/واژگان از روی سند. خروجی: دیکشنری با کلیدهای grammar, comprehension, vocab
    (همون قالب تب «exercises» / exercise_view). واژگان از لیست واژه‌های سند ساخته می‌شه.
    """
    import random
    prompt = DOC_EXERCISE_PROMPT.format(
        n_grammar=n_grammar, n_comp=n_comp, title=doc.get("title", ""),
        text=str(doc.get("swedish_text", ""))[:8000],
    )
    resp = gemini_generate(
        DOC_MODEL, [prompt],
        types.GenerateContentConfig(response_mime_type="application/json", max_output_tokens=6000),
    )
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", (resp.text or "").strip())
    data = json.loads(text)
    grammar = [q for q in (_shuffle_question(x) for x in data.get("grammar", []) if isinstance(x, dict)) if q]
    comp = [q for q in (_shuffle_question(x) for x in data.get("comprehension", []) if isinstance(x, dict)) if q]

    vocab, words = [], [v for v in doc.get("vocabulary", []) if isinstance(v, dict) and v.get("word") and v.get("translation_fa")]
    for v in words:
        others = list({w["translation_fa"] for w in words if w["translation_fa"] != v["translation_fa"]})
        if len(others) < 3:
            continue
        opts = random.sample(others, 3) + [v["translation_fa"]]
        random.shuffle(opts)
        vocab.append({"word_sv": v["word"], "options": opts, "correct_index": opts.index(v["translation_fa"])})
    if not grammar and not comp:
        raise ValueError("مدل تمرین معتبری نساخت")
    return {"grammar": grammar, "comprehension": comp, "vocab": vocab}


def doc_vocab_rows(doc, today, existing_words):
    """ردیف‌های Ordbank از واژه‌های سند (بدون تکراری‌ها). existing_words: مجموعه‌ی نرمال‌شده."""
    import srs
    rows, seen = [], set(existing_words)
    for v in doc.get("vocabulary", []):
        if not isinstance(v, dict) or not v.get("word"):
            continue
        key = srs.normalize_word_answer(v["word"])
        if not key or key in seen:
            continue
        seen.add(key)
        sv, fa = v.get("example_sentence_sv", ""), v.get("example_sentence_fa", "")
        sentence = f"{sv}\n{fa}\n(سند: {doc.get('title', '')[:40]})"
        practice = json.dumps([sv], ensure_ascii=False) if sv else ""
        rows.append([today, v["word"], f"{v.get('translation_fa', '')} ({v.get('word_class', '')})",
                     sentence, 0, "", practice])
    return rows
