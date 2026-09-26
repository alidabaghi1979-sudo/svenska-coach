"""Push lessons into Svenska Coach's Google Sheet ("Ali Svenska Journal").

- tab `lessons`  : one row per lesson (the app's "📅 امروز" tab reads this)
- tab `ordbank`  : new vocabulary → immediately part of the app's SRS review

Headers MUST match SHEET_TABS in the app's sheets_helper.py.
"""
from __future__ import annotations

import json
import logging
from datetime import date

from generator import Lesson
from settings import Settings
from storage import lemma_of

log = logging.getLogger(__name__)

LESSONS_TAB = "lessons"
LESSONS_HEADER = ["تاریخ", "شماره", "عنوان", "موضوع", "دسته", "گرامر", "توضیح_گرامر",
                  "مثال‌ها", "واژه‌ها", "متن", "لینک_درایو", "شناسه_فایل", "مدت_دقیقه"]
ORDBANK_TAB = "ordbank"
ORDBANK_HEADER = ["تاریخ", "کلمه", "معنی", "جمله", "سطح", "مرور_بعدی"]


def _open(settings: Settings):
    import gspread

    client = gspread.service_account_from_dict(settings.service_account)
    return client.open_by_key(settings.sheet_id)


def _get_or_create(ss, name: str, header: list[str]):
    import gspread

    try:
        ws = ss.worksheet(name)
        current = ws.row_values(1)
        if not current:
            ws.update(range_name="A1", values=[header])
        elif current != header and header[: len(current)] == current:
            ws.update(range_name="A1", values=[header])  # only extend, never reorder
        return ws
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=name, rows=500, cols=len(header))
        ws.update(range_name="A1", values=[header])
        return ws


def lesson_row(lesson: Lesson, *, day: date, category: str, drive_link: str | None,
               file_id: str | None, duration: float) -> list:
    g = lesson.grammar_focus
    return [
        day.isoformat(),
        lesson.lesson_id,
        lesson.title_sv,
        lesson.topic,
        category,
        g.rule_name,
        g.explanation_fa,
        json.dumps([e.model_dump() for e in g.examples], ensure_ascii=False),
        json.dumps([v.model_dump() for v in lesson.vocabulary], ensure_ascii=False),
        lesson.audio_script[:45000],
        drive_link or "",
        file_id or "",
        round(duration / 60, 1) if duration else "",
    ]


def vocab_rows(lesson: Lesson, day: date, existing_words: set[str]) -> list[list]:
    """Rows for ordbank in the app's own format; skips words already in the bank."""
    rows, seen = [], set(existing_words)
    for v in lesson.vocabulary:
        key = lemma_of(v.word).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        sentence = f"{v.example_sentence_sv}\n{v.example_sentence_fa}\n(درس روزانه {lesson.lesson_id})"
        rows.append([day.isoformat(), v.word, f"{v.translation_fa} ({v.word_class})", sentence, 0, ""])
    return rows


def push_lesson(lesson: Lesson, settings: Settings, *, day: date, category: str,
                drive_link: str | None, file_id: str | None, duration: float) -> int:
    """Upsert the lesson row + add new vocab. Returns number of words added to ordbank."""
    ss = _open(settings)

    ws = _get_or_create(ss, LESSONS_TAB, LESSONS_HEADER)
    row = lesson_row(lesson, day=day, category=category, drive_link=drive_link,
                     file_id=file_id, duration=duration)
    ids = ws.col_values(2)[1:]
    if str(lesson.lesson_id) in ids:
        r = ids.index(str(lesson.lesson_id)) + 2
        ws.update(range_name=f"A{r}", values=[row], value_input_option="RAW")
        log.info("Updated lesson %d in Google Sheet", lesson.lesson_id)
    else:
        ws.append_row(row, value_input_option="RAW")
        log.info("Added lesson %d to Google Sheet", lesson.lesson_id)

    if not settings.add_vocab_to_ordbank:
        return 0
    ob = _get_or_create(ss, ORDBANK_TAB, ORDBANK_HEADER)
    existing = {lemma_of(w).lower() for w in ob.col_values(2)[1:] if w}
    new_rows = vocab_rows(lesson, day, existing)
    if new_rows:
        ob.append_rows(new_rows, value_input_option="RAW")
    log.info("Added %d new words to ordbank (%d already existed)",
             len(new_rows), len(lesson.vocabulary) - len(new_rows))
    return len(new_rows)


def update_audio(settings: Settings, lesson_id: int, drive_link: str | None, file_id: str | None,
                 duration: float) -> None:
    ss = _open(settings)
    ws = _get_or_create(ss, LESSONS_TAB, LESSONS_HEADER)
    ids = ws.col_values(2)[1:]
    if str(lesson_id) not in ids:
        return
    r = ids.index(str(lesson_id)) + 2
    ws.update(range_name=f"K{r}:M{r}",
              values=[[drive_link or "", file_id or "", round(duration / 60, 1) if duration else ""]],
              value_input_option="RAW")
