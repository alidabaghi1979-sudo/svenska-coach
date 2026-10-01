"""
تب «🎧 شنیداری» — تمرین‌های شنیداریِ Rivstart A1+A2 (Hörförståelsetexter).
داده‌ها تو horforstaelse.py هستن (۹۷ آیتم، فصل‌های ۱ تا ۲۰).
"""
import html

import streamlit as st

import word_audio
from horforstaelse import LISTENING_ITEMS

CHAPTERS = sorted(set(it["chapter"] for it in LISTENING_ITEMS))


def _items_for_chapter(chapter):
    return [it for it in LISTENING_ITEMS if it["chapter"] == chapter]


def render(sh=None):
    st.subheader("🎧 تمرین شنیداری (Rivstart A1+A2)")
    st.caption(
        "اول فقط گوش بده و سعی کن بفهمی، بعد متن رو نشون بده و مقایسه کن. "
        "۹۷ تمرین از ۱۹ فصل کتاب."
    )

    if not word_audio.tts_available():
        st.warning("🔇 کلید Azure TTS تنظیم نشده، صدا در دسترس نیست.")

    chosen_chapter = st.selectbox(
        "فصل:", CHAPTERS, format_func=lambda c: f"فصل {c}", key="listening_chapter"
    )
    items = _items_for_chapter(chosen_chapter)

    state_key = f"listening_idx_{chosen_chapter}"
    if state_key not in st.session_state or st.session_state[state_key] >= len(items):
        st.session_state[state_key] = 0
    idx = st.session_state[state_key]
    item = items[idx]

    st.caption(f"تمرین {idx + 1} از {len(items)} این فصل — {item['exercise']}")

    lines = tuple((sp, tx) for sp, tx in item["lines"] if str(tx).strip())
    audio_bytes = word_audio.synth_dialog(lines) if len(lines) > 1 else (
        word_audio.synth_swedish(lines[0][1]) if lines else None
    )
    if audio_bytes:
        st.audio(audio_bytes, format="audio/mp3")
    elif word_audio.tts_available():
        st.caption("🔇 ساخت صدا برای این تمرین شکست خورد.")

    with st.expander("🔍 نشون بده (متن کامل)"):
        parts = []
        for sp, tx in item["lines"]:
            tx = str(tx).strip()
            if not tx:
                if sp:
                    parts.append(f"<p dir='rtl'><i>{html.escape(sp)}</i></p>")
                continue
            if sp and not sp.startswith("["):
                parts.append(f"<p dir='ltr'><b>{html.escape(sp)}:</b> {html.escape(tx)}</p>")
            elif sp:
                parts.append(f"<p dir='ltr'><i>{html.escape(sp)}</i><br>{html.escape(tx)}</p>")
            else:
                parts.append(f"<p dir='ltr'>{html.escape(tx)}</p>")
        st.markdown("".join(parts), unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➡️ تمرین بعدی", key=f"listening_next_{chosen_chapter}"):
            st.session_state[state_key] = (idx + 1) % len(items)
            st.rerun()
    with col2:
        if st.button("🔀 یکی تصادفی", key=f"listening_random_{chosen_chapter}"):
            import random
            st.session_state[state_key] = random.randrange(len(items))
            st.rerun()
