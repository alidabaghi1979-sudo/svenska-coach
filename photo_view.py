"""عکس صفحه‌ی کتاب → متن + ترجمه + کلمه‌های مهم با جمله‌ی کتاب و جمله‌های روزمره → انتخاب → Ordbank."""
import datetime
import io
import json
import re

import streamlit as st

import coach
import kort_view
import shadowing_view
import srs

MAX_SIDE = 1800
N_WORDS = 15


def _prep_image(raw):
    """کوچک‌کردن عکس (سرعت و هزینه) و تبدیل به JPEG."""
    try:
        from PIL import Image, ImageOps
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
        im.thumbnail((MAX_SIDE, MAX_SIDE))
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=88)
        return buf.getvalue()
    except Exception:
        return raw


def analyze_page(img_bytes):
    from google.genai import types
    prompt = (
        "این عکس یک صفحه از یک کتاب/متن سوئدی است و کاربر فارسی‌زبانی در سطح A2-B1 سوئدی یاد می‌گیرد.\n"
        "۱) متن سوئدی صفحه را دقیق بنویس (بدون اصلاح، پاراگراف‌ها با خط خالی).\n"
        "۲) ترجمه‌ی فارسیِ روان کل متن.\n"
        f"۳) حدود {N_WORDS} کلمه یا عبارت مفید و پرکاربرد برای یادگیری از همین متن انتخاب کن "
        "(نه کلمه‌های خیلی ساده مثل och/är/en؛ نه اسم خاص).\n"
        "فقط یک JSON خام (بدون ```) با این ساختار:\n"
        '{"text": "...", "translation_fa": "...", "words": [{'
        '"word": "شکل استاندارد: اسم با en/ett و جمع در پرانتز، فعل با صرف در پرانتز مثل \'boka (bokar, bokade, bokat)\'", '
        '"translation_fa": "معنی کوتاه در همین متن", '
        '"word_class": "substantiv|verb|adjektiv|adverb|fras", '
        '"book_sv": "همان جمله‌ی متن که کلمه در آن است", "book_fa": "ترجمه‌ی همان جمله", '
        '"daily": [{"sv": "جمله‌ی ساده‌ی روزمره (خرید، کار، پزشک، اداره، خانه) با همین کلمه، سطح A2", "fa": "ترجمه"}, '
        '{"sv": "جمله‌ی روزمره‌ی دوم، متفاوت", "fa": "ترجمه"}]}]}\n'
        "اگر عکس متن خوانا ندارد، text را خالی بگذار."
    )
    resp = coach.gemini_generate(
        coach.TRANSCRIBE_MODEL,
        [types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"), prompt],
        types.GenerateContentConfig(response_mime_type="application/json", max_output_tokens=12000),
    )
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", (resp.text or "").strip())
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", t, re.S)
        if not m:
            raise RuntimeError("پاسخ Gemini خوانا نبود؛ دوباره امتحان کن.")
        return json.loads(m.group(0))


def _row(deck, r):
    """ردیف Ordbank: جمله‌ی کتاب اول (برای مرور جمله‌ای)، جمله‌های روزمره در جملات_تمرینی."""
    wc = str(r["نوع"]).strip() or "fras"
    bsv, bfa = str(r["جمله_کتاب"]).strip(), str(r["ترجمه_کتاب"]).strip()
    daily = [(str(r[f"روزمره{i}_sv"]).strip(), str(r[f"روزمره{i}_fa"]).strip()) for i in (1, 2)]
    daily = [d for d in daily if d[0]]
    lines = [x for x in [bsv, bfa] if x]
    lines += [f"(روزمره) {sv} = {fa}" for sv, fa in daily]
    lines.append("(از عکس کتاب)")
    practice = [x for x in [bsv] + [d[0] for d in daily] if x]
    return [str(datetime.date.today()), str(r["کلمه"]).strip(),
            f"{str(r['معنی']).strip()} ({wc})", "\n".join(lines), 0, "",
            json.dumps(practice, ensure_ascii=False) if practice else "", deck]


def _send_to_reader(text):
    st.session_state["lr_text"] = text


def render(sh, recs):
    with st.expander("📷 عکس صفحه‌ی کتاب → ترجمه و کلمه‌ها", expanded=False):
        decks = sorted({srs.deck_of(x) for x in recs})
        existing = {srs.normalize_word_answer(x.get("کلمه", "")) for x in recs}

        src = st.radio("منبع:", ["📁 عکس از گالری", "📸 دوربین"], horizontal=True, key="ph_src")
        if src.startswith("📸"):
            f = st.camera_input("عکس صفحه:", key="ph_cam")
        else:
            f = st.file_uploader("عکس صفحه:", type=["jpg", "jpeg", "png", "webp"], key="ph_file")
        if f is not None and st.button("✨ تحلیل صفحه", key="ph_go", type="primary"):
            try:
                with st.spinner("Gemini دارد صفحه را می‌خواند..."):
                    res = analyze_page(_prep_image(f.getvalue()))
                if not str(res.get("text", "")).strip():
                    st.warning("متنی در عکس پیدا نشد؛ عکس واضح‌تر بگیر.")
                else:
                    st.session_state["ph_res"] = res
                    st.session_state["ph_n"] = st.session_state.get("ph_n", 0) + 1
            except Exception as e:
                st.error(f"{e}")

        res = st.session_state.get("ph_res")
        if not res:
            return
        st.markdown("**متن صفحه** (اگر جایی اشتباه خوانده شده اصلاحش کن):")
        text = st.text_area("متن", res.get("text", ""), height=160, key="ph_text", label_visibility="collapsed")
        st.markdown("**ترجمه‌ی فارسی**")
        st.markdown(f'<div dir="rtl" style="line-height:1.9">{res.get("translation_fa", "")}</div>'.replace("\n", "<br>"),
                    unsafe_allow_html=True)
        st.button("📚 این متن را به بخش خواندن بفرست (رنگ‌بندی و صدا)", key="ph_to_read",
                  on_click=_send_to_reader, args=(text,))

        n = st.session_state.get("ph_n", 0)
        words = []
        for w in res.get("words", []):
            word = str(w.get("word", "")).strip()
            if not word:
                continue
            d = (w.get("daily") or []) + [{}, {}]
            words.append({
                "کلمه": word, "معنی": str(w.get("translation_fa", "")),
                "نوع": str(w.get("word_class", "fras")),
                "جمله_کتاب": str(w.get("book_sv", "")), "ترجمه_کتاب": str(w.get("book_fa", "")),
                "روزمره1_sv": str(d[0].get("sv", "")), "روزمره1_fa": str(d[0].get("fa", "")),
                "روزمره2_sv": str(d[1].get("sv", "")), "روزمره2_fa": str(d[1].get("fa", "")),
                "تکراری": srs.normalize_word_answer(str(w.get("word", ""))) in existing,
            })
        if not words:
            st.info("کلمه‌ای پیشنهاد نشد.")
            return

        def _set_all(val):
            for i, w in enumerate(words):
                st.session_state[f"ph_sel_{n}_{i}"] = val and not w["تکراری"]

        st.markdown("### 🔑 کلمه‌های مهم")
        b1, b2 = st.columns(2)
        b1.button("☑️ همه", key="ph_all", on_click=_set_all, args=(True,), use_container_width=True)
        b2.button("⬜ هیچ‌کدام", key="ph_none", on_click=_set_all, args=(False,), use_container_width=True)

        def _val(i, field, default):
            return st.session_state.get(f"ph_{field}_{n}_{i}", default)

        for i, w in enumerate(words):
            with st.container(border=True):
                st.session_state.setdefault(f"ph_sel_{n}_{i}", not w["تکراری"])
                st.checkbox(f"**{w['کلمه']}** — {w['معنی']}  ·  {w['نوع']}", key=f"ph_sel_{n}_{i}")
                if w["تکراری"]:
                    st.caption("از قبل در بانک کلمات هست.")
                if w["جمله_کتاب"]:
                    st.markdown(f"📖 {w['جمله_کتاب']}")
                    st.caption(w["ترجمه_کتاب"])
                for k in (1, 2):
                    if w[f"روزمره{k}_sv"]:
                        st.markdown(f"💬 {w[f'روزمره{k}_sv']}")
                        st.caption(w[f"روزمره{k}_fa"])
                if st.button("🔊", key=f"ph_snd_{n}_{i}"):
                    mp3 = shadowing_view._tts(srs.normalize_word_answer(w["کلمه"]) or w["کلمه"])
                    if mp3:
                        st.audio(mp3, format="audio/mp3")
                with st.expander("✏️ ویرایش"):
                    for field, label in [("کلمه", "کلمه"), ("معنی", "معنی"), ("جمله_کتاب", "جمله‌ی کتاب"),
                                         ("ترجمه_کتاب", "ترجمه‌ی جمله‌ی کتاب"),
                                         ("روزمره1_sv", "روزمره ۱"), ("روزمره1_fa", "ترجمه ۱"),
                                         ("روزمره2_sv", "روزمره ۲"), ("روزمره2_fa", "ترجمه ۲")]:
                        st.text_input(label, w[field], key=f"ph_{field}_{n}_{i}")

        deck = kort_view._deck_picker(decks, "ph_deck")
        if st.button("💾 افزودن تیک‌خورده‌ها به کارت‌ها", key="ph_save", type="primary"):
            out = []
            for i, w in enumerate(words):
                if not st.session_state.get(f"ph_sel_{n}_{i}"):
                    continue
                r = {k: _val(i, k, w[k]) for k in w if k != "تکراری"}
                if str(r["کلمه"]).strip():
                    out.append(_row(deck, r))
            if not out:
                st.warning("هیچ کلمه‌ای تیک نخورده.")
            else:
                try:
                    sh.append_rows("ordbank", out)
                    st.session_state.pop("ph_res", None)
                    st.success(f"✅ {len(out)} کارت به دسته‌ی «{deck}» اضافه شد.")
                except Exception as e:
                    st.error(f"ذخیره شکست خورد: {e}")
