"""ارزیابی تلفظ سوئدی با Azure Speech (Pronunciation Assessment) — REST، بدون SDK."""
import base64
import io
import json
import wave

import numpy as np
import requests

import word_audio


def to_wav16k(raw):
    """WAV ضبط‌شده (هر نرخ نمونه‌برداری) → WAV تک‌کاناله ۱۶ کیلوهرتز ۱۶ بیت."""
    with wave.open(io.BytesIO(raw), "rb") as w:
        ch, width, rate, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        frames = w.readframes(n)
    if width == 2:
        data = np.frombuffer(frames, dtype="<i2").astype(np.float32)
    elif width == 1:
        data = (np.frombuffer(frames, dtype=np.uint8).astype(np.float32) - 128) * 256
    elif width == 4:
        data = np.frombuffer(frames, dtype="<i4").astype(np.float32) / 65536
    else:
        raise ValueError(f"فرمت ضبط پشتیبانی نمی‌شه (sample width {width})")
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    if rate != 16000 and len(data) > 1:
        t_old = np.arange(len(data)) / rate
        t_new = np.arange(int(len(data) * 16000 / rate)) / 16000
        data = np.interp(t_new, t_old, data)
    pcm = np.clip(data, -32768, 32767).astype("<i2").tobytes()
    out = io.BytesIO()
    with wave.open(out, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(pcm)
    return out.getvalue()


def assess(raw_wav, reference, locale="sv-SE"):
    """برمی‌گردونه: (dict نتیجه‌ی خام Azure). خطا → Exception با متن مناسب."""
    key, region = word_audio._cfg()
    if not key:
        raise RuntimeError("کلید Azure تنظیم نشده.")
    wav = to_wav16k(raw_wav)
    token = word_audio._get_token(key, region)
    cfg = {
        "ReferenceText": reference,
        "GradingSystem": "HundredMark",
        "Granularity": "Phoneme",
        "Dimension": "Comprehensive",
        "EnableMiscue": True,
        "EnableProsodyAssessment": True,
    }
    header = base64.b64encode(json.dumps(cfg).encode()).decode()
    resp = requests.post(
        f"https://{region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1"
        f"?language={locale}&format=detailed",
        headers={
            "Authorization": f"Bearer {token}",
            "Pronunciation-Assessment": header,
            "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
            "Accept": "application/json",
        },
        data=wav,
        timeout=40,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Azure خطا داد ({resp.status_code}): {resp.text[:300]}")
    return resp.json()


GOOD, OK = 80, 60


def summarize(res):
    """نتیجه‌ی خام Azure → {overall:{...}, words:[{word, acc, err, ph}]}."""
    nb = (res.get("NBest") or [{}])[0]
    pa = nb.get("PronunciationAssessment") or {}

    def g(key):
        v = nb.get(key, pa.get(key))
        return None if v is None else round(float(v))

    overall = {"pron": g("PronScore"), "acc": g("AccuracyScore"),
               "flu": g("FluencyScore"), "comp": g("CompletenessScore")}
    words = []
    for w in nb.get("Words") or []:
        wp = w.get("PronunciationAssessment") or {}
        acc = wp.get("AccuracyScore", w.get("AccuracyScore"))
        err = wp.get("ErrorType", w.get("ErrorType")) or "None"
        ph = []
        for p in w.get("Phonemes") or []:
            pp = p.get("PronunciationAssessment") or {}
            ph.append(pp.get("AccuracyScore", p.get("AccuracyScore")))
        words.append({"word": w.get("Word", ""), "acc": None if acc is None else round(float(acc)),
                      "err": err, "ph": ph})
    return {"overall": overall, "words": words}


def weak_words(summary):
    return [w for w in summary["words"]
            if w["err"] in ("Mispronunciation", "Omission") or (w["acc"] is not None and w["acc"] < OK)]


def tips(sentence, weak):
    """نکته‌ی کوتاه فارسی برای کلمه‌های ضعیف (Gemini)."""
    import coach
    from google.genai import types
    lines = "\n".join(
        f"- {w['word']} (نمره {w['acc']}، خطا: {w['err']}، نمره‌ی صداها به ترتیب: {w['ph']})" for w in weak
    )
    prompt = (
        "یک زبان‌آموز فارسی‌زبان جمله‌ی سوئدی زیر را بلند خوانده و ارزیابی تلفظ Azure این کلمه‌ها را ضعیف دانسته:\n"
        f"جمله: {sentence}\n{lines}\n\n"
        "برای هر کلمه‌ی ضعیف، در یک یا دو جمله‌ی فارسیِ ساده بگو احتمالاً کدام صدا برای یک فارسی‌زبان سخت است "
        "و چطور آن را تلفظ کند (مثلاً جای زبان یا لب، مقایسه با صداهای فارسی). "
        "فقط راهنمای عملی بده، حدس‌هایت را قطعی نگو (از «احتمالاً» استفاده کن) و نام واج‌ها را از خودت درنیاور. "
        "قالب: برای هر کلمه یک خط که با خودِ کلمه شروع شود. بدون مقدمه و جمع‌بندی."
    )
    resp = coach.gemini_generate(
        coach.TRANSCRIBE_MODEL, [prompt], types.GenerateContentConfig(max_output_tokens=3000)
    )
    return (resp.text or "").strip()
