"""Svenska Daily Lesson — CLI.

  python main.py run-daily [--force] [--no-audio] [--date YYYY-MM-DD]
  python main.py run-topic "Topic" "Grammar focus" [--level B1] [--no-audio]
  python main.py export-anki --lesson-id 3 [--format apkg|tsv|both]
  python main.py synthesize --lesson-id 3        # (re)create audio for a saved lesson
  python main.py sync-sheets --lesson-id 3       # (re)send a lesson to the Svenska Coach app
  python main.py next                            # show which topic comes next
  python main.py list                            # recent lessons
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from curriculum import WEEKDAY_NAMES_SV, Curriculum, StateStore, Topic
from generator import Lesson, generate_lesson
from settings import Settings, get_settings, setup_logging
from storage import Storage, slugify
from tts import synthesize_to_mp3, write_id3_tags

log = logging.getLogger("main")


# ─────────────────────────── helpers ───────────────────────────
def today(settings: Settings) -> date:
    return datetime.now(ZoneInfo(settings.timezone)).date()


def study_sheet(lesson: Lesson, topic: Topic, day: date) -> str:
    """Markdown study sheet (readable on GitHub, phone, Drive)."""
    g = lesson.grammar_focus
    lines = [
        f"# {lesson.lesson_id:03d} · {lesson.title_sv}",
        f"_{day.isoformat()} · {topic.category} · {topic.topic}_",
        "",
        f"## Grammatik: {g.rule_name}",
        g.explanation_fa,
        "",
        *[f"- **{e.sv}** — {e.fa}" for e in g.examples],
        "",
        "## Ordlista",
        "| Ord | Ordklass | فارسی | Exempel |",
        "|---|---|---|---|",
        *[f"| {v.word} | {v.word_class} | {v.translation_fa} | {v.example_sentence_sv}<br>{v.example_sentence_fa} |"
          for v in lesson.vocabulary],
        "",
        "## Manus",
        "",
        *[ln if ln.strip() else "" for ln in lesson.audio_script.splitlines()],
        "",
    ]
    return "\n".join(lines)


def github_summary(text: str) -> None:
    path = os.getenv("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")


def make_audio(lesson: Lesson, topic: Topic, day: date, settings: Settings) -> tuple[Path, float]:
    mp3 = settings.audio_dir / f"{lesson.lesson_id:04d}_{slugify(lesson.title_sv)}.mp3"
    synthesize_to_mp3(lesson.audio_script, mp3, settings)
    duration = write_id3_tags(mp3, title=lesson.title_sv, lesson_id=lesson.lesson_id, topic=topic.topic,
                              grammar=lesson.grammar_focus.rule_name, category=topic.category,
                              lyrics=lesson.audio_script, day=day)
    log.info("Audio duration: %.1f min", duration / 60)
    return mp3, duration


def upload_to_drive(mp3: Path | None, state: StateStore, settings: Settings) -> tuple[str | None, str | None]:
    """Upload the MP3; returns (drive_link, file_id). Never fatal."""
    if not mp3 or not mp3.exists():
        return None, None
    if not settings.gdrive_enabled:
        log.info("Google Drive not configured — skipping upload")
        return None, None
    try:
        from drive_sync import DriveClient

        client = DriveClient(settings)
        folder = client.ensure_folder(state.data.get("gdrive_folder_id"))
        state.data["gdrive_folder_id"] = folder
        file_id, link = client.upload(mp3, folder)
        return link, file_id
    except Exception as exc:  # noqa: BLE001 — upload is optional
        log.error("Google Drive upload failed (lesson is still saved locally): %s", exc)
        return None, None


def push_to_sheets(lesson: Lesson, topic: Topic, day: date, settings: Settings, *,
                   drive_link: str | None, file_id: str | None, duration: float) -> bool:
    """Send the lesson to Svenska Coach's Google Sheet. Returns False on failure."""
    if not settings.sheets_enabled:
        log.warning("Google Sheets not configured (SVENSKA_SHEET_ID / GCP_SERVICE_ACCOUNT_JSON) — "
                    "lesson will NOT appear in the Svenska Coach app")
        return True
    try:
        import sheets_sync

        added = sheets_sync.push_lesson(lesson, settings, day=day, category=topic.category,
                                        drive_link=drive_link, file_id=file_id, duration=duration)
        github_summary(f"- Svenska Coach: lesson added, {added} new words in ordbank")
        return True
    except Exception as exc:  # noqa: BLE001
        log.error("Google Sheets sync failed: %s — retry with `python main.py sync-sheets --lesson-id %d`",
                  exc, lesson.lesson_id)
        return False


