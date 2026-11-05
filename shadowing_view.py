"""شادوئینگ: جمله‌های درس‌ها یکی‌یکی پخش می‌شن، مکث می‌کنن تا تکرار کنی (دست‌آزاد)."""
import json

import streamlit as st

import handsfree
import word_audio

MAX_SENTENCES = 25


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

        if st.button("🎧 آماده کن", key="sh_build"):
            sents = []
            for n in picked:
                row = df[df["شماره"] == n].iloc[0].to_dict()
                sents += _sentences(row, use_vocab)
            if shuffle:
                import random
                random.shuffle(sents)
            sents = sents[:MAX_SENTENCES]
            tracks = []
            with st.spinner(f"دارم صدای {len(sents)} جمله رو می‌سازم..."):
                for sv, fa in sents:
                    mp3 = word_audio.synth_swedish(sv)
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
