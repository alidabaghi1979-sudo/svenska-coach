"""Topic syllabus + state tracking (which topic comes next)."""
from __future__ import annotations

import copy
import json
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

WEEKDAY_NAMES_SV = ["måndag", "tisdag", "onsdag", "torsdag", "fredag", "lördag", "söndag"]


@dataclass(frozen=True)
class Topic:
    id: int
    category: str
    topic: str
    grammar_focus: str
    level: str
    round: int = 1  # >1 when the curriculum has wrapped around

    @classmethod
    def manual(cls, topic: str, grammar_focus: str, level: str) -> "Topic":
        return cls(id=0, category="manuell", topic=topic, grammar_focus=grammar_focus, level=level)


# ─────────────────────────── JSON helpers ───────────────────────────
def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Corrupt JSON file: {path} ({exc})") from exc


def write_json_atomic(path: Path, data: Any) -> None:
    """Write via temp file + rename, so a crash never leaves half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


# ─────────────────────────── Curriculum ───────────────────────────
class Curriculum:
    def __init__(self, path: Path):
        doc = read_json(path, None)
        if not doc or not doc.get("topics"):
            raise RuntimeError(f"curriculum.json missing or empty: {path}")
        self.topics: list[dict] = doc["topics"]
        self.weekday_categories: dict[str, str] = doc.get("weekday_categories", {})

    def by_category(self, category: str) -> list[dict]:
        return [t for t in self.topics if t["category"] == category]

    def category_for(self, day: date) -> str:
        return self.weekday_categories.get(str(day.weekday()), "vardag")


# ─────────────────────────── State ───────────────────────────
DEFAULT_STATE: dict[str, Any] = {
    "last_lesson_id": 0,
    "sequential_cursor": 0,
    "category_cursor": {},
    "history": [],
    "gdrive_folder_id": None,
}


class StateStore:
    def __init__(self, path: Path):
        self.path = path
        self.data: dict[str, Any] = {**copy.deepcopy(DEFAULT_STATE), **read_json(path, {})}
        self.data.setdefault("category_cursor", {})

    def save(self) -> None:
        write_json_atomic(self.path, self.data)

    @property
    def next_lesson_id(self) -> int:
        return int(self.data.get("last_lesson_id", 0)) + 1

    def lesson_for_date(self, day: date) -> dict | None:
        for h in reversed(self.data.get("history", [])):
            if h.get("date") == day.isoformat() and h.get("source") == "daily":
                return h
        return None

    # -- selection (pure: does NOT mutate state) --
    def pick_topic(self, curriculum: Curriculum, day: date, mode: str) -> tuple[Topic, dict]:
        """Return (topic, cursor_update). Apply cursor_update via commit() only after success."""
        if mode == "sequential":
            pool = curriculum.topics
            cursor = int(self.data.get("sequential_cursor", 0))
            key = None
        else:
            category = curriculum.category_for(day)
            pool = curriculum.by_category(category) or curriculum.topics
            cursor = int(self.data["category_cursor"].get(category, 0))
            key = category

        idx = cursor % len(pool)
        rnd = cursor // len(pool) + 1
        t = pool[idx]
        topic = Topic(id=t["id"], category=t["category"], topic=t["topic"],
                      grammar_focus=t["grammar_focus"], level=t.get("level", "A2"), round=rnd)
        return topic, {"key": key, "cursor": cursor + 1}

    def commit(self, *, lesson_id: int, topic: Topic, day: date, cursor_update: dict | None,
               source: str, title: str, audio_path: str | None, drive_link: str | None) -> None:
        self.data["last_lesson_id"] = max(int(self.data.get("last_lesson_id", 0)), lesson_id)
        if cursor_update:
            if cursor_update["key"] is None:
                self.data["sequential_cursor"] = cursor_update["cursor"]
            else:
                self.data["category_cursor"][cursor_update["key"]] = cursor_update["cursor"]
        self.data["history"].append({
            "lesson_id": lesson_id,
            "date": day.isoformat(),
            "source": source,
            "topic_id": topic.id,
            "topic": topic.topic,
            "title": title,
            "audio": audio_path,
            "drive_link": drive_link,
        })
        self.data["history"] = self.data["history"][-400:]
        self.save()
        log.info("State updated: last_lesson_id=%s", self.data["last_lesson_id"])
