"""جعبه‌ی ترجمه‌ی سریع: کلمه/عبارت سوئدی یا فارسی → معنی + مثال → افزودن به ordbank."""
import datetime
import json

import streamlit as st

import coach
import srs


def render(sh):
    with st.container(border=True):
        st.markdown("**⚡ ترجمه‌ی سریع**")
        with st.form("qt_form", clear_on_submit=False):
            q = st.text_input("کلمه یا عبارت (سوئدی یا فارسی):", key="qt_input")
            go = st.form_submit_button("🔎 ترجمه کن")
        if go:
            if not q.strip():
                st.warning("چیزی ننوشتی.")
            else:
                try:
                    with st.spinner("..."):
                        st.session_state["qt_result"] = coach.translate_word(q.strip())
                except Exception as e:
                    st.session_state.pop("qt_result", None)
                    st.error(f"ترجمه شکست خورد: {e}")

        r = st.session_state.get("qt_result")
        if not r:
            return
        word = r.get("word", "")
        wc = r.get("word_class", "fras")
        st.markdown(f"### {word}")
        st.markdown(f"{r.get('translation_fa', '')}  ·  _{wc}_")
        if r.get("example_sentence_sv"):
            st.markdown(f"🔹 **{r['example_sentence_sv']}**")
            st.caption(r.get("example_sentence_fa", ""))

        try:
            df = sh.read_tab("ordbank")
            existing = (
                {srs.normalize_word_answer(w) for w in df["کلمه"] if str(w).strip()}
                if not df.empty and "کلمه" in df.columns else set()
            )
        except Exception:
            existing = set()
        if srs.normalize_word_answer(word) in existing:
            st.info("این کلمه از قبل در بانک کلمات هست.")
            return
        if st.button("➕ به بانک کلمات", key="qt_add", type="primary"):
            ex_sv = r.get("example_sentence_sv", "")
            ex_fa = r.get("example_sentence_fa", "")
            sentence = f"{ex_sv}\n{ex_fa}\n(ترجمه‌ی سریع)"
            practice = json.dumps([ex_sv], ensure_ascii=False) if ex_sv else ""
            meaning = f"{r.get('translation_fa', '')} ({wc})".strip()
            try:
                sh.append_row("ordbank", [str(datetime.date.today()), word, meaning, sentence, 0, "", practice])
                st.session_state.pop("qt_result", None)
                st.session_state["qt_added"] = word
                st.rerun()
            except Exception as e:
                st.error(f"ذخیره شکست خورد: {e}")


def show_added():
    w = st.session_state.pop("qt_added", None)
    if w:
        st.success(f"✅ «{w}» به بانک کلمات اضافه شد.")