# ─────────────────────────── pipeline ───────────────────────────
def run_pipeline(topic: Topic, day: date, *, source: str, cursor_update: dict | None,
                 no_audio: bool, settings: Settings) -> int:
    curriculum_state = StateStore(settings.state_path)
    storage = Storage(settings.db_path, settings.lessons_dir)
    lesson_id = curriculum_state.next_lesson_id

    log.info("── Lesson %d | %s (%s) | %s | grammar: %s", lesson_id, day, WEEKDAY_NAMES_SV[day.weekday()],
             topic.topic, topic.grammar_focus)

    # 1) LLM
    lesson = generate_lesson(topic, lesson_id, settings)

    # 2) study sheet (always saved, even if audio fails)
    settings.lessons_dir.mkdir(parents=True, exist_ok=True)
    sheet = settings.lessons_dir / f"{lesson_id:04d}_{slugify(lesson.title_sv)}.md"
    sheet.write_text(study_sheet(lesson, topic, day), encoding="utf-8")

    # 3) TTS
    mp3: Path | None = None
    duration = 0.0
    audio_error: Exception | None = None
    if not no_audio:
        try:
            mp3, duration = make_audio(lesson, topic, day, settings)
        except Exception as exc:  # noqa: BLE001
            audio_error = exc
            log.error("Audio generation failed: %s — lesson text is saved; retry with "
                      "`python main.py synthesize --lesson-id %d`", exc, lesson_id)

    # 4) Drive upload (optional)
    drive_link, file_id = upload_to_drive(mp3, curriculum_state, settings)

    # 5) persist
    rel_audio = str(mp3.relative_to(settings.data_dir)) if mp3 else None
    storage.save_lesson(lesson, day=day, topic_id=topic.id, category=topic.category, level=topic.level,
                        audio_path=rel_audio, duration=duration, drive_link=drive_link,
                        provider=settings.llm_provider, model=settings.llm_model)
    curriculum_state.commit(lesson_id=lesson_id, topic=topic, day=day, cursor_update=cursor_update,
                            source=source, title=lesson.title_sv, audio_path=rel_audio, drive_link=drive_link)

    # 6) Svenska Coach app (Google Sheets)
    sheets_ok = push_to_sheets(lesson, topic, day, settings, drive_link=drive_link, file_id=file_id,
                               duration=duration)

    # 7) flashcards
    exports = storage.export_anki(lesson_id, settings.exports_dir)

    github_summary(
        f"### 🇸🇪 Lektion {lesson_id}: {lesson.title_sv}\n"
        f"- Ämne: {topic.topic}\n- Grammatik: {lesson.grammar_focus.rule_name}\n"
        f"- Ord: {len(lesson.vocabulary)} · Manus: {lesson.word_count} ord · Ljud: {duration / 60:.1f} min\n"
        + (f"- [Lyssna på Google Drive]({drive_link})\n" if drive_link else "")
    )
    log.info("✔ Done: lesson %d '%s' | audio=%s | anki=%s", lesson_id, lesson.title_sv,
             mp3.name if mp3 else "—", ", ".join(p.name for p in exports))
    return 2 if (audio_error or not sheets_ok) else 0


# ─────────────────────────── commands ───────────────────────────
def cmd_run_daily(args: argparse.Namespace, settings: Settings) -> int:
    day = date.fromisoformat(args.date) if args.date else today(settings)
    state = StateStore(settings.state_path)
    existing = state.lesson_for_date(day)
    if existing and not args.force:
        log.info("Lesson for %s already exists (#%s '%s'). Use --force to create another.",
                 day, existing["lesson_id"], existing["title"])
        return 0
    curriculum = Curriculum(settings.curriculum_path)
    topic, cursor_update = state.pick_topic(curriculum, day, settings.topic_mode)
    return run_pipeline(topic, day, source="daily", cursor_update=cursor_update,
                        no_audio=args.no_audio, settings=settings)


def cmd_run_topic(args: argparse.Namespace, settings: Settings) -> int:
    topic = Topic.manual(args.topic, args.grammar, args.level or settings.target_level)
    return run_pipeline(topic, today(settings), source="manual", cursor_update=None,
                        no_audio=args.no_audio, settings=settings)


def cmd_export_anki(args: argparse.Namespace, settings: Settings) -> int:
    storage = Storage(settings.db_path, settings.lessons_dir)
    for p in storage.export_anki(args.lesson_id, settings.exports_dir, fmt=args.format):
        print(p)
    return 0


