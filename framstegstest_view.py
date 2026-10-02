"""
تب «📝 خودآزمایی» — تست‌های پیشرفتِ Rivstart A1+A2 (Framstegstester) با تصحیح خودکار.
"""
import re

import streamlit as st

from framstegstest import FRAMSTEGSTESTER


def _normalize(s):
    s = str(s or "").strip().lower()
    s = s.replace("å", "å").replace("ä", "ä").replace("ö", "ö")  # noop, keeps chars explicit
    s = re.sub(r"[.!?]+$", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _is_correct(item, given):
    accepted = [item.get("answer", "")] + list(item.get("accept", []))
    given_n = _normalize(given)
    if not given_n:
        return False
    return any(given_n == _normalize(a) for a in accepted)


def render(sh=None):
    st.subheader("📝 خودآزمایی (Framstegstest)")
    st.caption("از کتاب Rivstart A1+A2 — به هر بخش جواب بده، بعد «تصحیح کن» رو بزن تا نمره ببینی.")

    test_ids = sorted(FRAMSTEGSTESTER.keys())
    chosen_id = st.selectbox(
        "تست:", test_ids,
        format_func=lambda i: f"{FRAMSTEGSTESTER[i]['title']} — {FRAMSTEGSTESTER[i]['subtitle']}",
        key="framstegstest_pick",
    )
    test = FRAMSTEGSTESTER[chosen_id]
    graded_key = f"framstegstest_graded_{chosen_id}"

    total_items = sum(len(s["items"]) for s in test["sections"])
    st.caption(f"مجموع: {total_items} سؤال")

    for section in test["sections"]:
        st.divider()
        st.markdown(f"**{section['num']}. {section['title']}**")
        st.caption(section.get("instructions", ""))
        if section.get("passage"):
            st.markdown(
                f"<div dir='ltr' style='background:rgba(127,127,127,.08); padding:10px; "
                f"border-radius:8px; line-height:1.8;'>{section['passage']}</div>",
                unsafe_allow_html=True,
            )
            st.write("")

        show_results = st.session_state.get(graded_key, False)
        for i, item in enumerate(section["items"]):
            key = f"fs_{chosen_id}_{section['num']}_{i}"
            if section["type"] == "mcq":
                st.markdown(f"<div dir='ltr'>{item['prompt']}</div>", unsafe_allow_html=True)
                choice = st.radio(
                    " ", item["options"], index=None, key=key, label_visibility="collapsed",
                )
                if show_results:
                    correct_opt = item["options"][item["correct"]]
                    if choice == correct_opt:
                        st.success(f"✅ {correct_opt}")
                    else:
                        st.error(f"❌ تو زدی: {choice or '—'} — جواب درست: {correct_opt}")
            else:
                col1, col2 = st.columns([3, 2])
                with col1:
                    st.markdown(f"<div dir='ltr'>{item['prompt']}</div>", unsafe_allow_html=True)
                with col2:
                    given = st.text_input(" ", key=key, label_visibility="collapsed")
                if show_results:
                    if _is_correct(item, given):
                        st.success(f"✅ {item['answer']}")
                    else:
                        st.error(f"❌ تو نوشتی: «{given or '—'}» — جواب درست: {item['answer']}")

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("✅ تصحیح کن", key=f"fs_grade_{chosen_id}", type="primary"):
            st.session_state[graded_key] = True
            st.rerun()
    with col_b:
        if st.button("🔄 شروع دوباره", key=f"fs_reset_{chosen_id}"):
            for k in list(st.session_state.keys()):
                if k.startswith(f"fs_{chosen_id}_"):
                    del st.session_state[k]
            st.session_state[graded_key] = False
            st.rerun()

    if st.session_state.get(graded_key, False):
        correct_count = 0
        for section in test["sections"]:
            for i, item in enumerate(section["items"]):
                key = f"fs_{chosen_id}_{section['num']}_{i}"
                if section["type"] == "mcq":
                    choice = st.session_state.get(key)
                    if choice == item["options"][item["correct"]]:
                        correct_count += 1
                else:
                    if _is_correct(item, st.session_state.get(key, "")):
                        correct_count += 1
        pct = round(100 * correct_count / total_items) if total_items else 0
        st.metric("نمره", f"{correct_count} / {total_items}", f"{pct}%")
        if sh is not None:
            try:
                import datetime
                if st.button("📈 ثبت نمره در تب پیشرفت", key=f"fs_log_{chosen_id}"):
                    sh.append_row(
                        "progress",
                        [str(datetime.date.today()), f"خودآزمایی: {test['title']}", pct,
                         f"{correct_count}/{total_items}"],
                    )
                    st.success("ثبت شد.")
            except Exception:
                pass
