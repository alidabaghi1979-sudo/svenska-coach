"""
دانلود اپیزودهای جدید از فیدهای RSS پادکست سوئدی.
پیش‌نیاز: pip install feedparser requests
"""
import os
import json
from pathlib import Path

import feedparser
import requests


def load_state(state_file):
    """وضعیت قبلی (چه چیزهایی قبلاً دانلود شده) رو می‌خونه."""
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"podcast": {}, "youtube": {}}


def save_state(state_file, state):
    """وضعیت جدید رو ذخیره می‌کنه تا دفعه‌ی بعد چیزی دوباره دانلود نشه."""
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def fetch_new_podcast_episodes(feed_name, feed_url, download_dir, state, max_new=1):
    """
    فید RSS رو می‌خونه، اپیزودهای دانلود‌نشده رو پیدا و دانلود می‌کنه.
    خروجی: لیست مسیر فایل‌های mp3 جدید
    """
    parsed = feedparser.parse(feed_url)
    if parsed.bozo:
        print(f"⚠ هشدار: خواندن فید '{feed_name}' با مشکل مواجه شد: {parsed.bozo_exception}")

    downloaded_ids = state["podcast"].setdefault(feed_name, [])
    new_files = []

    out_dir = Path(download_dir) / "podcasts" / feed_name
    out_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for entry in parsed.entries:
        if count >= max_new:
            break

        episode_id = entry.get("id") or entry.get("link")
        if not episode_id or episode_id in downloaded_ids:
            continue

        audio_url = None
        for link in entry.get("links", []):
            if link.get("type", "").startswith("audio"):
                audio_url = link.get("href")
                break
        if not audio_url:
            continue

        safe_title = "".join(c for c in entry.title if c.isalnum() or c in " _-").strip()[:80]
        file_path = out_dir / f"{safe_title}.mp3"

        print(f"در حال دانلود پادکست: {entry.title}")
        try:
            resp = requests.get(audio_url, stream=True, timeout=60)
            resp.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
        except requests.RequestException as e:
            print(f"✗ خطا در دانلود '{entry.title}': {e}")
            continue

        downloaded_ids.append(episode_id)
        new_files.append(str(file_path))
        count += 1

    return new_files
