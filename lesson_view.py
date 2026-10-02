"""
نمایش «درس صوتی روزانه» داخل تب امروز.
درس‌ها رو پایپ‌لاین daily_lesson/ هر شب (GitHub Actions) می‌سازه و تو تب lessons
همون Google Sheet می‌نویسه؛ کلمه‌هاش هم خودکار به ordbank اضافه می‌شن.
"""
import base64
import datetime
import html
import json
import re
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

import coach
import srs

CATEGORY_LABELS = {
    "vardag": "🏠 روزمره",
    "arbete": "💼 کار و مصاحبه",
    "sfi_prov": "📝 سبک آزمون SFI",
    "fritt": "🎈 آزاد",
    "manuell": "✍️ موضوع دلخواه",
}
SPEAKER_RE = re.compile(r"^\s*([A-ZÅÄÖ][A-ZÅÄÖ\- ]{1,20}):\s*(.*)$")
DEFAULT_REPO = "alidabaghi1979-sudo/svenska-coach"
WORKFLOW_FILE = "daily-lesson.yml"


def _stockholm_today():
    try:
        return datetime.datetime.now(ZoneInfo("Europe/Stockholm")).date()
    except Exception:  # ویندوز بدون پکیج tzdata
        return datetime.date.today()


def _json_list(raw):
    try:
        value = json.loads(raw) if isinstance(raw, str) and raw.strip() else []
        return value if isinstance(value, list) else []
    except json.JSONDecodeError:
        return []


def _rtl(text):
    return f'<div dir="rtl" style="text-align:right; line-height:1.9;">{html.escape(str(text))}</div>'


# ---------------- کلمات قابل هاور تو متن کامل ----------------
def _vocab_variant_map(vocab):
    """از لیست واژه‌های درس، نگاشت «هر شکل صرفی → (معنی، نوع کلمه)» می‌سازه."""
    variant_map = {}
    for v in vocab:
        word = str(v.get("word", ""))
        translation = str(v.get("translation_fa", "")).strip()
        if not translation:
            continue
        wc = str(v.get("word_class", "")).strip()
        base = re.sub(r"\([^)]*\)", "", word).strip()
        base = re.sub(r"^(en|ett|att)\s+", "", base, flags=re.IGNORECASE).strip()
        forms = [base]
        m = re.search(r"\(([^)]*)\)", word)
        if m:
            forms += [f.strip() for f in re.split(r"[,/;]", m.group(1)) if f.strip()]
        tooltip = f"{translation} ({wc})" if wc else translation
        for f in forms:
            if f:
                variant_map[f.lower()] = tooltip
    return variant_map


_WORD_SPLIT_RE = re.compile(r"(\w+)", flags=re.UNICODE)


def _hover_html(text, variant_map):
    """متن رو escape می‌کنه و کلمات موجود تو variant_map رو با تول‌تیپِ هاور نشون می‌ده."""
    if not variant_map:
        return html.escape(text)
    parts = _WORD_SPLIT_RE.split(text)
    out = []
    for part in parts:
        if part and _WORD_SPLIT_RE.fullmatch(part):
            tooltip = variant_map.get(part.lower())
            if tooltip:
                out.append(
                    f'<span title="{html.escape(tooltip)}" '
                    f'style="border-bottom:1px dotted #888; cursor:help;">{html.escape(part)}</span>'
                )
                continue
        out.append(html.escape(part))
    return "".join(out)


