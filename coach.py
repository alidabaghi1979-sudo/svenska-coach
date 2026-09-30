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
    return "\nخلاصه‌ی آخرین گفتگوهامون تو جلسه‌های قبلی (برای تداوم، نه تکرار):\n" + "\n".join(lines) + "\n"


@st.cache_resource
def get_anthropic_client():
    return Anthropic(api_key=st.secrets["claude"]["api_key"])


def translate_word(word):
    """ترجمه و تحلیل سریع یه کلمه/عبارت سوئدی (برای افزودن دستی به بانک کلمات)."""
    client = get_anthropic_client()
    prompt = (
        f'کلمه یا عبارت سوئدی زیر رو تحلیل کن: "{word}"\n'
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
