"""گزارش هفتگی: ۷ روز اخیر در برابر ۷ روز قبل از آن — فقط از داده‌های شیت (بدون LLM)."""
import datetime

import pandas as pd
import streamlit as st


def _dates(df, col):
    if df is None or df.empty or col not in df.columns:
        return pd.Series([], dtype="object")
    return pd.to_datetime(df[col].astype(str).str[:10], errors="coerce").dt.date


def _delta(cur, prev, suffix=""):
    d = cur - prev
    if d == 0:
        return None
    return f"{d:+d}{suffix}"


def render(sh):
    today = datetime.date.today()
    w1 = today - datetime.timedelta(days=6)           # ۷ روز اخیر: w1..today
    p1, p2 = w1 - datetime.timedelta(days=7), w1 - datetime.timedelta(days=1)

    def tab(name):
        try:
            return sh.read_tab(name)
        except Exception:
            return pd.DataFrame()

    def in_cur(d):
        return d is not None and not pd.isna(d) and w1 <= d <= today

    def in_prev(d):
        return d is not None and not pd.isna(d) and p1 <= d <= p2

    # مرور کارت‌ها
    log = tab("review_log")
    cards = {"cur": 0, "prev": 0}
    right = {"cur": 0, "prev": 0}
    days = {"cur": set(), "prev": set()}
    if not log.empty and "تعداد_کارت" in log.columns:
        ds = _dates(log, "تاریخ")
        n = pd.to_numeric(log["تعداد_کارت"], errors="coerce").fillna(0).astype(int)
        r = pd.to_numeric(log.get("تعداد_درست"), errors="coerce").fillna(0).astype(int)
        for d, a, b in zip(ds, n, r):
            k = "cur" if in_cur(d) else "prev" if in_prev(d) else None
            if k:
                cards[k] += a
                right[k] += b
                if a > 0:
                    days[k].add(d)

    # کلمه‌های جدید، خطاهای جدید، درس‌ها و کوییزها
    ob = tab("ordbank")
    new_words = {"cur": 0, "prev": 0}
    for d in _dates(ob, "تاریخ"):
        if in_cur(d):
            new_words["cur"] += 1
        elif in_prev(d):
            new_words["prev"] += 1

    mf = tab("mina_fel")
    new_err = {"cur": 0, "prev": 0}
    err_types = {}
    for d, t in zip(_dates(mf, "اولین_بار"), mf["نوع_خطا"] if "نوع_خطا" in mf.columns else []):
        if in_cur(d):
            new_err["cur"] += 1
            t = str(t).split("(")[0].strip() or "نامشخص"
            err_types[t] = err_types.get(t, 0) + 1
        elif in_prev(d):
            new_err["prev"] += 1

    pg = tab("progress")
    lessons = {"cur": 0, "prev": 0}
    quiz_scores = []
    if not pg.empty and "موضوع" in pg.columns:
        for d, t, p in zip(_dates(pg, "تاریخ"), pg["موضوع"].astype(str),
                           pd.to_numeric(pg.get("درصد_فهم"), errors="coerce")):
            k = "cur" if in_cur(d) else "prev" if in_prev(d) else None
            if not k:
                continue
            if t.startswith("کوییز"):
                if k == "cur" and not pd.isna(p):
                    quiz_scores.append(float(p))
            elif t.startswith("درس"):
                lessons[k] += 1

    acc = lambda k: round(100 * right[k] / cards[k]) if cards[k] else 0

    with st.expander("📊 گزارش هفته (۷ روز اخیر)"):
        c1, c2, c3 = st.columns(3)
        c1.metric("کارت مرور", cards["cur"], _delta(cards["cur"], cards["prev"]))
        c2.metric("درصد درست", f"{acc('cur')}٪", _delta(acc("cur"), acc("prev"), "٪") if cards["prev"] else None)
        c3.metric("روز فعال", f"{len(days['cur'])}/7", _delta(len(days["cur"]), len(days["prev"])))
        c4, c5, c6 = st.columns(3)
        c4.metric("کلمه‌ی جدید", new_words["cur"], _delta(new_words["cur"], new_words["prev"]))
        c5.metric("درس شنیده‌شده", lessons["cur"], _delta(lessons["cur"], lessons["prev"]))
        c6.metric("خطای جدید", new_err["cur"], _delta(new_err["cur"], new_err["prev"]), delta_color="inverse")

        if quiz_scores:
            st.caption(f"🧠 میانگین نمره‌ی کوییزها: {round(sum(quiz_scores) / len(quiz_scores))}٪ ({len(quiz_scores)} کوییز)")
        if err_types:
            top = sorted(err_types.items(), key=lambda x: -x[1])[:3]
            st.caption("⚠️ بیشترین خطاها: " + "، ".join(f"{t} ({n})" for t, n in top))

        notes = []
        if cards["cur"] == 0:
            notes.append("این هفته مرور نکردی — امروز ۵ کارت هم کافی است تا استریک شروع شود.")
        else:
            if len(days["cur"]) >= 5:
                notes.append("ثبات خوبی داری: ۵ روز یا بیشتر فعال بودی.")
            elif len(days["cur"]) <= 2:
                notes.append("روزهای فعال کم بود؛ هدف را ۵ کارت در روز بگذار ولی هر روز.")
            if acc("cur") < 70:
                notes.append("درصد درست زیر ۷۰٪ است؛ ممکن است کارت‌های سخت زیاد شده باشند.")
            if cards["prev"] and cards["cur"] > cards["prev"]:
                notes.append("نسبت به هفته‌ی قبل بیشتر مرور کردی. 👏")
        for n in notes:
            st.markdown(f"- {n}")
