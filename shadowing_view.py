"""شادوئینگ: جمله‌های درس‌ها یکی‌یکی پخش می‌شن، مکث می‌کنن تا تکرار کنی (دست‌آزاد)."""
import hashlib
import json
import re
import os
import tempfile

import streamlit as st

import handsfree
import pronunciation
import word_audio

MAX_SENTENCES = 25

_DIR = os.path.join(tempfile.gettempdir(), "svenska_shadow")


def _tts(sv):
    """صدای جمله؛ اول از کش دیسک (زنده می‌مونه حتی اگه کش Streamlit خالی بشه)، بعد Azure."""
    try:
        os.makedirs(_DIR, exist_ok=True)
        path = os.path.join(_DIR, hashlib.sha1(sv.encode("utf-8")).hexdigest() + ".mp3")
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
    except OSError:
        path = None
    mp3 = word_audio.synth_swedish(sv)
    if mp3 and path:
        try:
            with open(path, "wb") as f:
                f.write(mp3)
        except OSError:
            pass
    return mp3



def _jl(raw):
    try:
        v = json.loads(raw) if isinstance(raw, str) and raw.strip() else []
        return v if isinstance(v, list) else []
    except json.JSONDecodeError:
        return []


def _sentences(row, use_vocab):
    out, seen = [], set()

    def add(sv, fa):
        sv = str(sv or "").strip()
        if sv and sv.lower() not in seen:
            seen.add(sv.lower())
            out.append((sv, str(fa or "").strip()))

    for ex in _jl(row.get("مثال‌ها", "")):
        if isinstance(ex, dict):
            add(ex.get("sv"), ex.get("fa"))
    if use_vocab:
        for v in _jl(row.get("واژه‌ها", "")):
            if isinstance(v, dict):
                add(v.get("example_sentence_sv"), v.get("example_sentence_fa"))
    return out


def _shorten(sents, max_words, split_long):
    """جمله‌های بلند را (اگه خواسته شد) سر ویرگول/نقطه‌ویرگول تکه می‌کنه و فقط کوتاه‌ها را نگه می‌داره."""
    out, seen = [], set()
    for sv, fa in sents:
        n = len(sv.split())
        if n <= max_words:
            cands = [(sv, fa)]
        elif split_long:
            parts = [p.strip(" ,;:.-") for p in re.split(r"[,;:]", sv)]
            parts = [p for p in parts if len(p.split()) >= 3]
            cands = [(p, "") for p in parts if len(p.split()) <= max_words]
        else:
            cands = []
        for c in cands:
            k = c[0].lower()
            if k not in seen:
                seen.add(k)
                out.append(c)
    return out


