"""پر کردن جای خالی روی متن درس: کلمه‌های ضعیفِ Ordbank از جمله‌ها برداشته می‌شن، جوابشون رو از بانک کلمه انتخاب کن."""
import datetime
import html
import json
import random
import re

import pandas as pd
import streamlit as st

import srs

_TOKEN = re.compile(r"[A-Za-zÅÄÖåäöÉéÜü]+")


_DEF_SUFFIXES = ("n", "en", "et", "na", "erna", "arna", "orna", "ena", "t")


def _forms(word_field):
    """شکل‌های صرفی Ordbank + شکل‌های معرفه‌ی ساده (kassa→kassan، utgift→utgiften، räkning→räkningen)."""
    base = set(srs.word_forms(word_field))
    out = set(base)
    for f in base:
        for suf in _DEF_SUFFIXES:
            out.add(f + suf)
        if f.endswith("a"):
            out.add(f[:-1] + "an")
    return out


def _meaning(card):
    m = str(card.get("معنی", "") or "")
    return re.sub(r"\s*\([^)]*\)\s*$", "", m).strip()


def _split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+|\n+", str(text or ""))
    return [p.strip() for p in parts if len(p.split()) >= 4]


def _candidates(sentences, cards, extra):
    """برای هر جمله حداکثر یک کلمه‌ی هدف. cards: لیست dict از Ordbank؛ extra: واژه‌های خودِ درس (بدون به‌روزرسانی سطح)."""
    pools = []
    for c in cards:
        pools.append((_forms(c.get("کلمه", "")), c, True))
    for v in extra:
        w = v.get("word", "")
        pools.append((_forms(w), {"کلمه": w, "معنی": v.get("translation_fa", "")}, False))
    used, out = set(), []
    for si, sent in enumerate(sentences):
        best = None
        for m in _TOKEN.finditer(sent):
            tok = m.group(0)
            if len(tok) < 3:
                continue
            low = tok.lower()
            for forms, card, real in pools:
                key = card.get("کلمه", "")
                if key in used or low not in forms:
                    continue
                cand = (m.start(), m.end(), tok, card, real)
                if best is None or (real and not best[4]):
                    best = cand
                break
            if best and best[4]:
                break
        if best:
            used.add(best[3].get("کلمه", ""))
            out.append({"sent": sent, "s": best[0], "e": best[1], "answer": best[2],
                        "hint": _meaning(best[3]), "word": best[3].get("کلمه", ""),
                        "level": best[3].get("سطح", 0), "real": best[4]})
    return out


def _lesson_cards(ob, vocab):
    """سطرهای Ordbank که معادل واژه‌های همین درس‌اند (هر سطحی)."""
    if ob is None or ob.empty or "کلمه" not in ob.columns:
        return []
    by_norm = {}
    for _, r in ob.iterrows():
        by_norm.setdefault(srs.normalize_word_answer(r.get("کلمه", "")), r.to_dict())
    out, seen = [], set()
    for v in vocab:
        key = srs.normalize_word_answer(v.get("word", ""))
        card = by_norm.get(key)
        if card and key not in seen:
            seen.add(key)
            out.append((card, v))
    return out


def _place_all(sentences, pairs):
    """هر کلمه را اول در جمله‌های متن، بعد در جمله‌ی مثالِ خودش جا می‌دهد. برمی‌گرداند (items, بی‌جا)."""
    items, used_sent, placed = [], set(), set()
    # 1) متن درس: یک جای خالی در هر جمله
    for si, sent in enumerate(sentences):
        for m in _TOKEN.finditer(sent):
            tok = m.group(0)
            if len(tok) < 3:
                continue
            hit = None
            for card, v in pairs:
                k = card.get("کلمه", "")
                if k not in placed and tok.lower() in _forms(k):
                    hit = (card, v)
                    break
            if hit:
                card = hit[0]
                placed.add(card.get("کلمه", ""))
                used_sent.add(sent)
                items.append({"sent": sent, "s": m.start(), "e": m.end(), "answer": tok,
                              "hint": _meaning(card), "word": card.get("کلمه", ""),
                              "level": card.get("سطح", 0), "real": True})
                break
    # 2) کلمه‌هایی که تو متن نبودند → جمله‌ی مثال خودشان
    for card, v in pairs:
        k = card.get("کلمه", "")
        if k in placed:
            continue
        ex = str(v.get("example_sentence_sv", "") or "").strip()
        if not ex or ex in used_sent:
            continue
        forms = _forms(k)
        for m in _TOKEN.finditer(ex):
            if len(m.group(0)) >= 3 and m.group(0).lower() in forms:
                placed.add(k)
                used_sent.add(ex)
                items.append({"sent": ex, "s": m.start(), "e": m.end(), "answer": m.group(0),
                              "hint": _meaning(card), "word": k,
                              "level": card.get("سطح", 0), "real": True})
                break
    missing = [c.get("کلمه", "") for c, _ in pairs if c.get("کلمه", "") not in placed]
    return items, missing