def cmd_synthesize(args: argparse.Namespace, settings: Settings) -> int:
    storage = Storage(settings.db_path, settings.lessons_dir)
    data = storage.get_lesson(args.lesson_id)
    if not data:
        log.error("Lesson %d not found", args.lesson_id)
        return 1
    row = data["lesson"]
    lesson = Lesson.model_validate_json(row["raw_json"])
    topic = Topic(id=row["topic_id"] or 0, category=row["category"] or "", topic=row["topic"],
                  grammar_focus=row["grammar_rule"] or "", level=row["level"] or "")
    day = date.fromisoformat(row["lesson_date"])
    mp3, duration = make_audio(lesson, topic, day, settings)
    state = StateStore(settings.state_path)
    link, file_id = upload_to_drive(mp3, state, settings)
    link = link or row["drive_link"]
    state.save()
    with storage.connect() as con:
        con.execute("UPDATE lessons SET audio_path=?, audio_duration_sec=?, drive_link=? WHERE id=?",
                    (str(mp3.relative_to(settings.data_dir)), duration, link, args.lesson_id))
    if settings.sheets_enabled and link:
        import sheets_sync
        sheets_sync.update_audio(settings, args.lesson_id, link, file_id, duration)
    print(mp3)
    return 0


def cmd_sync_sheets(args: argparse.Namespace, settings: Settings) -> int:
    storage = Storage(settings.db_path, settings.lessons_dir)
    data = storage.get_lesson(args.lesson_id)
    if not data:
        log.error("Lesson %d not found", args.lesson_id)
        return 1
    row = data["lesson"]
    lesson = Lesson.model_validate_json(row["raw_json"])
    topic = Topic(id=row["topic_id"] or 0, category=row["category"] or "", topic=row["topic"],
                  grammar_focus=row["grammar_rule"] or "", level=row["level"] or "")
    link = row["drive_link"]
    file_id = link.split("id=")[-1] if link and "id=" in link else None
    ok = push_to_sheets(lesson, topic, date.fromisoformat(row["lesson_date"]), settings,
                        drive_link=link, file_id=file_id, duration=row["audio_duration_sec"] or 0)
    return 0 if ok else 1


def cmd_next(args: argparse.Namespace, settings: Settings) -> int:
    day = date.fromisoformat(args.date) if args.date else today(settings)
    state = StateStore(settings.state_path)
    topic, _ = state.pick_topic(Curriculum(settings.curriculum_path), day, settings.topic_mode)
    print(f"{day} ({WEEKDAY_NAMES_SV[day.weekday()]}) → lesson {state.next_lesson_id}: "
          f"[{topic.category}] {topic.topic} | {topic.grammar_focus} (round {topic.round})")
    return 0


def cmd_list(args: argparse.Namespace, settings: Settings) -> int:
    for r in Storage(settings.db_path, settings.lessons_dir).list_lessons(args.limit):
        mins = (r["audio_duration_sec"] or 0) / 60
        print(f"#{r['id']:>4}  {r['lesson_date']}  [{r['category']}]  {r['title_sv']}  "
              f"({r['grammar_rule']}, {mins:.1f} min)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="main.py", description="Svenska Daily Lesson pipeline")
    sub = p.add_subparsers(dest="command", required=True)

    d = sub.add_parser("run-daily", help="nightly pipeline: next topic → LLM → TTS → DB")
    d.add_argument("--force", action="store_true", help="create a lesson even if today's exists")
    d.add_argument("--no-audio", action="store_true", help="skip text-to-speech")
    d.add_argument("--date", help="pretend it is this date (YYYY-MM-DD)")
    d.set_defaults(func=cmd_run_daily)

    t = sub.add_parser("run-topic", help="generate a lesson for a specific topic")
    t.add_argument("topic")
    t.add_argument("grammar")
    t.add_argument("--level", help="e.g. A2, B1 (default TARGET_LEVEL)")
    t.add_argument("--no-audio", action="store_true")
    t.set_defaults(func=cmd_run_topic)

    a = sub.add_parser("export-anki", help="export flashcards of a lesson")
    a.add_argument("--lesson-id", type=int, required=True)
    a.add_argument("--format", choices=["apkg", "tsv", "both"], default="both")
    a.set_defaults(func=cmd_export_anki)

    s = sub.add_parser("synthesize", help="(re)create audio for a saved lesson")
    s.add_argument("--lesson-id", type=int, required=True)
    s.set_defaults(func=cmd_synthesize)

    ss = sub.add_parser("sync-sheets", help="(re)send a saved lesson to the Svenska Coach Google Sheet")
    ss.add_argument("--lesson-id", type=int, required=True)
    ss.set_defaults(func=cmd_sync_sheets)

    n = sub.add_parser("next", help="show the next topic without generating")
    n.add_argument("--date")
    n.set_defaults(func=cmd_next)

    ls = sub.add_parser("list", help="list recent lessons")
    ls.add_argument("--limit", type=int, default=20)
    ls.set_defaults(func=cmd_list)
    return p


def main(argv: list[str] | None = None) -> int:
    settings = get_settings()
    setup_logging(settings.log_level)
    args = build_parser().parse_args(argv)
    try:
        return args.func(args, settings)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:  # noqa: BLE001 — top-level: log and fail cleanly
        log.exception("Pipeline failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
