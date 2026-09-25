"""
اجرای روزانه: دانلود صوت جدید از پادکست‌ها و یوتیوب + ساخت رونوشت خودکار.
اجرا: python main.py
"""
from pathlib import Path

import config
from fetch_podcast import load_state, save_state, fetch_new_podcast_episodes
from fetch_youtube import fetch_new_youtube_audio
from transcribe import transcribe_file


def main():
    Path(config.DOWNLOAD_DIR).mkdir(exist_ok=True)
    state = load_state(config.STATE_FILE)

    all_new_files = []

    print("=== بررسی پادکست‌ها ===")
    for name, url in config.PODCAST_FEEDS.items():
        new_files = fetch_new_podcast_episodes(
            name, url, config.DOWNLOAD_DIR, state, max_new=config.MAX_EPISODES_PER_RUN
        )
        all_new_files.extend(new_files)

    print("\n=== بررسی یوتیوب ===")
    for name, url in config.YOUTUBE_SOURCES.items():
        new_files = fetch_new_youtube_audio(
            name, url, config.DOWNLOAD_DIR, state, max_new=config.MAX_EPISODES_PER_RUN
        )
        all_new_files.extend(new_files)

    # وضعیت رو همین‌جا ذخیره کن، حتی اگه رونویسی بعداً خطا بده
    save_state(config.STATE_FILE, state)

    if not all_new_files:
        print("\nهیچ محتوای جدیدی پیدا نشد.")
        return

    print(f"\n=== ساخت رونوشت برای {len(all_new_files)} فایل جدید ===")
    for audio_path in all_new_files:
        try:
            transcribe_file(audio_path, model_size=config.WHISPER_MODEL_SIZE)
        except Exception as e:
            print(f"✗ خطا در رونویسی '{audio_path}': {e}")

    print("\nتمام! فایل‌های صوتی و رونوشت‌ها تو پوشه‌ی downloads آماده‌ان.")


if __name__ == "__main__":
    main()
