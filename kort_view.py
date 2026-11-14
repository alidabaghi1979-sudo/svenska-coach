"""تب Kort: فلش‌کارت‌های دسته‌بندی‌شده (مثل Anki) — کلمه/جمله‌ی بیرون از درس‌ها، با ساخت جمله‌ی مثال توسط Gemini."""
import csv
import datetime
import io
import json
import re

import pandas as pd
import streamlit as st

import coach
import srs

MAX_ITEMS = 45
CHUNK = 15
NEW_DECK = "➕ دسته‌ی جدید"


# ---------------- Gemini: ساخت کارت‌ها ----------------
def _extract_json_list(text):
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        v = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\[.*\]", text, re.S)
        if not m:
            raise
        v = json.loads(m.group(0))
    return v if isinstance(v, list) else []


def generate_cards(items):
    """items: لیست {word, hint}. خروجی: لیست dict هم‌ترتیب با ورودی (یا کوتاه‌تر اگه مدل کم برگردونه)."""
    from google.genai import types
    out = []
    for i in range(0, len(items), CHUNK):
        part = items[i:i + CHUNK]
        listing = "\n".join(
            f"{n + 1}. {it['word']}"
            + (f"   (معنی مورد نظر کاربر: {it['hint']})" if it.get("hint") else "")
            + (f"   (جمله‌ی مثال کاربر، همان را استفاده کن: {it['sent']})" if it.get("sent") else "")
            for n, it in enumerate(part)
        )
        prompt = (
            "برای ساخت فلش‌کارت زبان‌آموزِ فارسی‌زبانِ سوئدی، برای هر مورد زیر یک شیء JSON بساز. "
            "هر مورد ممکن است یک کلمه، یک عبارت یا یک جمله‌ی کامل سوئدی باشد.\n\n"
            f"{listing}\n\n"
            "خروجی: فقط یک آرایه‌ی JSON خام (بدون ``` و بدون توضیح)، دقیقاً به همان تعداد و ترتیب، "
            "هر شیء با این کلیدها:\n"
            '{"word": "شکل استاندارد: اسم با en/ett و جمع داخل پرانتز مثل \'en bil (bilar)\'، فعل مثل '
            '\'boka (bokar, bokade, bokat)\'، صفت مثل \'snabb (snabbt, snabba)\'، وگرنه خودِ کلمه/عبارت؛ '
            'اگر ورودی جمله‌ی کامل بود همان جمله", '
            '"translation_fa": "معنی فارسی کوتاه و طبیعی (اگر کاربر معنی داده همان را بگذار)", '
            '"word_class": "یکی از: substantiv, verb, adjektiv, adverb, fras", '
            '"example_sentence_sv": "یک جمله‌ی ساده و کوتاه (سطح A2 تا B1) که دقیقاً همین کلمه در آن باشد؛ '
            'اگر ورودی جمله بود همان جمله", '
            '"example_sentence_fa": "ترجمه‌ی فارسیِ طبیعیِ همان جمله"}\n'
            "اگر ورودی فارسی بود، معادل سوئدی را پیدا کن و برای آن کارت بساز."
        )
        resp = coach.gemini_generate(
            coach.TRANSCRIBE_MODEL, [prompt],
            types.GenerateContentConfig(response_mime_type="application/json", max_output_tokens=8000),
        )
        out += _extract_json_list(resp.text)
    return out


# ---------------- ورودی‌ها ----------------
def _parse_lines(text):
    """هر خط یک مورد؛ یا بلوک‌های کارت‌مانند:
        stolt
        معنی: مغرور
        جمله: Som läkare ...
        (ترجمه‌ی فارسی جمله)
    خطِ «معنی:» و «جمله:» و خطِ پرانتزی به مورد قبلی می‌چسبند."""
    items, cur = [], None
    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^(معنی|جمله)\s*[:：]\s*(.*)$", line)
        if m and cur is not None:
            if m.group(1) == "معنی":
                cur["hint"] = re.sub(r"\s*\([^)]*\)\s*$", "", m.group(2)).strip() or m.group(2).strip()
            else:
                cur["sent"] = m.group(2).strip()
            continue
        if cur is not None and cur.get("sent") and not cur.get("sent_fa") \
                and line.startswith("(") and line.endswith(")"):
            cur["sent_fa"] = line[1:-1].strip()
            continue
        hint = ""
        for sep in ("=", "\t", ";"):
            if sep in line:
                a, b = line.split(sep, 1)
                line, hint = a.strip(), b.strip()
                break
        if line:
            cur = {"word": line, "hint": hint, "sent": "", "sent_fa": ""}
            items.append(cur)
    return items