def render(df, options, labels):
    with st.expander("🗣 شادوئینگ — جمله‌ها رو بشنو و تکرار کن (دست‌آزاد)"):
        if not word_audio.tts_available():
            st.caption("صدای Azure تنظیم نشده.")
            return
        st.caption("هر جمله پخش می‌شه، بعد مکث می‌کنه تا خودت بلند تکرار کنی. فقط یک بار ▶ رو بزن.")
        picked = st.multiselect(
            "کدوم درس‌ها؟ (تا ۳ تا)", options, default=options[:1], max_selections=3,
            format_func=lambda n: labels[n], key="sh_pick",
        )
        c1, c2, c3 = st.columns(3)
        rep = c1.selectbox("هر جمله چند بار؟", [1, 2, 3], index=1, key="sh_rep")
        auto = c2.checkbox("مکث خودکار (به اندازه‌ی طول جمله)", value=True, key="sh_auto")
        if auto:
            factor = c2.slider("مکث = چند برابر طول جمله", 1.0, 3.0, 1.5, 0.25, key="sh_factor")
            gap = 6
        else:
            factor = 0
            gap = c2.slider("مکث تکرار (ثانیه)", 2, 15, 6, key="sh_gap")
        show_fa = c3.checkbox("ترجمه‌ی فارسی نشان بده", value=True, key="sh_fa")
        use_vocab = st.checkbox("جمله‌های مثالِ واژه‌ها هم باشد", value=True, key="sh_vocab")
        shuffle = st.checkbox("ترتیب تصادفی", value=False, key="sh_shuffle")
        max_words = st.slider("حداکثر طول جمله (کلمه)", 4, 20, 8, key="sh_maxw")
        split_long = st.checkbox("جمله‌های بلندتر را به تکه‌های کوتاه ببُر", value=True, key="sh_split")

        sig = (tuple(picked), use_vocab, shuffle, show_fa, max_words, split_long)
        pressed = st.button("🎧 آماده کن", key="sh_build")
        same = st.session_state.get("sh_sig") == sig and bool(st.session_state.get("sh_tracks"))
        if pressed and same:
            # انتخاب‌ها عوض نشده؛ صدا آماده است — فقط تنظیم تکرار/مکث رو به‌روز کن
            st.session_state["sh_params"] = (rep, gap, factor)
        elif pressed:
            st.session_state["sh_sig"] = sig
            sents = []
            for n in picked:
                row = df[df["شماره"] == n].iloc[0].to_dict()
                sents += _sentences(row, use_vocab)
            before = len(sents)
            sents = _shorten(sents, max_words, split_long)
            if before and not sents:
                st.warning("همه‌ی جمله‌ها از حد طول بلندتر بودند؛ حداکثر طول را بالاتر ببر.")
            if shuffle:
                import random
                random.shuffle(sents)
            sents = sents[:MAX_SENTENCES]
            tracks = []
            with st.spinner(f"دارم صدای {len(sents)} جمله رو می‌سازم..."):
                st.session_state["sh_sents"] = [sv for sv, _ in sents]
                for sv, fa in sents:
                    mp3 = _tts(sv)
                    if mp3:
                        label = sv + (f"\n{fa}" if show_fa and fa else "")
                        tracks.append((label, mp3))
            if not tracks:
                st.warning("جمله‌ای پیدا نشد یا ساخت صدا شکست خورد.")
            st.session_state["sh_tracks"] = tracks
            st.session_state["sh_params"] = (rep, gap, factor)

        tracks = st.session_state.get("sh_tracks")
        if tracks:
            if handsfree.total_mb(tracks) > handsfree.MAX_TOTAL_MB:
                st.warning("حجم صدا زیاده؛ درس‌ها یا جمله‌ها رو کمتر کن.")
            else:
                r, g, f = st.session_state.get("sh_params", (rep, gap, factor))
                st.caption(f"{len(tracks)} جمله آماده است.")
                handsfree.player(tracks, repeat=r, gap=g, height=380, gap_factor=f)

    render_practice(st.session_state.get("sh_sents", []))


def _log_weak_to_mistakes(ref, weak):
    """کلمه‌های ضعیفِ تلفظ → تب Mina fel (یک بار برای هر کلمه؛ تکراری اضافه نمی‌شه)."""
    import datetime
    import sheets_helper as sh
    if not weak:
        return
    try:
        df = sh.read_tab("mina_fel")
    except Exception:
        return
    seen = set()
    if not df.empty and "نوع_خطا" in df.columns and "غلط" in df.columns:
        for t, w in zip(df["نوع_خطا"].astype(str), df["غلط"].astype(str)):
            if t.startswith("تلفظ"):
                seen.add(w.split(" ")[0].lower())
    rows = [[str(datetime.date.today()), "تلفظ (شادوئینگ)", f"{w['word']} (نمره {w['acc']})", ref, 1]
            for w in weak if str(w["word"]).lower() not in seen]
    if rows:
        sh.append_rows("mina_fel", rows)


def _color(acc, err):
    if err == "Omission":
        return "#C0392B"
    if acc is None:
        return "#14293D"
    return "#1E8E3E" if acc >= pronunciation.GOOD else "#B7791F" if acc >= pronunciation.OK else "#C0392B"