def render(sh, chosen, row, vocab):
    key = f"gap_{chosen}"
    with st.expander("🧩 پر کردن جای خالی (کلمه‌های ضعیف تو)", expanded=key in st.session_state):
        state = st.session_state.get(key)
        if state is None:
            scope = st.radio(
                "کدام کلمه‌ها؟",
                ["همه‌ی کلمه‌های این درس (که در بانک کلمات هستند)", "فقط کلمه‌های ضعیف من (از متن درس)"],
                key=f"gap_scope_{chosen}",
            )
            all_mode = scope.startswith("همه")
            n = 10
            if not all_mode:
                n = st.slider("چند جای خالی؟", 3, 10, 6, key=f"gap_n_{chosen}")
            hints = st.checkbox("معنی فارسی را زیر هر جمله نشان بده", value=True, key=f"gap_hint_{chosen}")
            if st.button("▶️ شروع", key=f"gap_start_{chosen}", type="primary"):
                try:
                    ob = sh.read_tab("ordbank")
                except Exception:
                    ob = pd.DataFrame()
                sents = _split_sentences(row.get("متن", ""))
                missing = []
                if all_mode:
                    pairs = _lesson_cards(ob, vocab)
                    if not pairs:
                        st.warning("هیچ‌کدام از کلمه‌های این درس هنوز در بانک کلمات نیست. اول از بخش واژه‌ها به بانک اضافه‌شان کن.")
                        return
                    items, missing = _place_all(sents, pairs)
                else:
                    cards = []
                    if not ob.empty and "کلمه" in ob.columns:
                        for _, r in ob.iterrows():
                            if srs._parse_level(r.get("سطح", 0)) <= 2:
                                cards.append(r.to_dict())
                    items = _candidates(sents, cards, vocab)[:n]
                if len(items) < (1 if all_mode else 3):
                    st.warning("در متن این درس کلمه‌ی مناسب پیدا نشد.")
                    return
                bank = [it["answer"] for it in items]
                random.shuffle(bank)
                st.session_state[key] = {"items": items, "bank": bank, "hints": hints,
                                         "result": None, "missing": missing}
                st.rerun()
            return

        items, bank = state["items"], state["bank"]
        if state.get("missing"):
            st.caption(f"{len(state['missing'])} کلمه جایی در متن یا جمله‌ی مثالش نداشت: " + "، ".join(state["missing"]))
        if state["result"] is None:
            st.markdown("**بانک کلمه‌ها:** " + " ".join(
                f"<span dir='ltr' style='display:inline-block;margin:2px 4px;padding:2px 10px;border-radius:12px;"
                f"background:#EEF5FB;border:1px solid #BBD6EA;color:#006AA7;font-weight:600'>{html.escape(w)}</span>"
                for w in bank), unsafe_allow_html=True)
            for i, it in enumerate(items):
                s = html.escape(it["sent"])
                a, b = it["s"], it["e"]
                shown = html.escape(it["sent"][:a]) + "<b style='color:#B7791F'>_____</b>" + html.escape(it["sent"][b:])
                st.markdown(f"<div dir='ltr' style='font-size:18px;line-height:1.7;margin-top:10px'>{i + 1}. {shown}</div>",
                            unsafe_allow_html=True)
                if state["hints"] and it["hint"]:
                    st.caption(f"معنی: {it['hint']}")
                st.selectbox("جواب:", bank, index=None, placeholder="انتخاب کن", key=f"gap_sel_{chosen}_{i}",
                             label_visibility="collapsed")
            if st.button("✅ بررسی", key=f"gap_check_{chosen}", type="primary"):
                picks = [st.session_state.get(f"gap_sel_{chosen}_{i}") for i in range(len(items))]
                if any(p is None for p in picks):
                    st.warning("همه‌ی جای‌خالی‌ها را پر کن.")
                else:
                    _finish(sh, chosen, state, picks)
                    st.rerun()
            return

        res = state["result"]
        ok = sum(1 for r in res if r["ok"])
        st.success(f"نتیجه: {ok} از {len(res)}")
        for i, r in enumerate(res):
            it = items[i]
            full = (html.escape(it["sent"][:it["s"]]) +
                    f"<b style='color:{'#1E8E3E' if r['ok'] else '#C0392B'}'>{html.escape(it['answer'])}</b>" +
                    html.escape(it["sent"][it["e"]:]))
            mark = "✅" if r["ok"] else f"❌ ({html.escape(str(r['pick']))})"
            st.markdown(f"<div dir='ltr' style='font-size:17px;line-height:1.7;margin:6px 0'>{mark} {full}</div>",
                        unsafe_allow_html=True)
        if st.button("🔁 دوباره", key=f"gap_again_{chosen}"):
            for i in range(len(items)):
                st.session_state.pop(f"gap_sel_{chosen}_{i}", None)
            del st.session_state[key]
            st.rerun()


def _finish(sh, chosen, state, picks):
    items = state["items"]
    today = str(datetime.date.today())
    res = [{"ok": p.lower() == it["answer"].lower(), "pick": p} for p, it in zip(picks, items)]
    state["result"] = res
    updates, wrong_rows = [], []
    for r, it in zip(res, items):
        if it["real"]:
            lvl, nxt = srs.compute_next_review(it["level"], r["ok"])
            updates.append((it["word"], {"سطح": lvl, "مرور_بعدی": nxt}))
        if not r["ok"]:
            wrong_rows.append([today, f"واژگان (جای خالی درس {chosen})", r["pick"], it["answer"], 1])
    try:
        if updates:
            sh.batch_update_by_match("ordbank", "کلمه", updates)
    except Exception as e:
        st.warning(f"به‌روزرسانی Ordbank شکست خورد: {e}")
    try:
        if wrong_rows:
            sh.append_rows("mina_fel", wrong_rows)
    except Exception:
        pass
    try:
        sh.increment_review_log(today, len(res), sum(1 for r in res if r["ok"]))
    except Exception:
        pass
