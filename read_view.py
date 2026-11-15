"""تب Läs: متن سوئدی را بچسبان → رنگ‌بندی بر اساس Ordbank، لمس کلمه = ترجمه و افزودن، خواندن با صدا."""
import html
import re

import streamlit as st

import coach
import handsfree
import kort_view
import photo_view
import shadowing_view
import srs

WORD_RE = re.compile(r"[A-Za-zÅÄÖåäöÉéÜü]+(?:-[A-Za-zÅÄÖåäöÉéÜü]+)*")
KNOWN_LEVEL = 3          # سطح لایتنر از این به بالا = «بلد»
MAX_CHARS = 6000
MAX_SENTENCES = 25
MAX_PILLS = 80
DEFAULT_READ_DECK = "Läs"

_DEF_SUFFIXES = ("en", "n", "et", "t", "na", "a", "ar", "er", "or", "s")


def _norm(w):
    return str(w or "").strip().lower()


def build_lookup(records):
    """دیکشنری شکل‌کلمه → سطح (کمترین سطح اگر تکراری)."""
    look = {}
    for r in records:
        try:
            lvl = int(float(r.get("سطح", 0) or 0))
        except (ValueError, TypeError):
            lvl = 0
        forms = set(srs.word_forms(r.get("کلمه", "")))
        for f in list(forms):
            for suf in ("en", "n", "et", "t", "na"):
                forms.add(f + suf)
            if f.endswith("a"):
                forms.add(f[:-1] + "an")
        for f in forms:
            if f and (f not in look or lvl < look[f]):
                look[f] = lvl
    return look


def status_of(word, look):
    """'known' / 'learning' / 'unknown'."""
    w = _norm(word)
    lvl = look.get(w)
    if lvl is None and "-" in w:
        parts = [look.get(p) for p in w.split("-")]
        if parts and all(p is not None for p in parts):
            lvl = min(parts)
    if lvl is None:
        return "unknown"
    return "known" if lvl >= KNOWN_LEVEL else "learning"


def analyze(text, look):
    """(tokens[(نوع, متن)], آمار, لیست کلمه‌های نامعلوم به ترتیب ظهور)"""
    tokens, counts, unknown_order, seen = [], {"known": 0, "learning": 0, "unknown": 0}, [], set()
    pos = 0
    for m in WORD_RE.finditer(text):
        if m.start() > pos:
            tokens.append((None, text[pos:m.start()]))
        w = m.group(0)
        st_ = status_of(w, look)
        counts[st_] += 1
        if st_ == "unknown":
            k = _norm(w)
            if k not in seen and len(k) > 1:
                seen.add(k)
                unknown_order.append(k)
        tokens.append((st_, w))
        pos = m.end()
    if pos < len(text):
        tokens.append((None, text[pos:]))
    return tokens, counts, unknown_order


_STYLE = {
    "known": "background:#c8e6c9;color:#1b3a1e;",
    "learning": "background:#fff59d;color:#4a3f00;",
    "unknown": "border-bottom:2px dotted #888;",
}


def render_html(tokens, highlight=None):
    out = []
    for kind, txt in tokens:
        e = html.escape(txt).replace("\n", "<br>")
        if kind is None:
            out.append(e)
            continue
        style = _STYLE[kind]
        if highlight and _norm(txt) == highlight:
            style += "outline:2px solid #e53935;"
        out.append(f'<span style="{style}border-radius:4px;padding:0 2px;">{e}</span>')
    return (
        '<div dir="ltr" style="font-size:1.15rem;line-height:2;text-align:left;">'
        + "".join(out) + "</div>"
    )


def split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if len(p.split()) >= 2]


def _pick_word(pick):
    if pick:
        st.session_state["lr_word"] = pick


def render(sh):
    st.subheader("📚 Läs · خواندن")
    st.caption("متن سوئدی (از کتاب، خبر، سایت) را بچسبان. سبز = بلدی، زرد = در حال یادگیری، خط‌چین = ناشناخته.")

    try:
        ob = sh.read_tab("ordbank")
        recs = ob.to_dict("records") if not ob.empty else []
    except Exception as e:
        st.error(f"خواندن بانک کلمات شکست خورد: {e}")
        return
    look = build_lookup(recs)

    photo_view.render(sh, recs)

    text = st.text_area("متن:", height=200, key="lr_text", placeholder="Klistra in en svensk text här...")
    text = (text or "").strip()
    if len(text) > MAX_CHARS:
        st.warning(f"فقط {MAX_CHARS} حرف اول بررسی می‌شود.")
        text = text[:MAX_CHARS]
    if not text:
        st.info("یک متن بچسبان تا شروع کنیم.")
        return

    tokens, counts, unknown = analyze(text, look)
    total = sum(counts.values())
    if not total:
        st.warning("کلمه‌ی سوئدی‌ای پیدا نشد.")
        return
    cov = round(100 * (counts["known"] + counts["learning"]) / total)
    c1, c2, c3 = st.columns(3)
    c1.metric("کلمه‌های متن", total)
    c2.metric("می‌شناسی", f"{cov}٪")
    c3.metric("ناشناخته (یکتا)", len(unknown))
    if cov >= 95:
        st.success("این متن برای تو راحت است؛ برای خواندن روان عالی.")
    elif cov >= 80:
        st.info("سطح مناسب برای یادگیری (۸۰ تا ۹۵٪ آشنا).")
    else:
        st.warning("کمی سخت است؛ کلمه‌های ناشناخته را اول یاد بگیر یا متن ساده‌تری بردار.")

    st.markdown(render_html(tokens, st.session_state.get("lr_word")), unsafe_allow_html=True)
    st.divider()

    # ---------- لمس کلمه ----------
    st.markdown("### 👆 کلمه‌ی ناشناخته را انتخاب کن")
    if unknown:
        shown = unknown[:MAX_PILLS]
        if hasattr(st, "pills"):
            pick = st.pills("کلمه‌ها:", shown, key="lr_pill", label_visibility="collapsed")
        else:
            pick = st.selectbox("کلمه‌ها:", [""] + shown, key="lr_pill_sel") or None
        if pick:
            st.session_state["lr_word"] = pick
        if len(unknown) > MAX_PILLS:
            st.caption(f"{len(unknown) - MAX_PILLS} کلمه‌ی دیگر هم هست؛ از کادر زیر تایپ کن.")
    else:
        st.caption("همه‌ی کلمه‌ها را می‌شناسی!")
    typed = st.text_input("یا هر کلمه‌ای را تایپ کن:", key="lr_typed")
    if typed.strip():
        st.session_state["lr_word"] = _norm(typed)

    word = st.session_state.get("lr_word")
    if word:
        _word_panel(sh, word, text, recs)

    st.divider()
    _audio_panel(text)


