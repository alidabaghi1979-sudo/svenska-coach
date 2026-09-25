"""
دانلود صوت جدیدترین ویدیوهای یک کانال یوتیوب با yt-dlp.
پیش‌نیاز: pip install yt-dlp   و نصب ffmpeg روی سیستم (برای تبدیل به mp3)
فقط برای استفاده‌ی شخصی و غیرتجاری خودت استفاده کن.
"""
from pathlib import Path

import yt_dlp


def fetch_new_youtube_audio(source_name, channel_url, download_dir, state, max_new=1):
    """
    جدیدترین ویدیوهای کانال رو چک می‌کنه، اونایی که قبلاً دانلود نشدن رو
    به mp3 تبدیل و ذخیره می‌کنه.
    خروجی: لیست مسیر فایل‌های mp3 جدید
    """
    downloaded_ids = state["youtube"].setdefault(source_name, [])
    out_dir = Path(download_dir) / "youtube" / source_name
    out_dir.mkdir(parents=True, exist_ok=True)

    # اول فقط لیست ویدیوها رو می‌گیریم (بدون دانلود) تا تازه‌ها رو پیدا کنیم
    list_opts = {
        "quiet": True,
        "extract_flat": True,
        "playlistend": max_new + len(downloaded_ids) + 5,
    }
    try:
        with yt_dlp.YoutubeDL(list_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
    except Exception as e:
        print(f"✗ خطا در خواندن کانال '{source_name}': {e}")
        return []

    entries = info.get("entries", []) if info else []
    new_files = []
    count = 0

    for entry in entries:
        if count >= max_new:
            break

        video_id = entry.get("id")
        if not video_id or video_id in downloaded_ids:
            continue

        video_url = f"https://www.youtube.com/watch?v={video_id}"
        out_template = str(out_dir / "%(title)s.%(ext)s")

        dl_opts = {
            "format": "bestaudio/best",
            "outtmpl": out_template,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }],
            "quiet": False,
        }

        print(f"در حال دانلود از یوتیوب: {entry.get('title')}")
        try:
            with yt_dlp.YoutubeDL(dl_opts) as ydl_dl:
                result = ydl_dl.extract_info(video_url, download=True)
        except Exception as e:
            print(f"✗ خطا در دانلود ویدیوی '{entry.get('title')}': {e}")
            continue

        downloaded_ids.append(video_id)

        # پیدا کردن مسیر دقیق فایل mp3 ساخته‌شده
        expected_title = result.get("title", "") if result else entry.get("title", "")
        safe_prefix = expected_title[:30]
        match = None
        for f in out_dir.glob("*.mp3"):
            if safe_prefix and safe_prefix in f.stem:
                match = f
                break
        if match is None:
            # اگر مچ دقیق پیدا نشد، آخرین فایل ساخته‌شده رو بردار
            mp3_files = sorted(out_dir.glob("*.mp3"), key=lambda p: p.stat().st_mtime)
            match = mp3_files[-1] if mp3_files else None

        if match:
            new_files.append(str(match))
        count += 1

    return new_files