# ---------------- صدا ----------------
@st.cache_data(ttl=6 * 3600, max_entries=6, show_spinner=False)
def _drive_audio_bytes(file_id):
    """فایل رو با OAuth خود Ali از Drive می‌خونه (مطمئن‌تر از لینک عمومی)."""
    oauth = st.secrets["gdrive_oauth"]
    token = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": oauth["client_id"],
        "client_secret": oauth["client_secret"],
        "refresh_token": oauth["refresh_token"],
        "grant_type": "refresh_token",
    }, timeout=20)
    token.raise_for_status()
    resp = requests.get(
        f"https://www.googleapis.com/drive/v3/files/{file_id}",
        params={"alt": "media"},
        headers={"Authorization": f"Bearer {token.json()['access_token']}"},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.content


def _play_audio(row):
    file_id = str(row.get("شناسه_فایل", "") or "").strip()
    link = str(row.get("لینک_درایو", "") or "").strip()
    if file_id and "gdrive_oauth" in st.secrets:
        try:
            with st.spinner("در حال بارگذاری صدا..."):
                st.audio(_drive_audio_bytes(file_id), format="audio/mp3")
            return
        except Exception:
            pass  # برو سراغ لینک عمومی
    if link:
        st.audio(link)
    else:
        st.caption("🔇 صدای این درس هنوز آماده نیست (Google Drive تنظیم نشده یا ساخت صدا خطا داده).")


# ---------------- کارائوکه (هایلایتِ هم‌زمان با پخش صدا) ----------------
def _norm_for_match(s):
    s = re.sub(r"\s+", " ", str(s or "")).strip().lower()
    return re.sub(r"[^\wåäöÅÄÖ ]", "", s)


def _build_karaoke_lines(script_text, timings):
    """متنِ اسکریپت رو خط‌به‌خط (مثل متن کامل درس) می‌شکنه و سعی می‌کنه رویدادهای
    SentenceBoundary‌ی Azure (timings) رو به‌ترتیب به هر خط وصل کنه. اگه یه خط
    جور درنیومد فقط بدون هایلایت می‌مونه — هیچ‌وقت رندر رو خراب نمی‌کنه.
    """
    raw_lines = []
    for raw in str(script_text).splitlines():
        line = raw.strip()
        if not line or line.lower() == "[paus]":
            continue
        line = line.replace("[paus]", "").replace("[PAUS]", "").strip()
        if not line:
            continue
        m = SPEAKER_RE.match(line)
        if m:
            raw_lines.append({"speaker": m.group(1).title(), "text": m.group(2).strip()})
        else:
            raw_lines.append({"speaker": None, "text": line})

    t_idx, n = 0, len(timings)
    for entry in raw_lines:
        target = _norm_for_match(entry["text"])
        start = end = None
        consumed = ""
        while t_idx < n and len(consumed) < len(target):
            t = timings[t_idx]
            t_norm = _norm_for_match(t.get("text", ""))
            if not t_norm:
                t_idx += 1
                continue
            rest = target[len(consumed):]
            if rest.startswith(t_norm) or t_norm.startswith(rest):
                if start is None:
                    start = t.get("start_s")
                end = t.get("end_s")
                consumed += t_norm
                t_idx += 1
            else:
                break
        entry["start"], entry["end"] = start, end
    return raw_lines


def _render_karaoke(row, variant_map):
    """اگه این درس تایم‌استمپِ جمله‌ها رو داشته باشه، صدا + متن رو با هم تو یه
    کامپوننتِ HTML سفارشی نشون می‌ده (هایلایتِ کارائوکه). برمی‌گردونه True اگه
    کارائوکه نمایش داده شد، وگرنه False (یعنی باید fallback معمولی رو نشون بدی).
    """
    timings = _json_list(row.get("تایم‌استمپ_جمله‌ها", ""))
    if not timings:
        return False

    file_id = str(row.get("شناسه_فایل", "") or "").strip()
    audio_bytes = None
    if file_id and "gdrive_oauth" in st.secrets:
        try:
            audio_bytes = _drive_audio_bytes(file_id)
        except Exception:
            audio_bytes = None
    if not audio_bytes:
        return False

    lines = _build_karaoke_lines(str(row.get("متن", "")), timings)
    if not any(ln["start"] is not None for ln in lines):
        return False  # هیچ خطی جور درنیومد — کارائوکه فایده‌ای نداره

    b64 = base64.b64encode(audio_bytes).decode("ascii")
    rows_html = []
    for ln in lines:
        text_html = _hover_html(ln["text"], variant_map)
        prefix = f"<b>{html.escape(ln['speaker'])}:</b> " if ln["speaker"] else ""
        attrs = ""
        if ln["start"] is not None and ln["end"] is not None:
            attrs = f' data-start="{ln["start"]}" data-end="{ln["end"]}"'
        rows_html.append(f'<p class="kline" dir="ltr"{attrs}>{prefix}{text_html}</p>')

    page = f"""
    <div style="font-family: inherit; color: inherit;">
      <audio id="kaudio" controls style="width:100%;" src="data:audio/mp3;base64,{b64}"></audio>
      <div id="ktext" style="direction:ltr; line-height:1.9; margin-top:10px; max-height:420px;
                              overflow-y:auto; padding:4px;">
        {''.join(rows_html)}
      </div>
    </div>
    <style>
      .kline {{ transition: background-color .15s ease; padding:2px 4px; border-radius:4px; }}
      .kline.active {{ background-color: rgba(255, 213, 79, 0.45); }}
    </style>
    <script>
      const audio = document.getElementById('kaudio');
      const lines = Array.from(document.querySelectorAll('.kline[data-start]'));
      let current = null;
      audio.addEventListener('timeupdate', function() {{
        const t = audio.currentTime;
        let match = null;
        for (const el of lines) {{
          const s = parseFloat(el.dataset.start), e = parseFloat(el.dataset.end);
          if (t >= s && t < e) {{ match = el; break; }}
        }}
        if (match !== current) {{
          if (current) current.classList.remove('active');
          if (match) {{
            match.classList.add('active');
            match.scrollIntoView({{block: 'center', behavior: 'smooth'}});
          }}
          current = match;
        }}
      }});
    </script>
    """
    components.html(page, height=520, scrolling=False)
    st.caption("🎤 متن هم‌زمان با پخش صدا هایلایت می‌شه.")
    return True


# ---------------- Anki ----------------
def _surface_form(word, sentence):
    """شکلی از کلمه که واقعاً تو جمله اومده (مثلاً ringde برای ringa)."""
    base = re.sub(r"^(en|ett|att)\s+", "", word.split("(")[0].strip(), flags=re.IGNORECASE).strip()
    forms = [base]
    m = re.search(r"\(([^)]*)\)", word)
    if m:
        forms += [f.strip() for f in re.split(r"[,/;]", m.group(1)) if f.strip()]
    for form in sorted(set(forms), key=len, reverse=True):
        hit = re.search(rf"(?<![\wåäöÅÄÖ]){re.escape(form)}[\wåäöÅÄÖ]*", sentence, flags=re.IGNORECASE)
        if hit:
            return hit.group(0)
    return base


def _anki_items(vocab):
    items = []
    for v in vocab:
        sentence = v.get("example_sentence_sv", "")
        items.append({
            "word": _surface_form(v.get("word", ""), sentence),
            "sentence": sentence,
            "meaning": v.get("translation_fa", ""),
            "pos": v.get("word_class", ""),
            "forms": v.get("word", ""),
            "examples": [{"sv": sentence, "fa": v.get("example_sentence_fa", "")}],
        })
    return items


# ---------------- ساخت درس از گوشی ----------------
def _trigger_workflow(topic="", grammar="", force=False):
    gh = st.secrets["github"]
    repo = gh.get("repo", DEFAULT_REPO)
    inputs = {"topic": topic, "grammar": grammar, "force": "true" if force else "false"}
    resp = requests.post(
        f"https://api.github.com/repos/{repo}/actions/workflows/{WORKFLOW_FILE}/dispatches",
        headers={"Authorization": f"Bearer {gh['token']}", "Accept": "application/vnd.github+json"},
        json={"ref": gh.get("branch", "main"), "inputs": inputs},
        timeout=20,
    )
    return resp.status_code == 204, resp.text[:300]


def _render_trigger_box():
    if "github" not in st.secrets:
        return
    with st.expander("➕ ساخت درس جدید (با موضوع دلخواه)"):
        with st.form("new_lesson_form"):
            topic = st.text_input("موضوع (به سوئدی یا فارسی)", placeholder="Att köpa en begagnad bil")
            grammar = st.text_input("تمرکز گرامری (اختیاری)", placeholder="Adjektivets böjning")
            if st.form_submit_button("🚀 بساز"):
                ok, msg = _trigger_workflow(topic.strip(), grammar.strip(), force=not topic.strip())
                if ok:
                    st.success("درخواست ارسال شد. حدود ۲-۴ دقیقه دیگه صفحه رو رفرش کن.")
                else:
                    st.error(f"ارسال نشد: {msg}")


# ---------------- نمایش اصلی ----------------
def render(sh, can_fetch=False):
    """کل بخش درس روزانه رو رسم می‌کنه. sh = ماژول sheets_helper."""
    st.subheader("🎧 درس صوتی روزانه")
    try:
        df = sh.read_tab("lessons")
    except Exception as e:
        st.warning(f"خواندن درس‌ها از Google Sheet شکست خورد: {e}")
        return

    if df.empty:
        st.info("هنوز درسی ساخته نشده. اولین درس امشب ساخته می‌شه (یا از GitHub Actions دستی اجراش کن).")
        _render_trigger_box()
        return

    df = df.copy()
    df["شماره"] = pd.to_numeric(df["شماره"], errors="coerce")
    df = df.dropna(subset=["شماره"]).sort_values("شماره", ascending=False).head(30)
    options = df["شماره"].astype(int).tolist()
    labels = {int(r["شماره"]): f"#{int(r['شماره'])} · {r['تاریخ']} · {r['عنوان']}" for _, r in df.iterrows()}
    chosen = st.selectbox("درس:", options, format_func=lambda n: labels[n], key="lesson_pick")
    row = df[df["شماره"] == chosen].iloc[0].to_dict()

    is_today = str(row.get("تاریخ", "")) == _stockholm_today().isoformat()
    badge = CATEGORY_LABELS.get(str(row.get("دسته", "")), str(row.get("دسته", "")))
    st.markdown(f"### {'🆕 ' if is_today else ''}{html.escape(str(row.get('عنوان', '')))}")
    duration = row.get("مدت_دقیقه", "")
    st.caption(f"{badge} · {row.get('موضوع', '')}" + (f" · ⏱ {duration} دقیقه" if duration else ""))

    # واژه‌ها (زودتر محاسبه می‌شه چون کارائوکه برای هاور کلمات بهش نیاز داره)
    vocab = _json_list(row.get("واژه‌ها", ""))
    variant_map = _vocab_variant_map(vocab) if vocab else {}

    karaoke_shown = _render_karaoke(row, variant_map)
    if not karaoke_shown:
        _play_audio(row)

    # گرامر
    examples = _json_list(row.get("مثال‌ها", ""))
    with st.container(border=True):
        st.markdown(f"**📐 گرامر: {html.escape(str(row.get('گرامر', '')))}**")
        st.markdown(_rtl(row.get("توضیح_گرامر", "")), unsafe_allow_html=True)
        for ex in examples:
            st.markdown(
                f"<div dir='ltr' style='margin-top:6px'>🔹 <b>{html.escape(ex.get('sv', ''))}</b></div>"
                + _rtl(ex.get("fa", "")),
                unsafe_allow_html=True,
            )

    # واژه‌ها (vocab بالاتر، قبل از کارائوکه، محاسبه شده)
    if vocab:
        st.markdown(f"**📖 واژه‌های این درس ({len(vocab)})**")
        st.dataframe(
            pd.DataFrame([{
                "کلمه": v.get("word", ""),
                "نوع": v.get("word_class", ""),
                "معنی": v.get("translation_fa", ""),
                "مثال": v.get("example_sentence_sv", ""),
            } for v in vocab]),
            hide_index=True, use_container_width=True,
        )

        try:
            existing_df = sh.read_tab("ordbank")
            existing_words = (
                {srs.normalize_word_answer(w) for w in existing_df["کلمه"] if str(w).strip()}
                if not existing_df.empty and "کلمه" in existing_df.columns else set()
            )
        except Exception:
            existing_words = set()

        word_to_vocab = {v.get("word", ""): v for v in vocab if v.get("word", "")}
        already_added = [w for w in word_to_vocab if srs.normalize_word_answer(w) in existing_words]
        pickable = [w for w in word_to_vocab if w not in already_added]

        if already_added:
            st.caption("قبلاً تو بانک کلمات هستن: " + "، ".join(already_added))

        if pickable:
            def _vocab_pill_label(w):
                meaning = word_to_vocab.get(w, {}).get("translation_fa", "")
                return f"{w} · {meaning}" if meaning else w

            st.pills(
                "کلماتی که می‌خوای به بانک کلمات اضافه بشن رو انتخاب کن:",
                options=pickable,
                format_func=_vocab_pill_label,
                selection_mode="multi",
                default=pickable,
                key=f"lesson_vocab_pills_{chosen}",
            )

            if st.button("➕ افزودن کلمات انتخاب‌شده به بانک کلمات", key=f"lesson_vocab_add_{chosen}"):
                selected = st.session_state.get(f"lesson_vocab_pills_{chosen}", [])
                if not selected:
                    st.info("هیچ کلمه‌ای انتخاب نشده بود.")
                else:
                    added = 0
                    for w in selected:
                        v = word_to_vocab.get(w, {})
                        sentence = (
                            f"{v.get('example_sentence_sv','')}\n{v.get('example_sentence_fa','')}\n"
                            f"(درس روزانه {chosen})"
                        )
                        practice_sentences = (
                            json.dumps([v.get("example_sentence_sv", "")], ensure_ascii=False)
                            if v.get("example_sentence_sv") else ""
                        )
                        meaning_line = f"{v.get('translation_fa','')} ({v.get('word_class','')})".strip()
                        sh.append_row(
                            "ordbank",
                            [str(datetime.date.today()), w, meaning_line, sentence, 0, "", practice_sentences],
                        )
                        added += 1
                    st.success(f"✅ {added} کلمه به بانک کلمات اضافه شد.")
                    st.rerun()
        else:
            st.caption("همه‌ی کلمات این درس قبلاً تو بانک کلمات هستن. ✅")

        if can_fetch:
            try:
                import ankiconnect
                if ankiconnect.is_available() and st.button("🃏 ارسال این واژه‌ها به Anki", key=f"anki_{chosen}"):
                    n = ankiconnect.add_cards(_anki_items(vocab))
                    st.success(f"✅ {n} کارت به Anki اضافه شد.")
            except ImportError:
                pass

    # متن کامل (اگه کارائوکه بالا نشون داده شده باشه، متن همون‌جاست — این فقط fallback و فرمِ افزودنِ دستیه)
    with st.expander("📜 متن کامل درس", expanded=not karaoke_shown):
        if karaoke_shown:
            st.caption("متن کامل بالا، هم‌زمان با صدا هایلایت می‌شه.")
        else:
            if variant_map:
                st.caption("💡 نشونگر موس رو روی کلمه‌های زیرخط‌دار نگه دار تا معنیش رو ببینی.")
            lines = []
            for raw in str(row.get("متن", "")).splitlines():
                line = raw.strip()
                if not line or line.lower() == "[paus]":
                    continue
                line = line.replace("[paus]", "").replace("[PAUS]", "")
                m = SPEAKER_RE.match(line)
                if m:
                    lines.append(
                        f"<p dir='ltr'><b>{html.escape(m.group(1).title())}:</b> "
                        f"{_hover_html(m.group(2), variant_map)}</p>"
                    )
                else:
                    lines.append(f"<p dir='ltr'>{_hover_html(line, variant_map)}</p>")
            st.markdown("".join(lines), unsafe_allow_html=True)

        st.divider()
        st.markdown("**➕ افزودن کلمه‌ی دستی** (کلمه‌ای که از متن کپی کردی رو اینجا پیست کن)")
        manual_key = f"manual_word_input_{chosen}"
        manual_word = st.text_input("کلمه یا عبارت سوئدی:", key=manual_key, placeholder="t.ex. tandläkarmottagning")
        if st.button("🌐 دریافت ترجمه با هوش مصنوعی", key=f"manual_translate_{chosen}"):
            if not manual_word.strip():
                st.info("اول یه کلمه بنویس یا پیست کن.")
            else:
                try:
                    with st.spinner("در حال ترجمه..."):
                        result = coach.translate_word(manual_word.strip())
                    st.session_state[f"manual_word_result_{chosen}"] = result
                except Exception as e:
                    st.error(f"ترجمه شکست خورد: {e}")

        result = st.session_state.get(f"manual_word_result_{chosen}")
        if result:
            with st.form(f"manual_word_form_{chosen}"):
                w = st.text_input("کلمه (با فرم‌های صرفی):", value=result.get("word", ""))
                tr = st.text_input("معنی فارسی:", value=result.get("translation_fa", ""))
                wc = st.selectbox(
                    "نوع کلمه:", ["substantiv", "verb", "adjektiv", "fras"],
                    index=["substantiv", "verb", "adjektiv", "fras"].index(result.get("word_class", "fras"))
                    if result.get("word_class") in ["substantiv", "verb", "adjektiv", "fras"] else 3,
                )
                ex_sv = st.text_input("جمله‌ی مثال (سوئدی):", value=result.get("example_sentence_sv", ""))
                ex_fa = st.text_input("جمله‌ی مثال (فارسی):", value=result.get("example_sentence_fa", ""))
                if st.form_submit_button("➕ افزودن به بانک کلمات"):
                    sentence = f"{ex_sv}\n{ex_fa}\n(از متن درس روزانه {chosen})"
                    practice_sentences = json.dumps([ex_sv], ensure_ascii=False) if ex_sv else ""
                    meaning_line = f"{tr} ({wc})".strip()
                    sh.append_row(
                        "ordbank",
                        [str(datetime.date.today()), w, meaning_line, sentence, 0, "", practice_sentences],
                    )
                    st.session_state.pop(f"manual_word_result_{chosen}", None)
                    st.success(f"✅ «{w}» به بانک کلمات اضافه شد.")
                    st.rerun()

    # ثبت فهم در تب پیشرفت
    with st.form(f"lesson_progress_{chosen}"):
        pct = st.slider("چند درصدش رو بدون متن فهمیدی؟", 0, 100, 60, step=5)
        if st.form_submit_button("✅ گوش دادم — ثبت در پیشرفت"):
            sh.append_row("progress", [str(datetime.date.today()), f"درس {chosen}: {row.get('عنوان', '')}",
                                       pct, f"گرامر: {row.get('گرامر', '')}"])
            st.success("ثبت شد.")

    _render_trigger_box()


def coach_context(sh):
    """یه خلاصه‌ی کوتاه از درس آخر برای system prompt مربی."""
    try:
        df = sh.read_tab("lessons")
    except Exception:
        return ""
    if df.empty:
        return ""
    df = df.copy()
    df["شماره"] = pd.to_numeric(df["شماره"], errors="coerce")
    row = df.sort_values("شماره").iloc[-1]
    words = "، ".join(v.get("word", "") for v in _json_list(row.get("واژه‌ها", "")))
    return (
        f"\nآخرین درس صوتی من ({row.get('تاریخ', '')}): «{row.get('عنوان', '')}» — موقعیت: {row.get('موضوع', '')}.\n"
        f"گرامر درس: {row.get('گرامر', '')}. واژه‌های درس: {words}.\n"
        "اگه خواستم، همین موقعیت رو باهام نقش‌آفرینی کن و از همین واژه‌ها و گرامر استفاده کن.\n"
    )
