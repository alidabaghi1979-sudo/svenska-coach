"""SQLite + JSON persistence and Anki export (TSV / .apkg)."""
from __future__ import annotations

import csv
import html
import json
import logging
import re
import sqlite3
import unicodedata
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterator

from generator import Lesson, VocabItem

log = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS lessons (
    id                  INTEGER PRIMARY KEY,
    lesson_date         TEXT NOT NULL,
    title_sv            TEXT NOT NULL,
    topic               TEXT NOT NULL,
    topic_id            INTEGER,
    category            TEXT,
    level               TEXT,
    grammar_rule        TEXT,
    audio_script        TEXT NOT NULL,
    word_count          INTEGER,
    audio_path          TEXT,
    audio_duration_sec  REAL,
    drive_link          TEXT,
    llm_provider        TEXT,
    llm_model           TEXT,
    raw_json            TEXT NOT NULL,
    created_at          TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS vocabulary (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id            INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    word                 TEXT NOT NULL,
    lemma                TEXT NOT NULL,
    word_class           TEXT NOT NULL,
    translation_fa       TEXT NOT NULL,
    example_sentence_sv  TEXT NOT NULL,
    example_sentence_fa  TEXT NOT NULL,
    cloze_sv             TEXT,
    UNIQUE (lesson_id, word)
);
CREATE TABLE IF NOT EXISTS grammar_notes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id       INTEGER NOT NULL UNIQUE REFERENCES lessons(id) ON DELETE CASCADE,
    rule_name       TEXT NOT NULL,
    explanation_fa  TEXT NOT NULL,
    examples_json   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_vocab_lemma ON vocabulary(lemma);
"""

# stable IDs so re-imports into Anki update instead of duplicating
ANKI_DECK_ID = 2059412031
ANKI_BASIC_MODEL_ID = 1607392319
ANKI_CLOZE_MODEL_ID = 1607392320


# ─────────────────────────── helpers ───────────────────────────
def slugify(text: str, max_len: int = 40) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:max_len].rstrip("-") or "lesson"


def lemma_of(word: str) -> str:
    """'en remiss (remisser)' → 'remiss', 'att boka' → 'boka'."""
    base = word.split("(")[0].strip()
    base = re.sub(r"^(en|ett|att)\s+", "", base, flags=re.IGNORECASE)
    return base.strip(" ,;")


def word_forms(word: str) -> list[str]:
    forms = [lemma_of(word)]
    m = re.search(r"\(([^)]*)\)", word)
    if m:
        forms += [f.strip() for f in re.split(r"[,/;]", m.group(1)) if f.strip()]
    return [f for f in forms if f]


def make_cloze(item: VocabItem) -> str | None:
    """Wrap the target word in the example sentence with {{c1::...}}."""
    sentence = item.example_sentence_sv
    candidates = sorted(set(word_forms(item.word)), key=len, reverse=True)
    # 1) exact form (with possible inflection suffix)
    for form in candidates:
        m = re.search(rf"(?<![\wåäöÅÄÖ]){re.escape(form)}[\wåäöÅÄÖ]*", sentence, flags=re.IGNORECASE)
        if m:
            return sentence[:m.start()] + "{{c1::" + m.group(0) + "::" + item.translation_fa + "}}" + sentence[m.end():]
    # 2) stem match (e.g. 'gå' → 'gick' won't match, but 'ringa' → 'ringde' will)
    lemma = candidates[-1] if candidates else ""
    if " " not in lemma and len(lemma) >= 4:
        stem = lemma[: max(3, len(lemma) - 2)]
        m = re.search(rf"(?<![\wåäöÅÄÖ]){re.escape(stem)}[\wåäöÅÄÖ]*", sentence, flags=re.IGNORECASE)
        if m:
            return sentence[:m.start()] + "{{c1::" + m.group(0) + "::" + item.translation_fa + "}}" + sentence[m.end():]
    return None


def rtl(text: str) -> str:
    return f'<div dir="rtl" style="text-align:right">{html.escape(text)}</div>'


# ─────────────────────────── Storage ───────────────────────────
class Storage:
    def __init__(self, db_path: Path, lessons_dir: Path):
        self.db_path = db_path
        self.lessons_dir = lessons_dir
        db_path.parent.mkdir(parents=True, exist_ok=True)
        lessons_dir.mkdir(parents=True, exist_ok=True)
        with self.connect() as con:
            con.executescript(SCHEMA)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def save_lesson(self, lesson: Lesson, *, day: date, topic_id: int, category: str, level: str,
                    audio_path: str | None, duration: float, drive_link: str | None,
                    provider: str, model: str) -> Path:
        raw = lesson.model_dump()
        with self.connect() as con:
            con.execute("DELETE FROM lessons WHERE id = ?", (lesson.lesson_id,))  # idempotent re-run
            con.execute(
                """INSERT INTO lessons (id, lesson_date, title_sv, topic, topic_id, category, level,
                   grammar_rule, audio_script, word_count, audio_path, audio_duration_sec, drive_link,
                   llm_provider, llm_model, raw_json, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (lesson.lesson_id, day.isoformat(), lesson.title_sv, lesson.topic, topic_id, category, level,
                 lesson.grammar_focus.rule_name, lesson.audio_script, lesson.word_count, audio_path,
                 duration, drive_link, provider, model, json.dumps(raw, ensure_ascii=False),
                 datetime.now(timezone.utc).isoformat(timespec="seconds")),
            )
            for v in lesson.vocabulary:
                con.execute(
                    """INSERT OR IGNORE INTO vocabulary (lesson_id, word, lemma, word_class, translation_fa,
                       example_sentence_sv, example_sentence_fa, cloze_sv) VALUES (?,?,?,?,?,?,?,?)""",
                    (lesson.lesson_id, v.word, lemma_of(v.word).lower(), v.word_class, v.translation_fa,
                     v.example_sentence_sv, v.example_sentence_fa, make_cloze(v)),
                )
            g = lesson.grammar_focus
            con.execute(
                "INSERT INTO grammar_notes (lesson_id, rule_name, explanation_fa, examples_json) VALUES (?,?,?,?)",
                (lesson.lesson_id, g.rule_name, g.explanation_fa,
                 json.dumps([e.model_dump() for e in g.examples], ensure_ascii=False)),
            )

        # human-readable JSON + script copy (easy to read on GitHub / phone)
        json_path = self.lessons_dir / f"{lesson.lesson_id:04d}_{slugify(lesson.title_sv)}.json"
        doc = {**raw, "date": day.isoformat(), "category": category, "level": level,
               "audio_path": audio_path, "drive_link": drive_link, "duration_sec": round(duration, 1)}
        json_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("Saved lesson %d to DB and %s", lesson.lesson_id, json_path.name)
        return json_path

    def get_lesson(self, lesson_id: int) -> dict | None:
        with self.connect() as con:
            row = con.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
            if not row:
                return None
            vocab = [dict(r) for r in con.execute(
                "SELECT * FROM vocabulary WHERE lesson_id = ? ORDER BY id", (lesson_id,))]
            gram = con.execute("SELECT * FROM grammar_notes WHERE lesson_id = ?", (lesson_id,)).fetchone()
        return {"lesson": dict(row), "vocabulary": vocab, "grammar": dict(gram) if gram else None}

    def list_lessons(self, limit: int = 20) -> list[dict]:
        with self.connect() as con:
            rows = con.execute(
                "SELECT id, lesson_date, title_sv, category, grammar_rule, audio_duration_sec "
                "FROM lessons ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    # ─────────────────────── Anki export ───────────────────────
    def export_anki(self, lesson_id: int, out_dir: Path, fmt: str = "both") -> list[Path]:
        data = self.get_lesson(lesson_id)
        if not data:
            raise ValueError(f"Lesson {lesson_id} not found in database")
        out_dir.mkdir(parents=True, exist_ok=True)
        lesson, vocab, gram = data["lesson"], data["vocabulary"], data["grammar"]
        base = out_dir / f"lesson_{lesson_id:04d}_{slugify(lesson['title_sv'])}"
        tag = f"svenska_daily lesson_{lesson_id:04d} {lesson.get('category') or ''}".strip()
        paths: list[Path] = []

        basic_rows, cloze_rows = [], []
        for v in vocab:
            front = f"<b>{html.escape(v['word'])}</b><br><i>{v['word_class']}</i>"
            back = (f"{rtl(v['translation_fa'])}<hr>{html.escape(v['example_sentence_sv'])}"
                    f"{rtl(v['example_sentence_fa'])}")
            basic_rows.append((front, back, tag))
            if v["cloze_sv"]:
                extra = f"{html.escape(v['word'])}{rtl(v['example_sentence_fa'])}"
                cloze_rows.append((html.escape(v["cloze_sv"]), extra, tag))
        if gram:
            for ex in json.loads(gram["examples_json"]):
                front = f"<b>Grammatik: {html.escape(gram['rule_name'])}</b><br>{html.escape(ex['sv'])}"
                back = rtl(ex["fa"]) + "<hr>" + rtl(gram["explanation_fa"])
                basic_rows.append((front, back, tag + " grammatik"))

        if fmt in ("tsv", "both"):
            for suffix, rows in (("_basic.tsv", basic_rows), ("_cloze.tsv", cloze_rows)):
                p = base.with_name(base.name + suffix)
                with p.open("w", encoding="utf-8", newline="") as fh:
                    fh.write("#separator:tab\n#html:true\n#tags column:3\n")
                    csv.writer(fh, delimiter="\t", quoting=csv.QUOTE_MINIMAL).writerows(rows)
                paths.append(p)

        if fmt in ("apkg", "both"):
            paths.append(self._write_apkg(base.with_suffix(".apkg"), basic_rows, cloze_rows))
        log.info("Exported %d basic + %d cloze cards for lesson %d", len(basic_rows), len(cloze_rows), lesson_id)
        return paths

    @staticmethod
    def _write_apkg(path: Path, basic_rows: list[tuple], cloze_rows: list[tuple]) -> Path:
        import genanki

        css = ".card{font-family:Arial,sans-serif;font-size:22px;text-align:center;color:#222;background:#fff}"
        basic = genanki.Model(
            ANKI_BASIC_MODEL_ID, "Svenska Daily – Basic",
            fields=[{"name": "Front"}, {"name": "Back"}],
            templates=[{"name": "Card 1", "qfmt": "{{Front}}",
                        "afmt": "{{FrontSide}}<hr id=answer>{{Back}}"}],
            css=css,
        )
        cloze = genanki.Model(
            ANKI_CLOZE_MODEL_ID, "Svenska Daily – Cloze",
            fields=[{"name": "Text"}, {"name": "Extra"}],
            templates=[{"name": "Cloze", "qfmt": "{{cloze:Text}}", "afmt": "{{cloze:Text}}<br>{{Extra}}"}],
            css=css + ".cloze{font-weight:bold;color:#0a58ca}",
            model_type=genanki.Model.CLOZE,
        )
        deck = genanki.Deck(ANKI_DECK_ID, "Svenska::Daily Lessons")
        for front, back, tags in basic_rows:
            deck.add_note(genanki.Note(model=basic, fields=[front, back], tags=tags.split(),
                                       guid=genanki.guid_for(front)))
        for text, extra, tags in cloze_rows:
            deck.add_note(genanki.Note(model=cloze, fields=[text, extra], tags=tags.split(),
                                       guid=genanki.guid_for(text)))
        genanki.Package(deck).write_to_file(str(path))
        return path