def render_practice(sentences):
    """تمرین تلفظ: ضبط → Azure → جمله‌ی رنگی + نمره‌ها + نکته‌ی فارسی. نتیجه تو شیت ثبت می‌شه."""
    import datetime
    import html as _html

    with st.expander("🎤 تمرین تلفظ — بگو و ارزیابی بگیر"):
        if not sentences:
            st.caption("اول بالا «آماده کن» رو بزن تا جمله‌ها بیان.")
            return
        ref = st.selectbox("جمله:", sentences, key="pa_ref")
        st.markdown(f"<div dir='ltr' style='font-size:20px;font-weight:600;margin:6px 0'>{_html.escape(ref)}</div>",
                    unsafe_allow_html=True)
        mp3 = word_audio.synth_swedish(ref)
        if mp3:
            st.audio(mp3, format="audio/mp3")
        nonce = st.session_state.get("pa_nonce", 0)
        audio = st.audio_input("بگو:", key=f"pa_audio_{nonce}")
        if st.session_state.get("pa_result") is None:
            def _skip():
                i = sentences.index(ref) if ref in sentences else 0
                st.session_state["pa_ref"] = sentences[(i + 1) % len(sentences)]
                st.session_state["pa_nonce"] = st.session_state.get("pa_nonce", 0) + 1
            st.button("⏭ رد کن، جمله‌ی بعد", key="pa_skip", on_click=_skip)
        if audio is not None and st.button("🔎 ارزیابی کن", key="pa_go", type="primary"):
            try:
                with st.spinner("دارم گوش می‌دم..."):
                    res = pronunciation.assess(audio.getvalue(), ref)
                summ = pronunciation.summarize(res)
                st.session_state["pa_result"] = {"ref": ref, "summ": summ, "tips": None}
                weak = pronunciation.weak_words(summ)
                try:
                    import sheets_helper as _sh
                    o = summ["overall"]
                    _sh.append_row("pronunciation_log", [
                        str(datetime.date.today()), ref, o["pron"], o["acc"], o["flu"], o["comp"],
                        "، ".join(w["word"] for w in weak)])
                except Exception:
                    pass
                try:
                    _log_weak_to_mistakes(ref, weak)
                except Exception:
                    pass
            except Exception as e:
                st.session_state.pop("pa_result", None)
                st.error(f"{e}")

        r = st.session_state.get("pa_result")
        if not r or r["ref"] != ref:
            return
        summ = r["summ"]
        spans = " ".join(
            f"<span style='color:{_color(w['acc'], w['err'])};font-weight:700' title='{w['acc']}'>"
            f"{_html.escape(str(w['word']))}</span>" for w in summ["words"] if w["err"] != "Insertion"
        )
        st.markdown(f"<div dir='ltr' style='font-size:22px;line-height:1.8;margin:8px 0'>{spans}</div>",
                    unsafe_allow_html=True)
        o = summ["overall"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("کلی", o["pron"])
        c2.metric("دقت", o["acc"])
        c3.metric("روانی", o["flu"])
        c4.metric("کامل بودن", o["comp"])
        st.caption("سبز ≥۸۰ · زرد ۶۰–۷۹ · قرمز زیر ۶۰ یا جاافتاده. نمره‌ها تخمین ماشین‌اند؛ برای مقایسه‌ی خودت با خودت مفیدند.")

        weak = pronunciation.weak_words(summ)
        if not weak:
            st.success("همه‌ی کلمه‌ها خوب بود 👏")
        else:
            st.markdown(
                "**کلمه‌های ضعیف:** " + " ".join(
                    f"<span dir='ltr' style='display:inline-block;margin:0 4px;padding:1px 8px;"
                    f"border-radius:10px;background:#FDECEA;color:#C0392B;font-weight:700'>{_html.escape(str(w['word']))}</span>"
                    for w in weak),
                unsafe_allow_html=True)
            if r["tips"] is None and st.button("💡 نکته‌ی تلفظ بگیر", key="pa_tips"):
                try:
                    with st.spinner("..."):
                        r["tips"] = pronunciation.tips(ref, weak)
                    st.rerun()
                except Exception as e:
                    st.error(f"{e}")
            if r["tips"]:
                import re as _re
                rows = []
                for line in r["tips"].splitlines():
                    line = _re.sub(r"[*_`#]+", "", line).strip(" -•\t")
                    if not line:
                        continue
                    head, sep, rest = line.partition(":")
                    if sep and len(head) < 30:
                        body = (f"<b dir='ltr' style='unicode-bidi:isolate'>{_html.escape(head)}</b>: "
                                f"{_html.escape(rest.strip())}")
                    else:
                        body = _html.escape(line)
                    rows.append(f"<div dir='rtl' style='text-align:right;margin:8px 0;line-height:1.9'>{body}</div>")
                st.markdown("".join(rows), unsafe_allow_html=True)

        def _again():
            st.session_state["pa_nonce"] = st.session_state.get("pa_nonce", 0) + 1
            st.session_state.pop("pa_result", None)

        def _step(delta):
            i = sentences.index(ref) if ref in sentences else 0
            st.session_state["pa_ref"] = sentences[(i + delta) % len(sentences)]
            _again()

        b1, b2 = st.columns(2)
        b1.button("🔁 دوباره بگو", key="pa_again", on_click=_again, use_container_width=True)
        b2.button("⏭ جمله‌ی بعد", key="pa_next", on_click=_step, args=(1,),
                  use_container_width=True, type="primary")