def _context_sentence(word, text):
    for s in re.split(r"(?<=[.!?])\s+|\n+", text):
        if re.search(rf"\b{re.escape(word)}\b", s, re.IGNORECASE):
            return s.strip()
    return ""


def _word_panel(sh, word, text, recs):
    key = f"lr_tr_{word}"
    with st.container(border=True):
        st.markdown(f"#### {word}")
        ctx = _context_sentence(word, text)
        if ctx:
            st.caption(f"در متن: {ctx}")
        if key not in st.session_state:
            try:
                with st.spinner("..."):
                    st.session_state[key] = coach.translate_word(word)
            except Exception as e:
                st.error(f"ترجمه شکست خورد: {e}")
                return
        r = st.session_state[key]
        wc = r.get("word_class", "fras")
        st.markdown(f"**{r.get('translation_fa', '')}** · _{wc}_")
        st.markdown(f"`{r.get('word', word)}`")
        if r.get("example_sentence_sv"):
            st.markdown(f"🔹 {r['example_sentence_sv']}")
            st.caption(r.get("example_sentence_fa", ""))
        mp3 = shadowing_view._tts(r.get("word", word))
        if mp3:
            st.audio(mp3, format="audio/mp3")

        existing = {srs.normalize_word_answer(x.get("کلمه", "")) for x in recs}
        if srs.normalize_word_answer(r.get("word", word)) in existing:
            st.info("این کلمه از قبل در بانک کلمات هست.")
            return
        decks = sorted({srs.deck_of(x) for x in recs})
        opts = decks if DEFAULT_READ_DECK in decks else [DEFAULT_READ_DECK] + decks
        deck = st.selectbox("دسته:", opts, key="lr_deck")
        if st.button("➕ به بانک کلمات", key=f"lr_add_{word}", type="primary"):
            sv = ctx or r.get("example_sentence_sv", "")
            fa = "" if ctx else r.get("example_sentence_fa", "")
            try:
                row = kort_view._ordbank_row(
                    deck, r.get("word", word), r.get("translation_fa", ""), wc, sv, fa, note="(از متن Läs)")
                sh.append_row("ordbank", row)
                st.session_state.pop("lr_word", None)
                st.session_state.pop("lr_pill", None)
                st.success("اضافه شد ✅ (بعد از تغییر متن رنگ کلمه عوض می‌شود)")
            except Exception as e:
                st.error(f"ذخیره شکست خورد: {e}")


def _audio_panel(text):
    st.markdown("### 🔊 گوش دادن")
    sents = split_sentences(text)[:MAX_SENTENCES]
    if not sents:
        return
    c1, c2 = st.columns(2)
    rep = c1.number_input("تکرار هر جمله", 1, 5, 1, key="lr_rep")
    gap = c2.number_input("مکث (ثانیه)", 0, 15, 2, key="lr_gap")
    if st.button("🎧 ساخت صدای دست‌آزاد", key="lr_build"):
        tracks = []
        with st.spinner(f"ساخت صدای {len(sents)} جمله..."):
            for i, s in enumerate(sents, 1):
                mp3 = shadowing_view._tts(s)
                if mp3:
                    tracks.append((f"{i}. {s}", mp3))
        if not tracks:
            st.error("ساخت صدا ممکن نشد (کلید Azure؟).")
        else:
            st.session_state["lr_tracks"] = (tracks, int(rep), float(gap), text)
    pack = st.session_state.get("lr_tracks")
    if pack and pack[3] == text:
        tracks, r, g, _ = pack
        if handsfree.total_mb(tracks) > handsfree.MAX_TOTAL_MB:
            st.warning("حجم صدا زیاد است؛ متن را کوتاه‌تر کن.")
        else:
            handsfree.player(tracks, repeat=r, gap=g, height=380)
