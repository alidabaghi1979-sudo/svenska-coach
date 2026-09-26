"""Text-to-speech: Azure Speech (default) or ElevenLabs → tagged MP3."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

from http_utils import request_with_retry
from settings import Settings

log = logging.getLogger(__name__)

NARRATOR_TAG = "BERÄTTARE"
PAUSE_RE = re.compile(r"^\s*\[paus\]\s*$", re.IGNORECASE)
SPEAKER_RE = re.compile(r"^\s*([A-ZÅÄÖ][A-ZÅÄÖ\- ]{1,20}):\s*(.*)$")
INLINE_PAUSE_RE = re.compile(r"\[paus\]", re.IGNORECASE)


@dataclass
class Segment:
    role: str          # "narrator" | "male" | "female"
    text: str
    pause_after_ms: int = 350


# ─────────────────────────── Script parsing ───────────────────────────
def parse_script(script: str) -> list[Segment]:
    """Turn 'SPEAKER: text' lines into segments with a role per voice.

    BERÄTTARE → narrator. First other speaker → male, second → female
    (the generator prompt enforces this order). Unknown extra speakers
    alternate between male/female. Untagged lines continue the last speaker.
    """
    segments: list[Segment] = []
    roles: dict[str, str] = {NARRATOR_TAG: "narrator"}
    current_role = "narrator"

    for raw in script.splitlines():
        line = raw.strip()
        if not line:
            continue
        if PAUSE_RE.match(line):
            if segments:
                segments[-1].pause_after_ms = max(segments[-1].pause_after_ms, 1800)
            continue
        m = SPEAKER_RE.match(line)
        if m:
            name, text = m.group(1).strip(), m.group(2).strip()
            if name not in roles:
                n_chars = len([r for r in roles if r != NARRATOR_TAG])
                roles[name] = "male" if n_chars % 2 == 0 else "female"
            current_role = roles[name]
        else:
            text = line
        # inline [paus] inside a line → split into two segments
        parts = [p.strip() for p in INLINE_PAUSE_RE.split(text)]
        for i, part in enumerate(parts):
            if part:
                segments.append(Segment(current_role, part))
            if i < len(parts) - 1 and segments:
                segments[-1].pause_after_ms = 1800

    # a slightly longer breath when the speaker changes
    for a, b in zip(segments, segments[1:]):
        if a.role != b.role:
            a.pause_after_ms = max(a.pause_after_ms, 600)
    return segments


def _rate_percent(rate: float) -> str:
    pct = round((rate - 1.0) * 100)
    return f"{pct:+d}%"


# ─────────────────────────── Azure ───────────────────────────
class AzureTTS:
    OUTPUT_FORMAT = "audio-24khz-96kbitrate-mono-mp3"
    MAX_VOICE_ELEMENTS = 40      # Azure limit is 50 per request
    MAX_CHARS = 6000             # conservative per-request text budget

    def __init__(self, settings: Settings):
        if not settings.tts_api_key:
            raise ValueError("TTS_API_KEY (Azure Speech key) is not set")
        self.s = settings
        self.url = f"https://{settings.azure_region}.tts.speech.microsoft.com/cognitiveservices/v1"
        self.voices = {
            "narrator": settings.azure_voice_narrator,
            "male": settings.azure_voice_male,
            "female": settings.azure_voice_female,
        }

    def build_ssml(self, segments: list[Segment]) -> str:
        rate = _rate_percent(self.s.speaking_rate)
        body = []
        for seg in segments:
            body.append(
                f'<voice name="{self.voices[seg.role]}"><prosody rate="{rate}">{escape(seg.text)}</prosody>'
                f'<break time="{seg.pause_after_ms}ms"/></voice>'
            )
        return ('<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
                'xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="sv-SE">' + "".join(body) + "</speak>")

    def _chunks(self, segments: list[Segment]) -> list[list[Segment]]:
        chunks, cur, chars = [], [], 0
        for seg in segments:
            if cur and (len(cur) >= self.MAX_VOICE_ELEMENTS or chars + len(seg.text) > self.MAX_CHARS):
                chunks.append(cur)
                cur, chars = [], 0
            cur.append(seg)
            chars += len(seg.text)
        if cur:
            chunks.append(cur)
        return chunks

    def synthesize(self, segments: list[Segment]) -> bytes:
        audio = bytearray()
        chunks = self._chunks(segments)
        for i, chunk in enumerate(chunks, 1):
            ssml = self.build_ssml(chunk)
            log.info("Azure TTS chunk %d/%d (%d segments)", i, len(chunks), len(chunk))
            resp = request_with_retry(
                "POST", self.url,
                headers={
                    "Ocp-Apim-Subscription-Key": self.s.tts_api_key,
                    "Content-Type": "application/ssml+xml; charset=utf-8",
                    "X-Microsoft-OutputFormat": self.OUTPUT_FORMAT,
                    "User-Agent": "svenska-daily-lesson",
                },
                data=ssml.encode("utf-8"),
            )
            audio.extend(resp.content)
        return bytes(audio)


# ─────────────────────────── ElevenLabs ───────────────────────────
class ElevenLabsTTS:
    MAX_CHARS = 2500

    def __init__(self, settings: Settings):
        if not settings.tts_api_key:
            raise ValueError("TTS_API_KEY (ElevenLabs key) is not set")
        if not settings.eleven_voice_narrator:
            raise ValueError("ELEVENLABS_VOICE_NARRATOR is not set")
        self.s = settings
        a = settings.eleven_voice_narrator
        self.voices = {
            "narrator": a,
            "male": settings.eleven_voice_male or a,
            "female": settings.eleven_voice_female or settings.eleven_voice_male or a,
        }

    def _merge(self, segments: list[Segment]) -> list[tuple[str, str]]:
        """Merge consecutive same-voice segments into ≤ MAX_CHARS requests."""
        out: list[tuple[str, str]] = []
        for seg in segments:
            voice = self.voices[seg.role]
            piece = f'{seg.text} <break time="{seg.pause_after_ms / 1000:.1f}s" />'
            if out and out[-1][0] == voice and len(out[-1][1]) + len(piece) < self.MAX_CHARS:
                out[-1] = (voice, out[-1][1] + " " + piece)
            else:
                out.append((voice, piece))
        return out

    def synthesize(self, segments: list[Segment]) -> bytes:
        audio = bytearray()
        requests_ = self._merge(segments)
        speed = min(1.2, max(0.7, self.s.speaking_rate))
        for i, (voice, text) in enumerate(requests_, 1):
            log.info("ElevenLabs TTS request %d/%d", i, len(requests_))
            resp = request_with_retry(
                "POST",
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
                headers={"xi-api-key": self.s.tts_api_key, "Content-Type": "application/json"},
                json={
                    "text": text,
                    "model_id": self.s.eleven_model,
                    "voice_settings": {"stability": 0.55, "similarity_boost": 0.75, "speed": speed},
                },
            )
            audio.extend(resp.content)
        return bytes(audio)


PROVIDERS = {"azure": AzureTTS, "elevenlabs": ElevenLabsTTS}


# ─────────────────────────── ID3 tags ───────────────────────────
def write_id3_tags(path: Path, *, title: str, lesson_id: int, topic: str, grammar: str,
                   category: str, lyrics: str, day: date) -> float:
    """Write ID3 metadata. Returns duration in seconds (0 if unknown)."""
    from mutagen.id3 import COMM, ID3, TALB, TCON, TDRC, TIT2, TLAN, TPE1, TRCK, USLT, ID3NoHeaderError
    from mutagen.mp3 import MP3

    try:
        tags = ID3(path)
    except ID3NoHeaderError:
        tags = ID3()
    tags.add(TIT2(encoding=3, text=f"{lesson_id:03d} – {title}"))
    tags.add(TPE1(encoding=3, text="Svenska Daily Lesson"))
    tags.add(TALB(encoding=3, text=f"Svenska Daily – {category}"))
    tags.add(TRCK(encoding=3, text=str(lesson_id)))
    tags.add(TDRC(encoding=3, text=day.isoformat()))
    tags.add(TCON(encoding=3, text="Podcast"))
    tags.add(TLAN(encoding=3, text="swe"))
    tags.add(COMM(encoding=3, lang="swe", desc="topic", text=f"{topic} | Grammatik: {grammar}"))
    tags.add(USLT(encoding=3, lang="swe", desc="script", text=lyrics))
    tags.save(path, v2_version=3)
    try:
        return float(MP3(path).info.length)
    except Exception:  # noqa: BLE001 — duration is nice-to-have
        return 0.0


# ─────────────────────────── Public API ───────────────────────────
def synthesize_to_mp3(script: str, out_path: Path, settings: Settings) -> Path:
    provider = settings.tts_provider
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown TTS_PROVIDER '{provider}'. Use: {', '.join(PROVIDERS)}")
    segments = parse_script(script)
    if not segments:
        raise ValueError("Audio script is empty after parsing")
    engine = PROVIDERS[provider](settings)
    audio = engine.synthesize(segments)
    if len(audio) < 10_000:
        raise RuntimeError(f"TTS returned suspiciously small audio ({len(audio)} bytes)")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(audio)
    log.info("Saved audio: %s (%.1f MB)", out_path, len(audio) / 1e6)
    return out_path