def _parse_upload(upl):
    data = upl.getvalue().decode("utf-8-sig", errors="replace")
    if upl.name.lower().endswith(".csv"):
        items = []
        for row in csv.reader(io.StringIO(data), delimiter=";" if data.count(";") > data.count(",") else ","):
            if row and row[0].strip():
                items.append({"word": row[0].strip(), "hint": row[1].strip() if len(row) > 1 else "", "sent": "", "sent_fa": ""})
        return items
    return _parse_lines(data)


def _deck_picker(decks, key):
    opts = decks + [NEW_DECK] if decks else [NEW_DECK]
    sel = st.selectbox("🗂 دسته:", opts, key=f"{key}_sel")
    if sel == NEW_DECK:
        name = st.text_input("نام دسته‌ی جدید (مثلاً «کتاب X»):", key=f"{key}_new").strip()
        return name or srs.DEFAULT_DECK
    return sel


def _ordbank_row(deck, word, tr, wc, sv, fa, note="(کارت دستی)"):
    wc = "fras" if wc in ("mening", "") else wc
    sentence = "\n".join(x for x in [sv, fa, note] if x)
    practice = json.dumps([sv], ensure_ascii=False) if sv else ""
    return [str(datetime.date.today()), word, f"{tr} ({wc})".strip(), sentence, 0, "", practice, deck]


# ---------------- صفحه ----------------
def _go_review(deck):
    st.session_state["srs_deck"] = deck
    st.session_state["srs_queue"] = None
    st.session_state["main_nav"] = "vocab"


