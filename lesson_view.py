"""
نمایش «درس صوتی روزانه» داخل تب امروز.
درس‌ها رو پایپ‌لاین daily_lesson/ هر شب (GitHub Actions) می‌سازه و تو تب lessons
همون Google Sheet می‌نویسه؛ کلمه‌هاش هم خودکار به ordbank اضافه می‌شن.
"""
import datetime
import html
import json
import re
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import streamlit as st

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

    # واژه‌ها
    vocab = _json_list(row.get("واژه‌ها", ""))
    if vocab:
        st.markdown(f"**📖 واژه‌های این درس ({len(vocab)})** — خودکار به بانک کلمات و مرور SRS اضافه شدن.")
        st.dataframe(
            pd.DataFrame([{
                "کلمه": v.get("word", ""),
                "نوع": v.get("word_class", ""),
                "معنی": v.get("translation_fa", ""),
                "مثال": v.get("example_sentence_sv", ""),
            } for v in vocab]),
            hide_index=True, use_container_width=True,
        )
        if can_fetch:
            try:
                import ankiconnect
                if ankiconnect.is_available() and st.button("🃏 ارسال این واژه‌ها به Anki", key=f"anki_{chosen}"):
                    n = ankiconnect.add_cards(_anki_items(vocab))
                    st.success(f"✅ {n} کارت به Anki اضافه شد.")
            except ImportError:
                pass

    # متن کامل
    with st.expander("📜 متن کامل درس"):
        lines = []
        for raw in str(row.get("متن", "")).splitlines():
            line = raw.strip()
            if not line or line.lower() == "[paus]":
                continue
            line = line.replace("[paus]", "").replace("[PAUS]", "")
            m = SPEAKER_RE.match(line)
            if m:
                lines.append(f"<p dir='ltr'><b>{html.escape(m.group(1).title())}:</b> {html.escape(m.group(2))}</p>")
            else:
                lines.append(f"<p dir='ltr'>{html.escape(line)}</p>")
        st.markdown("".join(lines), unsafe_allow_html=True)

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
