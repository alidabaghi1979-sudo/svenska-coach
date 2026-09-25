"""
تولید رونوشت متنی سوئدی از فایل صوتی با faster-whisper (اجرا روی خود سیستم، بدون اینترنت بعد از دانلود مدل).
پیش‌نیاز: pip install faster-whisper
"""
from pathlib import Path

from faster_whisper import WhisperModel

_model_cache = {}


def get_model(model_size="small"):
    """مدل رو فقط یک بار بارگذاری می‌کنه و تو حافظه نگه می‌داره."""
    if model_size not in _model_cache:
        print(f"در حال بارگذاری مدل Whisper ({model_size})... اولین بار ممکنه چند دقیقه طول بکشه")
        _model_cache[model_size] = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _model_cache[model_size]


def transcribe_file(audio_path, model_size="small"):
    """
    فایل صوتی رو رونویسی می‌کنه — با تشخیص خودکار زبان (بدون اجبار به سوئدی، چون بعضی
    منابع مثل Ny i Sverige-podden چندزبانه‌ان و باید بفهمیم واقعاً چه زبونیه).
    رونوشت رو کنار همون فایل با پسوند .txt ذخیره می‌کنه.
    خروجی: (مسیر فایل متنی، کد زبان تشخیص‌داده‌شده مثل "sv" یا "en")
    """
    model = get_model(model_size)
    segments, info = model.transcribe(audio_path)

    text_lines = []
    for segment in segments:
        text_lines.append(f"[{segment.start:.1f}s -> {segment.end:.1f}s] {segment.text.strip()}")

    txt_path = Path(audio_path).with_suffix(".txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(text_lines))

    print(f"✓ رونوشت ذخیره شد: {txt_path} (زبان تشخیص‌داده‌شده: {info.language})")
    return str(txt_path), info.language
