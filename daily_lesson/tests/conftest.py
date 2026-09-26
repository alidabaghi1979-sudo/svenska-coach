import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

FIXTURES = Path(__file__).parent / "fixtures"


def sample_script(words_target: int = 700) -> str:
    dialogue = [
        "BERÄTTARE: Hej och välkommen till dagens lektion! Idag ska vi till vårdcentralen.",
        "[paus]",
        "JOHAN: Hej, jag skulle vilja boka en tid hos en läkare, tack.",
        "SARA: Absolut. Vad gäller det? Har du ont någonstans?",
        "JOHAN: Ja, jag har haft ont i halsen i en vecka och jag måste nog få en remiss.",
        "SARA: Okej, du kan få en tid på tisdag klockan halv tre. Passar det? [paus] Bra.",
        "BERÄTTARE: Lyssna igen: jag skulle vilja boka en tid.",
        "[paus]",
    ]
    lines, count = [], 0
    while count < words_target:
        for ln in dialogue:
            lines.append(ln)
            count += len(ln.split())
    lines.append("BERÄTTARE: Tack för idag. Vi hörs i morgon!")
    return "\n".join(lines)


def sample_lesson_dict(lesson_id: int = 1, script_words: int = 700) -> dict:
    vocab = [
        ("en remiss (remisser)", "substantiv", "ارجاع پزشکی", "Jag måste nog få en remiss."),
        ("boka (bokar, bokade, bokat)", "verb", "رزرو کردن", "Jag skulle vilja boka en tid."),
        ("ont", "fras", "درد", "Har du ont någonstans?"),
        ("en läkare (läkare)", "substantiv", "پزشک", "Jag vill träffa en läkare."),
        ("passa (passar, passade, passat)", "verb", "مناسب بودن", "Passar det på tisdag?"),
        ("en vårdcentral (vårdcentraler)", "substantiv", "درمانگاه", "Jag ringer vårdcentralen."),
        ("att ringa (ringer, ringde, ringt)", "verb", "زنگ زدن", "Jag ringde i morse."),
        ("sjuk", "adjektiv", "بیمار", "Jag är sjuk idag."),
        ("gå (går, gick, gått)", "verb", "رفتن", "Hon gick hem tidigt."),
    ]
    return {
        "lesson_id": 999,  # generator must override this
        "title_sv": "Hos vårdcentralen",
        "topic": "Att gå till vårdcentralen",
        "grammar_focus": {
            "rule_name": "Modala hjälpverb",
            "explanation_fa": "افعال کمکی مثل måste و kan قبل از فعل اصلی مصدری بدون att می‌آیند. " * 3,
            "examples": [
                {"sv": "Jag måste gå.", "fa": "باید بروم."},
                {"sv": "Du kan komma.", "fa": "می‌توانی بیایی."},
                {"sv": "Vi ska äta.", "fa": "قرار است غذا بخوریم."},
            ],
        },
        "vocabulary": [
            {"word": w, "word_class": c, "translation_fa": fa, "example_sentence_sv": ex,
             "example_sentence_fa": "ترجمه"}
            for w, c, fa, ex in vocab
        ],
        "audio_script": sample_script(script_words),
    }


class FakeResponse:
    def __init__(self, json_data=None, content: bytes = b"", headers=None):
        self._json = json_data
        self.content = content
        self.headers = headers or {}
        self.ok = True
        self.status_code = 200
        self.text = ""

    def json(self):
        return self._json


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Isolated settings pointing at a temp data dir."""
    for k in ["GDRIVE_CLIENT_ID", "GDRIVE_CLIENT_SECRET", "GDRIVE_REFRESH_TOKEN", "LLM_MODEL",
              "SVENSKA_SHEET_ID", "GCP_SERVICE_ACCOUNT_JSON"]:
        monkeypatch.setenv(k, "")
    monkeypatch.setenv("IGNORE_APP_SECRETS", "1")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LLM_PROVIDER", "claude")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("TTS_PROVIDER", "azure")
    monkeypatch.setenv("TTS_API_KEY", "test-tts-key")
    monkeypatch.setenv("TOPIC_MODE", "weekday")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary.md"))
    from settings import get_settings
    return get_settings()


@pytest.fixture
def tone_mp3() -> bytes:
    return (FIXTURES / "tone.mp3").read_bytes()