def render(sh):
    st.subheader("🃏 کارت‌ها (Kort)")
    st.caption("کلمه و جمله‌ی بیرون از درس‌ها (مثلاً از کتابی که می‌خوانی) را اضافه کن؛ مرورشان همان سیستم Ordbank است.")
    try:
        ob = sh.read_tab("ordbank")
    except Exception as e:
        st.error(f"خواندن بانک کلمات شکست خورد: {e}")
        return
    recs = ob.to_dict("records") if not ob.empty else []
    decks = sorted({srs.deck_of(r) for r in recs})
    existing = {srs.normalize_word_answer(r.get("کلمه", "")) for r in recs}
    today = datetime.date.today()

    # ---- خلاصه‌ی دسته‌ها ----
    if recs:
        st.markdown("**دسته‌های من**")
        for d in decks:
            cards = [r for r in recs if srs.deck_of(r) == d]
            due = sum(1 for r in cards if srs._is_due(r.get("مرور_بعدی"), today))
            c1, c2 = st.columns([3, 2])
            c1.markdown(f"**{d}** — {len(cards)} کارت · موعددار: {due}")
            c2.button("▶️ مرور", key=f"kort_rev_{d}", on_click=_go_review, args=(d,), use_container_width=True)
        st.divider()

    st.markdown("### ➕ افزودن کارت")
    t1, t2 = st.tabs(["📝 لیست کلمه / جمله (با Gemini)", "✍️ دستی"])

    # ---- لیست + فایل → Gemini ----
    with t1:
        st.caption("هر خط یک کلمه یا جمله. اگر معنی دلخواه داری: «کلمه = معنی». Gemini معنی، صرف، en/ett و جمله‌ی مثال با ترجمه می‌سازد.")
        text = st.text_area("کلمه‌ها:", height=160, key="kort_text", placeholder="kvitto\nspendera = خرج کردن\nHur mycket kostar det?")
        upl = st.file_uploader("یا فایل (.txt / .csv — ستون اول کلمه، ستون دوم معنی اختیاری):", type=["txt", "csv"], key="kort_file")
        deck = _deck_picker(decks, "kort_gen_deck")
        if st.button("✨ بساز", key="kort_gen", type="primary"):
            items = _parse_lines(text)
            if upl is not None:
                try:
                    items += _parse_upload(upl)
                except Exception as e:
                    st.error(f"خواندن فایل شکست خورد: {e}")
            seen, uniq = set(), []
            for it in items:
                k = it["word"].lower()
                if k not in seen:
                    seen.add(k)
                    uniq.append(it)
            if not uniq:
                st.warning("چیزی وارد نکردی.")
            else:
                if len(uniq) > MAX_ITEMS:
                    st.warning(f"فقط {MAX_ITEMS} مورد اول پردازش می‌شود.")
                    uniq = uniq[:MAX_ITEMS]
                try:
                    with st.spinner(f"Gemini دارد {len(uniq)} کارت می‌سازد..."):
                        gen = generate_cards(uniq)
                    rows = []
                    for it, g in zip(uniq, gen):
                        w = str(g.get("word") or it["word"])
                        rows.append({
                            "افزودن": srs.normalize_word_answer(w) not in existing,
                            "کلمه": w,
                            "معنی": it["hint"] or str(g.get("translation_fa", "")),
                            "نوع": str(g.get("word_class", "fras")),
                            "جمله_سوئدی": it.get("sent") or str(g.get("example_sentence_sv", "")),
                            "جمله_فارسی": it.get("sent_fa") or str(g.get("example_sentence_fa", "")),
                            "تکراری": srs.normalize_word_answer(w) in existing,
                        })
                    if len(gen) < len(uniq):
                        st.warning(f"Gemini فقط {len(gen)} از {len(uniq)} مورد را برگرداند؛ بقیه را دوباره امتحان کن.")
                    st.session_state["kort_preview"] = rows
                    st.session_state["kort_preview_deck"] = deck
                except Exception as e:
                    st.error(f"{e}")

        prev = st.session_state.get("kort_preview")
        if prev:
            st.markdown("**پیش‌نمایش** — ویرایش کن، ناخواسته‌ها را تیک نزن، بعد ذخیره کن:")
            edited = st.data_editor(
                pd.DataFrame(prev), hide_index=True, use_container_width=True, key="kort_editor",
                column_config={"افزودن": st.column_config.CheckboxColumn(), "تکراری": st.column_config.CheckboxColumn(disabled=True)},
            )
            st.caption("«تکراری» یعنی از قبل در بانک کلمات هست (پیش‌فرض تیک نخورده).")
            if st.button("💾 ذخیره‌ی کارت‌های تیک‌خورده", key="kort_save"):
                deck_name = st.session_state.get("kort_preview_deck", srs.DEFAULT_DECK)
                rows = [
                    _ordbank_row(deck_name, str(r["کلمه"]).strip(), str(r["معنی"]).strip(), str(r["نوع"]).strip(),
                                 str(r["جمله_سوئدی"]).strip(), str(r["جمله_فارسی"]).strip(), "(کارت دستی)")
                    for r in edited.to_dict("records") if r["افزودن"] and str(r["کلمه"]).strip()
                ]
                if not rows:
                    st.warning("هیچ کارتی تیک نخورده.")
                else:
                    try:
                        sh.append_rows("ordbank", rows)
                        st.session_state.pop("kort_preview", None)
                        st.success(f"✅ {len(rows)} کارت به دسته‌ی «{deck_name}» اضافه شد.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"ذخیره شکست خورد: {e}")

    # ---- دستی ----
    with t2:
        deck_m = _deck_picker(decks, "kort_man_deck")
        with st.form("kort_manual", clear_on_submit=True):
            w = st.text_input("کلمه یا جمله‌ی سوئدی:")
            tr = st.text_input("معنی فارسی:")
            sv = st.text_input("جمله‌ی مثال (سوئدی) — اختیاری:")
            fa = st.text_input("ترجمه‌ی جمله‌ی مثال — اختیاری:")
            ok = st.form_submit_button("➕ افزودن")
        if ok:
            if not w.strip() or not tr.strip():
                st.warning("کلمه و معنی لازم است.")
            elif srs.normalize_word_answer(w) in existing:
                st.info("این کلمه از قبل در بانک هست.")
            else:
                try:
                    sh.append_row("ordbank", _ordbank_row(deck_m, w.strip(), tr.strip(), "fras", sv.strip(), fa.strip()))
                    st.success(f"✅ «{w.strip()}» اضافه شد.")
                except Exception as e:
                    st.error(f"ذخیره شکست خورد: {e}")
