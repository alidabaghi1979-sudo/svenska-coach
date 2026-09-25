"""
ساخت کارت‌های Cloze آنکی (با تکه‌ی صوتی واقعی جمله) از کلمات انتخاب‌شده، خروجی .apkg.
فقط نسخه‌ی محلی — به ffmpeg و فایل mp3 محلی نیاز داره.
پیش‌نیاز: pip install genanki
"""
import re
import subprocess
import tempfile
from pathlib import Path

import genanki

# این دو عدد باید همیشه ثابت بمونن (یه‌بار تصادفی تولید شدن) تا وارد کردن‌های بعدی
# دسته‌ی جدید نسازن، بلکه به همون دسته‌ی قبلی اضافه بشن.
MODEL_ID = 1847392655  # نسخه‌ی جدید با قابلیت تایپ جواب (v2)
DECK_ID = 2059573283

CLOZE_MODEL = genanki.Model(
    MODEL_ID,
    "Svenska Coach Cloze v2",
    fields=[{"name": "Text"}, {"name": "Extra"}, {"name": "Audio"}],
    templates=[
        {
            "name": "Cloze",
            "qfmt": "{{type:cloze:Text}}<br>{{Audio}}",
            "afmt": "{{cloze:Text}}<hr id='answer'>{{Extra}}<br>{{Audio}}",
        }
    ],
    model_type=genanki.Model.CLOZE,
)


def _make_cloze_text(sentence, word):
    """کلمه‌ی هدف رو تو جمله با نحو Cloze آنکی ({{c1::کلمه}}) جایگزین می‌کنه."""
    pattern = re.compile(r"\b" + re.escape(word) + r"\b")
    cloze_text, n = pattern.subn(f"{{{{c1::{word}}}}}", sentence, count=1)
    if n == 0:
        cloze_text = sentence.replace(word, f"{{{{c1::{word}}}}}", 1)
    return cloze_text


def _slice_audio(source_path, start, end, out_path):
    """با ffmpeg تکه‌ی صوتی بین start و end (ثانیه) رو می‌بره (با کمی حاشیه)."""
    duration = max(0.5, end - start) + 0.6
    ss = max(0, start - 0.3)
    cmd = [
        "ffmpeg", "-y", "-i", str(source_path),
        "-ss", str(ss), "-t", str(duration),
        "-c:a", "libmp3lame", "-q:a", "4",
        str(out_path),
    ]
    subprocess.run(cmd, capture_output=True, check=True)


def build_apkg(selected_items, deck_subname, output_path):
    """
    selected_items: لیست دیکشنری با کلیدهای:
      word, sentence, meaning, pos, forms, examples,
      audio_source_path (یا None), start (یا None), end (یا None)
    خروجی: مسیر همون output_path که فایل .apkg توش نوشته شده
    """
    deck = genanki.Deck(DECK_ID, f"Svenska Coach::{deck_subname}")
    media_files = []

    with tempfile.TemporaryDirectory() as tmp_dir:
        for item in selected_items:
            cloze_text = _make_cloze_text(item["sentence"], item["word"])

            extra_lines = [f"{item.get('meaning', '')} ({item.get('pos', '')})"]
            if item.get("forms"):
                extra_lines.append(f"صرف: {item['forms']}")
            for ex in item.get("examples", []):
                extra_lines.append(f"{ex.get('sv', '')} — {ex.get('fa', '')}")
            extra = "<br>".join(line for line in extra_lines if line.strip())

            audio_field = ""
            has_audio_info = (
                item.get("audio_source_path")
                and item.get("start") is not None
                and item.get("end") is not None
            )
            if has_audio_info:
                safe_word = re.sub(r"[^a-zA-Z0-9åäöÅÄÖ]", "_", item["word"])
                clip_name = f"clip_{safe_word}_{abs(hash(str(item['start'])))}.mp3"
                clip_path = Path(tmp_dir) / clip_name
                try:
                    _slice_audio(item["audio_source_path"], item["start"], item["end"], clip_path)
                    media_files.append(str(clip_path))
                    audio_field = f"[sound:{clip_name}]"
                except Exception:
                    audio_field = ""

            note = genanki.Note(model=CLOZE_MODEL, fields=[cloze_text, extra, audio_field])
            deck.add_note(note)

        package = genanki.Package(deck)
        package.media_files = media_files
        package.write_to_file(output_path)

    return output_path
