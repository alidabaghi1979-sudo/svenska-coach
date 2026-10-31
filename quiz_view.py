"""کوییز بعد از درس روزانه — از واژه‌ها و جمله‌های همان درس ساخته می‌شود (بدون Gemini)."""
import datetime
import random
import re

import streamlit as st


def _bare(word):
    w = str(word).strip()
    m = re.match(r"^(en|ett)\s+(\S.*)$", w, flags=re.I)
    return m.group(2) if m else w


def _options(correct, pool, n=4):
    others = [p for p in pool if p != correct]
    random.shuffle(others)
    opts = others[: n - 1] + [correct]
    random.shuffle(opts)
    return opts


def build_questions(vocab, count):
    items = [v for v in vocab if v.get("word") and v.get("translation_fa")]
    if len(items) < 4:
        return []
    fa_pool = [v["translation_fa"] for v in items]
    sv_pool = [v["word"] for v in items]
    bare_pool = [_bare(v["word"]) for v in items]
    qs = []
    for v in items:
        qs.append({"kind": "sv2fa", "prompt": v["word"], "answer": v["translation_fa"],
                   "options": _options(v["translation_fa"], fa_pool), "word": v["word"]})
        qs.append({"kind": "fa2sv", "prompt": v["translation_fa"], "answer": v["word"],
                   "options": _options(v["word"], sv_pool), "word": v["word"]})
        ex = str(v.get("example_sentence_sv", "") or "")
        b = _bare(v["word"])
        m = re.search(r"\b" + re.escape(b) + r"\w*", ex, flags=re.I) if ex and b else None
        if m:
            surface = m.group(0)
            blanked = ex[: m.start()] + "_____" + ex[m.end():]
            pool = bare_pool + [surface]
            qs.append({"kind": "cloze", "prompt": blanked, "answer": surface,
                       "options": _options(surface, pool), "word": v["word"],
                       "hint": v.get("translation_fa", "")})
    random.shuffle(qs)
    # تکراری نشدن یک کلمه پشت‌سرهم تا جای ممکن: فقط حداکثر یک بار از هر نوع برای هر کلمه
    seen, out = set(), []
    for q in qs:
        k = (q["word"], q["kind"])
        if k not in seen:
            seen.add(k)
            out.append(q)
    return out[:count]


def render(sh, chosen, lesson_title, vocab):
    key = f"quiz_{chosen}"
    st.markdown("---")
    with st.expander("🧠 کوییز این درس", expanded=key in st.session_state):
        usable = [v for v in vocab if v.get("word") and v.get("translation_fa")]
        if len(usable) < 4:
            st.caption("این درس واژه‌ی کافی برای کوییز ندارد.")
            return
        state = st.session_state.get(key)

        if state is None:
            maxq = min(30, len(usable) * 3)
            default = min(12, maxq)
            if maxq > 5:
                n = st.slider("تعداد سؤال:", 5, maxq, default, key=f"quiz_n_{chosen}")
            else:
                n = maxq
            if st.button("▶️ شروع کوییز", key=f"quiz_start_{chosen}", type="primary"):
                qs = build_questions(vocab, n)
                st.session_state[key] = {"qs": qs, "i": 0, "answers": [], "checked": False,
                                         "saved": False, "pick": None}
                st.rerun()
            return

        qs = state["qs"]
        total = len(qs)

        if state["i"] >= total:
            correct = sum(1 for a in state["answers"] if a["ok"])
            wrong = [a for a in state["answers"] if not a["ok"]]
            st.success(f"نتیجه: {correct} از {total}")
            if not state["saved"]:
                today = str(datetime.date.today())
                try:
                    if wrong:
                        sh.append_rows("mina_fel", [
                            [today, f"واژگان (کوییز درس {chosen})", a["picked"], a["answer"], 1]
                            for a in wrong
                        ])
                except Exception as e:
                    st.warning(f"ثبت خطاها شکست خورد: {e}")
                try:
                    sh.increment_review_log(today, total, correct)
                except Exception:
                    pass
                try:
                    sh.append_row("progress", [today, f"کوییز درس {chosen}: {lesson_title}",
                                               round(100 * correct / max(total, 1)), f"{correct}/{total}"])
                except Exception:
                    pass
                state["saved"] = True
            if wrong:
                st.caption(f"{len(wrong)} غلط به «Mina fel» اضافه شد:")
                for a in wrong:
                    st.markdown(f"- ❌ {a['picked']} → ✅ **{a['answer']}**")
            else:
                st.balloons()
            if st.button("🔁 کوییز دوباره", key=f"quiz_again_{chosen}"):
                del st.session_state[key]
                st.rerun()
            return

        q = qs[state["i"]]
        st.progress(state["i"] / total, text=f"سؤال {state['i'] + 1} از {total}")
        if q["kind"] == "sv2fa":
            st.markdown(f"### {q['prompt']}")
            st.caption("معنی فارسی‌اش کدام است؟")
        elif q["kind"] == "fa2sv":
            st.markdown(f"### {q['prompt']}")
            st.caption("کدام کلمه‌ی سوئدی است؟")
        else:
            st.markdown(f"### {q['prompt']}")
            st.caption(f"جای خالی را پر کن (معنی کلمه: {q.get('hint', '')})")

        if not state["checked"]:
            pick = st.radio("جواب:", q["options"], index=None, key=f"quiz_pick_{chosen}_{state['i']}")
            if st.button("✅ تأیید", key=f"quiz_ok_{chosen}_{state['i']}"):
                if pick is None:
                    st.warning("اول یکی را انتخاب کن.")
                else:
                    state["answers"].append({"ok": pick == q["answer"], "picked": pick,
                                             "answer": q["answer"], "word": q["word"]})
                    state["checked"] = True
                    st.rerun()
        else:
            last = state["answers"][-1]
            if last["ok"]:
                st.success(f"✅ درست: {q['answer']}")
            else:
                st.error(f"❌ جوابت: {last['picked']}\n\n✅ درست: {q['answer']}")
            if st.button("بعدی ➡️", key=f"quiz_next_{chosen}_{state['i']}", type="primary"):
                state["i"] += 1
                state["checked"] = False
                st.rerun()
