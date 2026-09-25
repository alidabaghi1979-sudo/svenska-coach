"""
مربی هوش مصنوعی سوئدی داخل اپ — پشتیبانی از هم Claude (Anthropic) هم Gemini (Google).
"""
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

کلماتی که اخیراً یاد گرفتم (برای ارجاع و استفاده‌ی طبیعی، نه تکرار الکی):
{vocab_context}

خطاهای تکراری من که باید موقع اصلاح بهشون توجه ویژه کنی:
{mistakes_context}
"""


def build_system_prompt(focus, vocab_df, mistakes_df):
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

    return SYSTEM_PROMPT_TEMPLATE.format(
        focus=focus, vocab_context=vocab_lines, mistakes_context=mistakes_lines
    )


@st.cache_resource
def get_anthropic_client():
    return Anthropic(api_key=st.secrets["claude"]["api_key"])


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
    return response.content[0].text
