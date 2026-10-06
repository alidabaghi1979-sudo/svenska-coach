"""
Svenska Coach — اپ یکپارچه‌ی تمرین سوئدی.
داشبورد امروز، بانک کلمات، خطاهای من، پیشرفت، و مربی هوش مصنوعی.
اجرا: streamlit run app.py
"""
import datetime
import html
import json
import os
import re

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import coach
import framstegstest_view
import exercise_view
import horforstaelse_view
import irregular_verbs
import lesson_view
import sheets_helper as sh
import srs
import vocab_extract
import word_audio

st.set_page_config(page_title="Svenska Coach", page_icon="🇸🇪", layout="wide")

# چرخه‌ی هفتگی تمرکز — دوشنبه=0 ... یکشنبه=6
WEEKDAY_FOCUS = {
    0: "مکالمه‌ی روزمره",
    1: "واژگان کاری / مصاحبه",
    2: "مکالمه‌ی روزمره",
    3: "واژگان کاری / مصاحبه",
    4: "مکالمه‌ی روزمره",
    5: "مرور هفته + سبک آزمون SFI/SAS",
    6: "آزاد، بدون تکلیف",
}


def parse_transcript_sentences(transcript_text):
    """
    خط‌های رونوشت («[0.0s -> 4.0s] متن») رو به لیستی از دیکشنری تبدیل می‌کنه:
    {"start": ثانیه یا None, "end": ثانیه یا None, "text": متن}
    """
    sentences = []
    pattern = re.compile(r"^\[(\d+\.?\d*)s\s*->\s*(\d+\.?\d*)s\]\s*(.*)$")
    for line in (transcript_text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            start, end, text = float(m.group(1)), float(m.group(2)), m.group(3).strip()
        else:
            start, end, text = None, None, line
        if text:
            sentences.append({"start": start, "end": end, "text": text})
    return sentences


def tokenize_words(sentence):
    """کلمات یه جمله رو جدا می‌کنه و علائم نگارشی اطرافشون رو حذف می‌کنه."""
    words = []
    for tok in sentence.split():
        cleaned = tok.strip(".,!?;:،؛\"'()[]«»")
        if cleaned:
            words.append(cleaned)
    return words


def is_learnable_word(word, is_first_in_sentence):
    """
    تشخیص می‌ده کلمه ارزش یادگیری داره یا احتمالاً اسم‌خاص/عدده.
    قانون: عدد خالص، یا حرف اول بزرگ و وسط جمله (نه شروع جمله) → اسم‌خاص فرض می‌شه.
    تو سوئدی برخلاف انگلیسی/آلمانی، اسم‌های معمولی وسط جمله بزرگ نوشته نمی‌شن.
    """
    if word.isdigit():
        return False
    if word[0].isupper() and not is_first_in_sentence:
        return False
    return True


def normalize_meaning_info(raw):
    """
    ورودی batch_lookup_meanings ممکنه یا دیکشنری {"meaning":.., "level":..} باشه
    (فرمت جدید) یا یه رشته‌ی ساده (فرمت قدیمی/کش‌شده). همیشه دیکشنری برمی‌گردونه
    تا بقیه‌ی کد مجبور نباشه نوع رو چک کنه.
    """
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw:
        return {"meaning": raw, "level": ""}
    return {}


CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1"]


def level_sort_key(level):
    """فاصله‌ی سطح کلمه از A2 (سطح فعلی) — نزدیک‌ترها اول نشون داده بشن."""
    try:
        return abs(CEFR_ORDER.index(level) - CEFR_ORDER.index("A2"))
    except ValueError:
        return 99

today_focus = WEEKDAY_FOCUS[datetime.date.today().weekday()]

st.title("🇸🇪 Svenska Coach")
st.caption(f"Idag: {datetime.date.today().strftime('%Y-%m-%d')} — Fokus: {today_focus}")

NAV_OPTIONS = {
    "today": "📅 Idag · امروز",
    "vocab": "📖 Ordbank · کلمات",
    "listening": "🎧 Lyssna · شنیداری",
    "selftest": "📝 Prov · خودآزمایی",
    "exercises": "✏️ Övningar · تمرین درس",
    "mistakes": "⚠️ Mina fel · خطاها",
    "progress": "📈 Framsteg · پیشرفت",
    "coach": "🤖 Coach · مربی",
}
nav = st.radio(
    "بخش:", list(NAV_OPTIONS.keys()), format_func=lambda k: NAV_OPTIONS[k],
    horizontal=True, key="main_nav", label_visibility="collapsed",
)
# نکته‌ی عملکردی: هر بخش فقط وقتی انتخاب شده کدش اجرا می‌شه (نه همه‌ی بخش‌ها هر بار)
# که باعث می‌شه جابه‌جایی بین بخش‌ها سریع‌تر بشه (قبلاً با st.tabs هر ۵ بخش هر بار اجرا می‌شدن).

# ---------------- تب امروز ----------------
if nav == "today":
    st.subheader(f"تمرکز امروز: {today_focus}")

    # قابلیت دانلود/رونویسی فقط رو نسخه‌ی محلی در دسترسه (به کتابخونه‌های سنگین نیاز داره)
    can_fetch = True
    try:
        import config
        from fetch_podcast import fetch_new_podcast_episodes, load_state, save_state
        from fetch_youtube import fetch_new_youtube_audio
        from transcribe import transcribe_file
    except ImportError:
        can_fetch = False

    # درس صوتی روزانه (ساخته‌شده شبانه توسط daily_lesson/ در GitHub Actions)
    lesson_view.render(sh, can_fetch=can_fetch)
    st.divider()
    st.subheader("📥 صوت‌های واقعی (پادکست/یوتیوب)")

    if can_fetch:
        today_category = config.WEEKDAY_CATEGORY.get(datetime.date.today().weekday())
        if today_category is None:
            st.info("امروز یکشنبه‌ست — روز آزاده، منبع خودکاری تعریف نشده.")
        else:
            st.caption(f"دسته‌ی امروز: {today_category} — فقط از منابع همین دسته دریافت می‌کنه.")
            if st.button("📥 دریافت محتوای جدید"):
                with st.spinner("در حال دانلود و رونویسی... ممکنه چند دقیقه طول بکشه"):
                    state = load_state(config.STATE_FILE)
                    accepted = []  # (path, txt_path, transcript) فقط موارد سوئدی
                    skipped_languages = []

                    # منابعی که امروز باید ازشون دریافت کنیم
                    sources_today = [
                        ("podcast", name, url, fetch_new_podcast_episodes)
                        for name, url in config.PODCAST_FEEDS.get(today_category, {}).items()
                    ] + [
                        ("youtube", name, url, fetch_new_youtube_audio)
                        for name, url in config.YOUTUBE_SOURCES.get(today_category, {}).items()
                    ]

                    MAX_ATTEMPTS_PER_SOURCE = 2  # اگه اپیزود اول سوئدی نبود، یه بار دیگه امتحان کن

                    for kind, name, url, fetch_func in sources_today:
                        for attempt in range(MAX_ATTEMPTS_PER_SOURCE):
                            new_files = fetch_func(name, url, config.DOWNLOAD_DIR, state, 1)
                            if not new_files:
                                break  # چیز جدیدی از این منبع نمونده
                            path = new_files[0]
                            txt_path, lang = transcribe_file(path, model_size=config.WHISPER_MODEL_SIZE)
                            if lang == "sv":
                                with open(txt_path, "r", encoding="utf-8") as f:
                                    transcript = f.read()
                                accepted.append((path, transcript))
                                break  # این منبع برای امروز کافیه
                            else:
                                skipped_languages.append((name, lang))
                                try:
                                    os.remove(path)
                                    os.remove(txt_path)
                                except OSError:
                                    pass
                                # حلقه ادامه پیدا می‌کنه و اپیزود بعدی رو امتحان می‌کنه

                    save_state(config.STATE_FILE, state)

                    for path, transcript in accepted:
                        title = path.replace("\\", "/").split("/")[-1]
                        try:
                            import drive_upload
                            drive_link = drive_upload.upload_audio_and_get_link(path, title)
                        except ImportError:
                            drive_link = ""
                        sh.append_row(
                            "audio_log",
                            [str(datetime.date.today()), "local", title, path, transcript[:45000], drive_link],
                        )

                if skipped_languages:
                    for name, lang in skipped_languages:
                        st.warning(f"یه اپیزود از «{name}» به زبان «{lang}» بود (نه سوئدی) — ردش کردم.")
                st.success(f"{len(accepted)} فایل جدید سوئدی دریافت و رونویسی شد.")
                st.rerun()
    else:
        st.info(
            "قابلیت دانلود خودکار فقط رو نسخه‌ی محلی (کامپیوتر) در دسترسه. "
            "اینجا (نسخه‌ی ابری) فقط رونوشت‌های قبلی رو می‌بینی و می‌تونی با مربی تمرین کنی."
        )

    st.divider()
    st.subheader("جلسه‌های اخیر")
    audio_df = sh.read_tab("audio_log")
    if audio_df.empty:
        st.write("هنوز جلسه‌ای ثبت نشده.")
    else:
        for _, row in audio_df.tail(5).iloc[::-1].iterrows():
            entry_key = f"{row.get('تاریخ','')}_{row.get('عنوان','')}"
            transcript_text = row.get("رونوشت", "")
            with st.expander(f"{row.get('تاریخ', '')} — {row.get('عنوان', '')}"):
                audio_shown = False
                if can_fetch:
                    local_path = row.get("مسیر_محلی", "")
                    if local_path and os.path.exists(local_path):
                        st.audio(local_path)
                        audio_shown = True
                if not audio_shown and row.get("لینک_درایو"):
                    try:
                        st.audio(row["لینک_درایو"])
                        audio_shown = True
                    except Exception:
                        pass
                if not audio_shown:
                    st.caption("صدا برای این جلسه در دسترس نیست.")

                sentences = parse_transcript_sentences(transcript_text)

                # کلمات یکتای «قابل‌یادگیری» (نه اسم‌خاص/عدد) + جمله‌ای که اولین‌بار توش اومدن
                word_to_info = {}
                unique_words = []
                for sentence in sentences:
                    for idx, w in enumerate(tokenize_words(sentence["text"])):
                        if not is_learnable_word(w, is_first_in_sentence=(idx == 0)):
                            continue
                        if w not in word_to_info:
                            word_to_info[w] = sentence
                            unique_words.append(w)

                # معنی + سطح CEFR برای تولتیپ هاور — فقط یه‌بار در کل عمر جلسه محاسبه می‌شه
                # (v2: بعد از تغییر فرمت خروجی به دیکشنری meaning+level، کلید کش عوض شد
                # تا با نسخه‌ی قبلی که فقط رشته بود تداخل نکنه)
                meanings_key = f"hover_meanings_v2_{entry_key}"
                if meanings_key not in st.session_state:
                    if unique_words:
                        with st.spinner("در حال آماده‌سازی تولتیپ کلمات..."):
                            result = vocab_extract.batch_lookup_meanings(unique_words, transcript_text)
                        if not result:
                            st.warning(
                                "دریافت معنی کلمات برای هاور شکست خورد (شاید پاسخ ناقص برگشته). "
                                "دوباره جلسه رو باز/بسته کن، یا با تعداد کلمه‌ی کمتری امتحان کن."
                            )
                        st.session_state[meanings_key] = result
                    else:
                        st.session_state[meanings_key] = {}
                hover_meanings = st.session_state[meanings_key]

                st.caption(
                    "موس رو هر کلمه نگه دار تا معنیش رو ببینی. اسم‌های خاص و عددها قابل‌انتخاب نیستن. "
                    "برای اضافه‌کردن به بانک کلمات، از لیست پایین انتخابش کن."
                )

                # ---------- نمایش HTML با تولتیپ هاور (native title) ----------
                html_parts = ['<div style="line-height:2.4; font-size:16px;">']
                for sentence in sentences:
                    html_parts.append('<p dir="ltr" style="text-align:left; margin:4px 0;">')
                    for idx, w in enumerate(tokenize_words(sentence["text"])):
                        word_html = html.escape(w)
                        info = normalize_meaning_info(hover_meanings.get(w)) if is_learnable_word(w, idx == 0) else {}
                        if info:
                            meaning = html.escape(str(info.get("meaning", "")))
                            level = html.escape(str(info.get("level", "")))
                            title = f"{meaning} ({level})" if level else meaning
                            html_parts.append(
                                f'<span title="{title}" '
                                f'style="border-bottom:1px dotted #888; cursor:help; margin-left:3px;">'
                                f'{word_html}</span>'
                            )
                        else:
                            html_parts.append(f'<span style="margin-left:3px; color:#999;">{word_html}</span>')
                    html_parts.append("</p>")
                html_parts.append("</div>")
                st.markdown("".join(html_parts), unsafe_allow_html=True)

                # ---------- انتخاب کلمه برای افزودن به بانک + کارت آنکی ----------
                if unique_words:
                    sorted_words = sorted(
                        unique_words,
                        key=lambda w: level_sort_key(normalize_meaning_info(hover_meanings.get(w)).get("level", ""))
                    )

                    def _pill_label(w):
                        lvl = normalize_meaning_info(hover_meanings.get(w)).get("level", "")
                        return f"{w} · {lvl}" if lvl else w

                    st.pills(
                        "کلماتی که نمی‌دونستی رو انتخاب کن (مرتب‌شده از نزدیک‌ترین به سطح A2):",
                        options=sorted_words,
                        format_func=_pill_label,
                        selection_mode="multi",
                        key=f"pills_{entry_key}",
                    )

                    if st.button("➕ افزودن کلمات انتخاب‌شده به بانک کلمات", key=f"add_{entry_key}"):
                        selected = st.session_state.get(f"pills_{entry_key}", [])
                        if not selected:
                            st.info("هیچ کلمه‌ای انتخاب نشده بود.")
                        else:
                            pairs = [(w, word_to_info[w]["text"]) for w in selected]
                            with st.spinner("در حال گرفتن جزئیات از مربی..."):
                                details = vocab_extract.batch_lookup_details(pairs)

                            apkg_items = []
                            added = 0
                            for d in details:
                                word = d.get("word", "")
                                info = word_to_info.get(word, {})
                                meaning_line = f"{d.get('meaning', '')} ({d.get('pos', '')})".strip()
                                extra_lines = [info.get("text", "")]
                                if d.get("forms"):
                                    extra_lines.append(f"صرف: {d['forms']}")
                                for ex in d.get("examples", []):
                                    extra_lines.append(f"مثال: {ex.get('sv','')} — {ex.get('fa','')}")
                                jomle_field = "\n".join(line for line in extra_lines if line)

                                sv_sentences = [ex.get("sv", "") for ex in d.get("examples", []) if ex.get("sv")]
                                sentences_field = json.dumps(sv_sentences, ensure_ascii=False) if sv_sentences else ""
                                sh.append_row(
                                    "ordbank",
                                    [str(datetime.date.today()), word, meaning_line, jomle_field, 0, "", sentences_field],
                                )
                                added += 1
                                with st.expander(f"✅ {word} — {meaning_line}"):
                                    for ex in d.get("examples", []):
                                        st.write(f"🔹 {ex.get('sv','')} — {ex.get('fa','')}")

                                apkg_items.append({
                                    "word": word,
                                    "sentence": info.get("text", ""),
                                    "meaning": d.get("meaning", ""),
                                    "pos": d.get("pos", ""),
                                    "forms": d.get("forms", ""),
                                    "examples": d.get("examples", []),
                                    "audio_source_path": row["مسیر_محلی"] if can_fetch else None,
                                    "start": info.get("start"),
                                    "end": info.get("end"),
                                })

                            if added:
                                st.success(f"{added} کلمه به بانک کلمات اضافه شد.")

                            # ---------- ارسال کارت آنکی: مستقیم (AnkiConnect) یا دانلود (فقط محلی) ----------
                            if can_fetch and apkg_items:
                                anki_live = False
                                try:
                                    import ankiconnect
                                    anki_live = ankiconnect.is_available()
                                except ImportError:
                                    pass

                                if anki_live:
                                    import tempfile
                                    from pathlib import Path

                                    import anki_export as ae

                                    with st.spinner("در حال ارسال مستقیم به Anki..."):
                                        sliced_paths = {}
                                        with tempfile.TemporaryDirectory() as tmp_dir:
                                            for item in apkg_items:
                                                if item.get("audio_source_path") and item.get("start") is not None:
                                                    clip_path = Path(tmp_dir) / f"clip_{item['word']}.mp3"
                                                    try:
                                                        ae._slice_audio(
                                                            item["audio_source_path"],
                                                            item["start"], item["end"], clip_path,
                                                        )
                                                        sliced_paths[item["word"]] = str(clip_path)
                                                    except Exception:
                                                        pass
                                            anki_added = ankiconnect.add_cards(apkg_items, sliced_paths)
                                    st.success(
                                        f"✅ {anki_added} کارت مستقیم به Anki اضافه شد — لازم نیست فایلی دانلود/ایمپورت کنی!"
                                    )
                                else:
                                    try:
                                        import anki_export
                                        apkg_path = f"anki_export_{entry_key}.apkg".replace(" ", "_")
                                        with st.spinner("در حال ساخت کارت‌های آنکی..."):
                                            anki_export.build_apkg(apkg_items, "Ordförråd", apkg_path)
                                        with open(apkg_path, "rb") as f:
                                            st.download_button(
                                                "📥 دانلود دسته‌ی آنکی (.apkg)",
                                                data=f.read(),
                                                file_name="svenska_coach.apkg",
                                                mime="application/octet-stream",
                                                key=f"apkg_{entry_key}",
                                            )
                                        st.caption(
                                            "نکته: اگه Anki رو باز کنی (با افزونه‌ی AnkiConnect نصب‌شده)، "
                                            "دفعه‌ی بعد نیازی به دانلود دستی نیست."
                                        )
                                    except ImportError:
                                        st.caption("برای ساخت کارت آنکی، کتابخونه‌ی genanki رو نصب کن: pip install genanki")

# ---------------- تب بانک کلمات ----------------
if nav == "vocab":
    st.subheader("📖 بانک کلمات")
    vocab_df = sh.read_tab("ordbank")

    # ---------- بخش مرور فلش‌کارتی (SRS) — سه حالت تصادفی ----------
    st.markdown("### 🎴 مرور امروز")

    if "srs_queue" not in st.session_state:
        st.session_state.srs_queue = None
        st.session_state.srs_index = 0
        st.session_state.srs_show_answer = False
        st.session_state.srs_correct_count = 0
        st.session_state.srs_typed_result = None
        st.session_state.srs_typed_value = ""
        st.session_state.srs_logged = False

    due_df = srs.get_due_words(vocab_df)

    if st.session_state.srs_queue is None:
        if due_df.empty:
            st.info("امروز کلمه‌ای برای مرور نداری. 🎉")
        else:
            st.write(f"امروز **{len(due_df)}** کلمه برای مرور آماده‌ست.")
            if st.button("▶️ شروع مرور"):
                records = due_df.to_dict("records")
                for r in records:
                    r["_mode"] = srs.pick_mode()
                st.session_state.srs_queue = records
                st.session_state.srs_index = 0
                st.session_state.srs_show_answer = False
                st.session_state.srs_correct_count = 0
                st.session_state.srs_typed_result = None
                st.session_state.srs_typed_value = ""
                st.session_state.srs_logged = False
                st.rerun()

    else:
        queue = st.session_state.srs_queue
        idx = st.session_state.srs_index

        if idx >= len(queue):
            st.success(
                f"امروز {len(queue)} کلمه مرور شد، {st.session_state.srs_correct_count} تا درست. 👏"
            )
            if len(queue) > 0 and not st.session_state.get("srs_logged", False):
                sh.append_row(
                    "review_log",
                    [str(datetime.date.today()), len(queue), st.session_state.srs_correct_count],
                )
                st.session_state.srs_logged = True
            if st.button("🔁 بستن جلسه‌ی مرور"):
                st.session_state.srs_queue = None
                st.session_state.srs_logged = False
                st.rerun()
        else:
            card = queue[idx]
            mode = card.get("_mode", "sv2fa")
            st.caption(f"کارت {idx + 1} از {len(queue)}")

            def _go_next(correct):
                new_level, next_date = srs.compute_next_review(card.get("سطح", 0), correct)
                sh.update_cells_by_match(
                    "ordbank", "کلمه", card.get("کلمه", ""),
                    {"سطح": new_level, "مرور_بعدی": next_date},
                )
                if correct:
                    st.session_state.srs_correct_count += 1
                st.session_state.srs_index += 1
                st.session_state.srs_show_answer = False
                st.session_state.srs_typed_result = None
                st.session_state.srs_typed_value = ""

            # ---- حالت ۱: سوئدی → فارسی (خودارزیابی، مثل قبل) ----
            if mode == "sv2fa":
                st.caption("🇸🇪 ← → 🇮🇷")
                st.markdown(f"## {card.get('کلمه', '')}")
                if not st.session_state.srs_show_answer:
                    if st.button("🔍 نشون بده", key=f"sv2fa_show_{idx}"):
                        st.session_state.srs_show_answer = True
                        st.rerun()
                else:
                    st.write(f"**معنی:** {card.get('معنی', '')}")
                    if card.get("جمله"):
                        st.write(f"**جمله:** {card.get('جمله', '')}")
                    col_yes, col_no = st.columns(2)
                    if col_yes.button("✅ بلد بودم", key=f"sv2fa_yes_{idx}"):
                        _go_next(True)
                        st.rerun()
                    if col_no.button("❌ بلد نبودم", key=f"sv2fa_no_{idx}"):
                        _go_next(False)
                        st.rerun()

            # ---- حالت ۲: فارسی → سوئدی (تایپ کن، چک خودکار) ----
            elif mode == "fa2sv":
                st.caption("🇮🇷 → 🇸🇪 (تایپ کن)")
                st.markdown(f"## {card.get('معنی', '')}")
                if not st.session_state.srs_show_answer:
                    typed = st.text_input("سوئدیش رو تایپ کن:", key=f"fa2sv_input_{idx}")
                    if st.button("✅ بررسی کن", key=f"fa2sv_check_{idx}"):
                        correct = srs.check_word_answer(typed, card.get("کلمه", ""))
                        st.session_state.srs_typed_result = correct
                        st.session_state.srs_typed_value = typed
                        st.session_state.srs_show_answer = True
                        st.rerun()
                else:
                    correct = st.session_state.srs_typed_result
                    if correct:
                        st.success(f"✅ درست بود: **{card.get('کلمه', '')}**")
                    else:
                        st.error(f"❌ جواب درست: **{card.get('کلمه', '')}**")
                        st.caption(f"چیزی که تو نوشتی: «{st.session_state.get('srs_typed_value', '')}»")
                    if card.get("جمله"):
                        st.caption(card.get("جمله", ""))
                    if st.button("➡️ بعدی", key=f"fa2sv_next_{idx}"):
                        _go_next(bool(correct))
                        st.rerun()

            # ---- حالت ۳: املا (فقط صدا، بدون معنی) ----
            else:
                st.caption("✍️ املا — فقط گوش کن و بنویس")
                audio_bytes = word_audio.synth_swedish(card.get("کلمه", ""))
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")
                else:
                    st.caption("🔇 صدا در دسترس نیست (کلید Azure تنظیم نشده).")
                if not st.session_state.srs_show_answer:
                    typed = st.text_input("چی شنیدی؟ املاش رو بنویس:", key=f"dictation_input_{idx}")
                    if st.button("✅ بررسی کن", key=f"dictation_check_{idx}"):
                        correct = srs.check_word_answer(typed, card.get("کلمه", ""))
                        st.session_state.srs_typed_result = correct
                        st.session_state.srs_typed_value = typed
                        st.session_state.srs_show_answer = True
                        st.rerun()
                else:
                    correct = st.session_state.srs_typed_result
                    if correct:
                        st.success(f"✅ درست بود: **{card.get('کلمه', '')}**")
                    else:
                        st.error(f"❌ جواب درست: **{card.get('کلمه', '')}**")
                        st.caption(f"چیزی که تو نوشتی: «{st.session_state.get('srs_typed_value', '')}»")
                        st.write(f"**معنی:** {card.get('معنی', '')}")
                    if st.button("➡️ بعدی", key=f"dictation_next_{idx}"):
                        _go_next(bool(correct))
                        st.rerun()

    st.divider()
    st.markdown("### 🎧 تمرین دیکته‌ی جمله (کلمات تازه)")
    st.caption("جمله رو فقط با صدا می‌شنوی، تایپش می‌کنی، بعد با اصل جمله مقایسه می‌کنی — نمره‌دهی خودکار نداره.")

    practice_rows = []
    if not vocab_df.empty and "جملات_تمرینی" in vocab_df.columns:
        for _, row in vocab_df.iterrows():
            raw = row.get("جملات_تمرینی", "")
            if not raw or not str(raw).strip():
                continue
            try:
                sv_list = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                sv_list = []
            for s_idx, sv in enumerate(sv_list):
                if sv:
                    practice_rows.append((row.get("کلمه", ""), s_idx, sv))

    if not practice_rows:
        st.caption("هنوز جمله‌ی تمرینی‌ای ثبت نشده. وقتی کلمه‌ی جدید از یه رونوشت اضافه کنی، خودکار ساخته می‌شه.")
    else:
        if (
            "dictation_sentence_idx" not in st.session_state
            or st.session_state.dictation_sentence_idx >= len(practice_rows)
        ):
            st.session_state.dictation_sentence_idx = 0
        choice_idx = st.session_state.dictation_sentence_idx
        word_label, _, chosen_sv = practice_rows[choice_idx]
        st.caption(f"جمله‌ی {choice_idx + 1} از {len(practice_rows)} — کلمه: {word_label}")
        sentence_audio = word_audio.synth_swedish(chosen_sv)
        if sentence_audio:
            st.audio(sentence_audio, format="audio/mp3")
        else:
            st.caption("🔇 صدا در دسترس نیست (کلید Azure تنظیم نشده).")
        st.text_area("چی شنیدی؟", key=f"dictation_sentence_input_{choice_idx}")
        with st.expander("🔍 نشون بده (اصل جمله)"):
            st.write(chosen_sv)
        if st.button("➡️ جمله‌ی بعدی", key="dictation_sentence_next"):
            st.session_state.dictation_sentence_idx = (choice_idx + 1) % len(practice_rows)
            st.rerun()

    st.divider()
    st.markdown("### 📚 افزودن فعل‌های بی‌قاعده (Rivstart A1+A2)")
    st.caption("۶۹ فعل بی‌قاعده از کتاب Rivstart — انتخاب کن کدوما به بانک کلمات اضافه بشن.")

    try:
        existing_verb_words = (
            {srs.normalize_word_answer(w) for w in vocab_df["کلمه"] if str(w).strip()}
            if not vocab_df.empty and "کلمه" in vocab_df.columns else set()
        )
    except Exception:
        existing_verb_words = set()

    verb_by_word = {v["word"]: v for v in irregular_verbs.IRREGULAR_VERBS}
    verb_already_added = [w for w in verb_by_word if srs.normalize_word_answer(w) in existing_verb_words]
    verb_pickable = [w for w in verb_by_word if w not in verb_already_added]

    with st.expander(f"نمایش فعل‌ها ({len(verb_pickable)} باقی‌مونده، {len(verb_already_added)} اضافه‌شده)"):
        if verb_pickable:
            def _verb_pill_label(w):
                meaning = verb_by_word.get(w, {}).get("meaning_fa", "")
                return f"{w} · {meaning}" if meaning else w

            st.pills(
                "فعل‌هایی که می‌خوای به بانک کلمات اضافه بشن رو انتخاب کن:",
                options=verb_pickable,
                format_func=_verb_pill_label,
                selection_mode="multi",
                key="irregular_verb_pills",
            )

            if st.button("➕ افزودن فعل‌های انتخاب‌شده به بانک کلمات", key="irregular_verb_add"):
                selected = st.session_state.get("irregular_verb_pills", [])
                if not selected:
                    st.info("هیچ فعلی انتخاب نشده بود.")
                else:
                    added = 0
                    for w in selected:
                        v = verb_by_word.get(w, {})
                        word_field = f"{w} ({v.get('forms', '')})"
                        meaning_line = f"{v.get('meaning_fa', '')} (verb, oregelbunden)"
                        sh.append_row(
                            "ordbank",
                            [str(datetime.date.today()), word_field, meaning_line, "", 0, "", ""],
                        )
                        added += 1
                    st.success(f"✅ {added} فعل به بانک کلمات اضافه شد.")
                    st.rerun()
        else:
            st.caption("همه‌ی فعل‌های بی‌قاعده قبلاً تو بانک کلمات هستن. ✅")

    st.divider()
    st.markdown("### فهرست کامل و ویرایش دستی")
    edited_vocab = st.data_editor(
        vocab_df, num_rows="dynamic", use_container_width=True, key="vocab_editor"
    )
    if st.button("💾 ذخیره‌ی تغییرات بانک کلمات"):
        sh.overwrite_tab("ordbank", edited_vocab)
        st.success("ذخیره شد.")
        st.rerun()

# ---------------- تب خطاهای من ----------------
if nav == "listening":
    horforstaelse_view.render(sh)

if nav == "selftest":
    framstegstest_view.render(sh)

if nav == "exercises":
    exercise_view.render(sh)

if nav == "mistakes":
    st.subheader("⚠️ خطاهای تکراری من")
    st.caption("مهم‌ترین جدول — مربی تمرین گرامری رو بر همین اساس طراحی می‌کنه.")
    mistakes_df = sh.read_tab("mina_fel")
    edited_mistakes = st.data_editor(
        mistakes_df, num_rows="dynamic", use_container_width=True, key="mistakes_editor"
    )
    if st.button("💾 ذخیره‌ی تغییرات خطاها"):
        sh.overwrite_tab("mina_fel", edited_mistakes)
        st.success("ذخیره شد.")
        st.rerun()

# ---------------- تب پیشرفت ----------------
if nav == "progress":
    st.subheader("📈 پیشرفت")
    progress_df = sh.read_tab("progress")

    with st.form("log_progress_form"):
        col1, col2 = st.columns(2)
        topic = col1.text_input("موضوع جلسه", value=today_focus)
        pct = col2.slider("درصد فهم صوت بدون متن", 0, 100, 50)
        note = st.text_input("نکته (اختیاری)")
        if st.form_submit_button("➕ ثبت جلسه‌ی امروز"):
            sh.append_row("progress", [str(datetime.date.today()), topic, pct, note])
            st.success("ثبت شد.")
            st.rerun()

    if not progress_df.empty:
        progress_df["درصد_فهم"] = pd.to_numeric(progress_df["درصد_فهم"], errors="coerce")
        fig = px.line(
            progress_df, x="تاریخ", y="درصد_فهم", markers=True, title="روند درصد فهم شنیداری"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(progress_df, use_container_width=True)
    else:
        st.write("هنوز جلسه‌ای ثبت نشده.")

    st.divider()
    st.markdown("#### 🔥 استمرار مرور (۱۳ هفته‌ی اخیر)")
    review_log_df = sh.read_tab("review_log")

    WEEKDAY_LABELS_FA = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]
    N_WEEKS = 13
    today_d = datetime.date.today()
    start_d = today_d - datetime.timedelta(days=today_d.weekday() + 7 * (N_WEEKS - 1))

    daily_counts = {}
    if not review_log_df.empty and "تاریخ" in review_log_df.columns:
        counts_series = pd.to_numeric(review_log_df.get("تعداد_کارت"), errors="coerce").fillna(0)
        for d_str, cnt in zip(review_log_df["تاریخ"].astype(str), counts_series):
            daily_counts[d_str] = daily_counts.get(d_str, 0) + cnt

    z = [[0] * N_WEEKS for _ in range(7)]
    hover = [[""] * N_WEEKS for _ in range(7)]
    for week in range(N_WEEKS):
        for wd in range(7):
            d = start_d + datetime.timedelta(days=week * 7 + wd)
            if d > today_d:
                hover[wd][week] = ""
                continue
            cnt = int(daily_counts.get(d.isoformat(), 0))
            z[wd][week] = cnt
            hover[wd][week] = f"{d.isoformat()} ({WEEKDAY_LABELS_FA[wd]})<br>{cnt} کارت مرور شد"

    heat_fig = go.Figure(
        data=go.Heatmap(
            z=z,
            y=WEEKDAY_LABELS_FA,
            x=[f"هفته‌ی {i + 1}" for i in range(N_WEEKS)],
            colorscale=[
                [0.0, "#2b2f36"], [0.01, "#0e4429"], [0.35, "#006d32"],
                [0.65, "#26a641"], [1.0, "#39d353"],
            ],
            zmin=0,
            xgap=3, ygap=3,
            hoverinfo="text",
            text=hover,
            colorbar=dict(title="کارت", thickness=12),
            showscale=True,
        )
    )
    heat_fig.update_layout(
        height=280,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showgrid=False, side="top"),
        yaxis=dict(showgrid=False, autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(heat_fig, use_container_width=True)
    st.caption("هر خونه یه روزه؛ رنگ تیره‌تر یعنی تو اون روز کلمات بیشتری مرور کردی.")

# ---------------- تب مربی ----------------
if nav == "coach":
    st.subheader("🤖 مربی هوش مصنوعی")

    model_choice = st.selectbox(
        "مدل هوش مصنوعی مربی:",
        options=list(coach.AVAILABLE_MODELS.keys()),
        format_func=lambda m: coach.AVAILABLE_MODELS[m]["label"],
        key="coach_model_choice",
    )

    fresh_session = "chat_history" not in st.session_state
    if fresh_session:
        st.session_state.chat_history = []

    vocab_df = sh.read_tab("ordbank")
    mistakes_df = sh.read_tab("mina_fel")
    is_work_day = today_focus == "واژگان کاری / مصاحبه"
    coach_log_df = sh.read_tab("coach_log") if fresh_session else None
    system_prompt = coach.build_system_prompt(
        today_focus, vocab_df, mistakes_df, work_day=is_work_day, past_context_df=coach_log_df
    )
    system_prompt += lesson_view.coach_context(sh)

    if fresh_session and coach_log_df is not None and not coach_log_df.empty:
        st.caption("🧠 مربی خلاصه‌ی گفتگوهای قبلیت رو یادشه.")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("پیام بده... (فارسی یا سوئدی)")
    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)
        sh.append_row("coach_log", [str(datetime.date.today()), "user", user_input[:1500]])

        with st.chat_message("assistant"):
            with st.spinner("..."):
                reply = coach.ask_coach(st.session_state.chat_history, system_prompt, model=model_choice)
                st.write(reply)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        sh.append_row("coach_log", [str(datetime.date.today()), "assistant", reply[:1500]])
