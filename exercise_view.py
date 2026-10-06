"""
تب «📝 تمرین درس» — تمرین‌های خودکارِ هر درس (گرامر / درک مطلب / واژگان)
با تصحیح، ثبت درصد تو «پیشرفت» و ثبت خودکار جواب‌های غلط تو «خطاهای من».
"""
import datetime
import json

import pandas as pd
import streamlit as st

SECTIONS = [
    ("grammar", "🧩 Grammatik · گرامر"),
    ("comprehension", "👂 Läsförståelse · درک مطلب"),
    ("vocab", "📖 Ordförråd · واژگان"),
]
ERR_TYPE = {"grammar": "گرامر", "comprehension": "درک مطلب", "vocab": "واژگان"}


def _load(raw):
    try:
        data = json.loads(raw) if raw else []
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _prompt(kind, q):
    if kind == "grammar":
        return q.get("sentence_sv", "")
    if kind == "comprehension":
        return q.get("question_sv") or q.get("question_fa", "")
    return f"«{q.get('word_sv', '')}» یعنی چی؟"


def _collect(row):
    """-> list of (kind, idx, question) with valid options."""
    items = []
    for kind, _ in SECTIONS:
        for i, q in enumerate(_load(row.get({"grammar": "گرامر", "comprehension": "درک_مطلب", "vocab": "واژگان"}[kind]))):
            opts = q.get("options") or []
            ci = q.get("correct_index", -1)
            if opts and isinstance(ci, int) and 0 <= ci < len(opts):
                items.append((kind, i, q))
    return items


def render(sh):
    st.subheader("📝 Övningar")
    st.caption("تمرین درس — به هر سؤال جواب بده، بعد «Rätta» رو بزن.")

    ex = sh.read_tab("exercises")
    if ex is None or ex.empty:
        st.info("هنوز تمرینی ساخته نشده. از درس بعدی به بعد خودکار ساخته می‌شه.")
        return

    ex = ex.copy()
    ex["شماره_درس"] = pd.to_numeric(ex["شماره_درس"], errors="coerce")
    ex = ex.dropna(subset=["شماره_درس"]).sort_values("شماره_درس", ascending=False)
    if ex.empty:
        st.info("هنوز تمرینی ساخته نشده.")
        return

    titles = {}
    try:
        lessons = sh.read_tab("lessons")
        lessons["شماره"] = pd.to_numeric(lessons["شماره"], errors="coerce")
        titles = {int(r["شماره"]): str(r["عنوان"]) for _, r in lessons.dropna(subset=["شماره"]).iterrows()}
    except Exception:
        pass

    ids = ex["شماره_درس"].astype(int).tolist()
    lid = st.selectbox(
        "Lektion:", ids,
        format_func=lambda i: f"#{i} · {titles.get(i, '')}",
        key="exv_pick",
    )
    row = ex[ex["شماره_درس"] == lid].iloc[0].to_dict()
    items = _collect(row)
    if not items:
        st.warning("تمرین این درس خالیه یا خراب شده.")
        return

    graded_key = f"exv_graded_{lid}"
    logged_key = f"exv_logged_{lid}"
    show = st.session_state.get(graded_key, False)
    st.caption(f"{len(items)} frågor")

    current = None
    for kind, i, q in items:
        if kind != current:
            current = kind
            st.divider()
            st.markdown(f"**{dict(SECTIONS)[kind]}**")
        key = f"exv_{lid}_{kind}_{i}"
        st.markdown(f"<div dir='auto'>{i + 1}. {_prompt(kind, q)}</div>", unsafe_allow_html=True)
        choice = st.radio(" ", q["options"], index=None, key=key, label_visibility="collapsed")
        if show:
            correct = q["options"][q["correct_index"]]
            if choice == correct:
                st.success(f"✅ {correct}")
            else:
                st.error(f"❌ Du valde: {choice or '—'} — Rätt svar: {correct}")
            if kind in ("grammar", "comprehension") and q.get("explanation_fa"):
                st.caption(f"💡 {q['explanation_fa']}")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Rätta", key=f"exv_grade_{lid}", type="primary"):
            st.session_state[graded_key] = True
            st.rerun()
    with c2:
        if st.button("🔄 Börja om", key=f"exv_reset_{lid}"):
            for k in list(st.session_state.keys()):
                if k.startswith(f"exv_{lid}_"):
                    del st.session_state[k]
            st.session_state[graded_key] = False
            st.session_state[logged_key] = False
            st.rerun()

    if not show:
        return

    correct_n, wrong = 0, []
    for kind, i, q in items:
        choice = st.session_state.get(f"exv_{lid}_{kind}_{i}")
        right = q["options"][q["correct_index"]]
        if choice == right:
            correct_n += 1
        else:
            wrong.append((kind, q, choice, right))
    total = len(items)
    pct = round(100 * correct_n / total)
    st.metric("Resultat", f"{correct_n} / {total}", f"{pct}%")

    if st.session_state.get(logged_key):
        st.success("✅ نتیجه ثبت شده.")
        return
    if st.button("📈 Spara resultat · ثبت نتیجه", key=f"exv_log_{lid}"):
        today = str(datetime.date.today())
        try:
            sh.append_row("progress", [today, f"تمرین درس {lid}: {titles.get(lid, '')}", pct, f"{correct_n}/{total}"])
            for kind, q, choice, right in wrong:
                if not choice:
                    continue  # جواب‌نداده رو خطا حساب نمی‌کنیم
                sh.append_row("mina_fel", [today, ERR_TYPE[kind], f"{_prompt(kind, q)} → {choice}", right, 1])
            st.session_state[logged_key] = True
            st.success(f"ثبت شد (+ {sum(1 for w in wrong if w[2])} خطا تو «خطاهای من»).")
        except Exception as exc:
            st.error(f"ثبت نشد: {exc}")
