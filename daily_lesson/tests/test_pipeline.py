import json
import sqlite3
from datetime import date

import pytest
from conftest import FakeResponse, sample_lesson_dict

import generator
import main
import tts
from curriculum import Curriculum, StateStore
from generator import Lesson, check_script_format
from storage import Storage, lemma_of, make_cloze


# ─────────────────────────── curriculum ───────────────────────────
def test_curriculum_has_60_plus_topics_and_all_weekdays(env):
    cur = Curriculum(env.curriculum_path)
    assert len(cur.topics) >= 60
    assert len({t["id"] for t in cur.topics}) == len(cur.topics)
    for wd in range(7):
        assert cur.by_category(cur.weekday_categories[str(wd)]), wd


def test_pick_topic_follows_weekly_cycle_and_wraps(env):
    cur = Curriculum(env.curriculum_path)
    state = StateStore(env.state_path)
    tuesday, saturday = date(2026, 9, 29), date(2026, 10, 3)
    t, upd = state.pick_topic(cur, tuesday, "weekday")
    assert t.category == "arbete" and upd == {"key": "arbete", "cursor": 1}
    t, _ = state.pick_topic(cur, saturday, "weekday")
    assert t.category == "sfi_prov"
    # wrap-around → round 2
    state.data["category_cursor"]["sfi_prov"] = len(cur.by_category("sfi_prov"))
    t, _ = state.pick_topic(cur, saturday, "weekday")
    assert t.round == 2 and t.id == cur.by_category("sfi_prov")[0]["id"]


# ─────────────────────────── generator ───────────────────────────
def _claude_reply(payload):
    return FakeResponse({"stop_reason": "tool_use",
                         "content": [{"type": "tool_use", "name": "save_lesson", "input": payload}]})


def test_generate_lesson_claude_retries_on_short_script(env, monkeypatch):
    calls = []
    replies = [_claude_reply(sample_lesson_dict(script_words=100)), _claude_reply(sample_lesson_dict())]

    def fake(method, url, **kw):
        calls.append(kw["json"])
        return replies.pop(0)

    monkeypatch.setattr(generator, "request_with_retry", fake)
    from curriculum import Topic
    lesson = generator.generate_lesson(Topic.manual("Vårdcentralen", "Modala hjälpverb", "A2"), 7, env)
    assert lesson.lesson_id == 7                         # id overridden
    assert len(calls) == 2
    assert "rejected" in calls[1]["messages"][0]["content"]  # feedback sent on retry
    assert calls[0]["tool_choice"] == {"type": "tool", "name": "save_lesson"}
    assert calls[0]["model"] == "claude-sonnet-5"


@pytest.mark.parametrize("provider", ["gemini", "openai"])
def test_generate_lesson_other_providers(env, monkeypatch, provider):
    monkeypatch.setenv("LLM_PROVIDER", provider)
    from settings import get_settings
    s = get_settings()
    text = json.dumps(sample_lesson_dict(), ensure_ascii=False)
    if provider == "gemini":
        reply = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"text": text}]}}]}
    else:
        reply = {"choices": [{"finish_reason": "stop", "message": {"content": text}}]}
    seen = {}

    def fake(method, url, **kw):
        seen.update(url=url, body=kw["json"])
        return FakeResponse(reply)

    monkeypatch.setattr(generator, "request_with_retry", fake)
    from curriculum import Topic
    lesson = generator.generate_lesson(Topic.manual("X", "Y", "A2"), 1, s)
    assert lesson.title_sv == "Hos vårdcentralen"
    assert "additionalProperties" not in json.dumps(seen["body"]) or provider == "openai"


def test_script_format_checks():
    bad = "Hej hej " * 400
    assert any("SPEAKER" in p for p in check_script_format(bad))
    assert check_script_format(sample_lesson_dict()["audio_script"]) == []


# ─────────────────────────── TTS ───────────────────────────
def test_parse_script_roles_and_pauses():
    segs = tts.parse_script("BERÄTTARE: Hej!\n[paus]\nJOHAN: Tjena.\nSARA: Hej Johan. [paus] Hur mår du?\nJOHAN: Bra.")
    assert [s.role for s in segs] == ["narrator", "male", "female", "female", "male"]
    assert segs[0].pause_after_ms == 1800
    assert segs[2].pause_after_ms == 1800


def test_azure_ssml_escaping_and_rate(env):
    engine = tts.AzureTTS(env)
    ssml = engine.build_ssml([tts.Segment("male", "Räksmörgås & kaffe <3")])
    assert 'rate="-5%"' in ssml
    assert "sv-SE-MattiasNeural" in ssml
    assert "&amp; kaffe &lt;3" in ssml and "Räksmörgås" in ssml


def test_azure_chunks_respect_voice_limit(env):
    engine = tts.AzureTTS(env)
    segs = [tts.Segment("narrator", "Hej där.") for _ in range(95)]
    chunks = engine._chunks(segs)
    assert len(chunks) == 3 and all(len(c) <= 40 for c in chunks)


# ─────────────────────────── storage ───────────────────────────
def test_cloze_and_lemma():
    lesson = Lesson.model_validate(sample_lesson_dict())
    v = {x.word: x for x in lesson.vocabulary}
    assert lemma_of("en remiss (remisser)") == "remiss"
    assert lemma_of("att ringa (ringer)") == "ringa"
    assert make_cloze(v["en remiss (remisser)"]) == "Jag måste nog få en {{c1::remiss::ارجاع پزشکی}}."
    assert "{{c1::ringde::" in make_cloze(v["att ringa (ringer, ringde, ringt)"])
    assert "{{c1::gick::" in make_cloze(v["gå (går, gick, gått)"])   # irregular form from parentheses


# ─────────────────────────── end-to-end ───────────────────────────
def test_run_daily_end_to_end(env, monkeypatch, tone_mp3, tmp_path):
    monkeypatch.setattr(generator, "request_with_retry",
                        lambda *a, **k: _claude_reply(sample_lesson_dict()))
    tts_calls = []

    def fake_tts(method, url, **kw):
        tts_calls.append(kw["data"].decode("utf-8"))
        return FakeResponse(content=tone_mp3)

    monkeypatch.setattr(tts, "request_with_retry", fake_tts)

    rc = main.main(["run-daily", "--date", "2026-09-28"])   # a Monday → vardag
    assert rc == 0
    data = env.data_dir
    mp3s = list((data / "audio").glob("*.mp3"))
    assert len(mp3s) == 1 and mp3s[0].name.startswith("0001_")
    from mutagen.id3 import ID3
    tags = ID3(mp3s[0])
    assert "Hos vårdcentralen" in str(tags["TIT2"]) and tags.getall("USLT")
    assert all("<speak" in c and "xml:lang=\"sv-SE\"" in c for c in tts_calls)

    state = json.loads((data / "state.json").read_text(encoding="utf-8"))
    assert state["last_lesson_id"] == 1 and state["category_cursor"] == {"vardag": 1}

    con = sqlite3.connect(data / "lessons.db")
    assert con.execute("SELECT count(*) FROM lessons").fetchone()[0] == 1
    assert con.execute("SELECT count(*) FROM vocabulary").fetchone()[0] == 9
    assert con.execute("SELECT count(*) FROM grammar_notes").fetchone()[0] == 1
    assert list((data / "exports").glob("*.apkg"))
    assert list((data / "lessons").glob("0001_*.md")) and list((data / "lessons").glob("0001_*.json"))
    assert "Lektion 1" in (tmp_path / "summary.md").read_text(encoding="utf-8")

    # second run same day → skipped; --force → lesson 2 with next vardag topic
    assert main.main(["run-daily", "--date", "2026-09-28"]) == 0
    assert json.loads((data / "state.json").read_text())["last_lesson_id"] == 1
    assert main.main(["run-daily", "--date", "2026-09-28", "--force"]) == 0
    assert json.loads((data / "state.json").read_text())["category_cursor"] == {"vardag": 2}

    # manual topic + export command
    assert main.main(["run-topic", "Att köpa en cykel", "Adjektivets böjning", "--no-audio"]) == 0
    assert main.main(["export-anki", "--lesson-id", "3", "--format", "tsv"]) == 0
    tsv = next((data / "exports").glob("lesson_0003_*_cloze.tsv")).read_text(encoding="utf-8")
    assert tsv.startswith("#separator:tab") and "{{c1::" in tsv


def test_audio_failure_keeps_lesson_and_state(env, monkeypatch):
    monkeypatch.setattr(generator, "request_with_retry",
                        lambda *a, **k: _claude_reply(sample_lesson_dict()))

    def boom(*a, **k):
        raise tts.APIError("azure down") if hasattr(tts, "APIError") else RuntimeError("azure down")

    monkeypatch.setattr(tts, "request_with_retry", boom)
    rc = main.main(["run-daily", "--date", "2026-09-29"])
    assert rc == 2                                    # non-zero so CI shows a warning
    st = Storage(env.db_path, env.lessons_dir)
    assert st.get_lesson(1)["lesson"]["audio_path"] is None


def test_ssml_is_well_formed_xml(env):
    import xml.etree.ElementTree as ET
    engine = tts.AzureTTS(env)
    segs = tts.parse_script(sample_lesson_dict()["audio_script"])
    for chunk in engine._chunks(segs):
        ET.fromstring(engine.build_ssml(chunk))  # raises if malformed


def test_drive_upload_flow(env, monkeypatch, tmp_path):
    import drive_sync
    monkeypatch.setenv("GDRIVE_CLIENT_ID", "id")
    monkeypatch.setenv("GDRIVE_CLIENT_SECRET", "secret")
    monkeypatch.setenv("GDRIVE_REFRESH_TOKEN", "refresh")
    from settings import get_settings
    s = get_settings()
    calls = []

    def fake(method, url, **kw):
        calls.append((method, url))
        if "oauth2" in url:
            return FakeResponse({"access_token": "tok"})
        if method == "GET":
            return FakeResponse({"files": []})
        if url.endswith("/permissions"):
            assert kw["json"] == {"role": "reader", "type": "anyone"}
            return FakeResponse({})
        if method == "POST" and "upload" not in url:
            return FakeResponse({"id": "folder123"})
        if method == "POST":
            return FakeResponse({}, headers={"Location": "https://upload/session"})
        return FakeResponse({"id": "f1", "webViewLink": "https://drive.google.com/file/d/f1/view"})

    monkeypatch.setattr(drive_sync, "request_with_retry", fake)
    f = tmp_path / "a.mp3"
    f.write_bytes(b"x" * 100)
    client = drive_sync.DriveClient(s)
    folder = client.ensure_folder(None)
    assert folder == "folder123"
    file_id, link = client.upload(f, folder)
    assert file_id == "f1" and link == "https://drive.google.com/uc?export=download&id=f1"
    assert any(c[1].endswith("/f1/permissions") for c in calls)
    assert sum(1 for c in calls if "oauth2" in c[1]) == 1   # token cached


# ─────────────────────────── Svenska Coach (Google Sheets) ───────────────────────────
class FakeWorksheet:
    def __init__(self, rows=None):
        self.rows = rows or []

    def row_values(self, i):
        return self.rows[i - 1] if len(self.rows) >= i else []

    def col_values(self, c):
        return [r[c - 1] if len(r) >= c else "" for r in self.rows]

    def update(self, range_name, values, value_input_option=None):
        import re
        m = re.match(r"([A-Z])(\d+)", range_name)
        col, row = ord(m.group(1)) - 65, int(m.group(2))
        while len(self.rows) < row:
            self.rows.append([])
        r = self.rows[row - 1]
        r.extend([""] * (col + len(values[0]) - len(r)))
        r[col:col + len(values[0])] = [str(x) for x in values[0]]

    def append_row(self, row, value_input_option=None):
        self.rows.append([str(x) for x in row])

    def append_rows(self, rows, value_input_option=None):
        for r in rows:
            self.append_row(r)


class FakeSpreadsheet:
    def __init__(self):
        self.tabs = {"ordbank": FakeWorksheet([["تاریخ", "کلمه", "معنی", "جمله", "سطح", "مرور_بعدی"],
                                               ["2026-09-01", "remiss", "ارجاع", "", "2", ""]])}

    def worksheet(self, name):
        import gspread
        if name not in self.tabs:
            raise gspread.WorksheetNotFound(name)
        return self.tabs[name]

    def add_worksheet(self, title, rows, cols):
        self.tabs[title] = FakeWorksheet()
        return self.tabs[title]


def test_pipeline_pushes_lesson_and_vocab_to_app_sheet(env, monkeypatch, tone_mp3):
    import sheets_sync
    monkeypatch.setenv("SVENSKA_SHEET_ID", "sheet123")
    monkeypatch.setenv("GCP_SERVICE_ACCOUNT_JSON", '{"type": "service_account"}')
    fake = FakeSpreadsheet()
    monkeypatch.setattr(sheets_sync, "_open", lambda s: fake)
    monkeypatch.setattr(generator, "request_with_retry", lambda *a, **k: _claude_reply(sample_lesson_dict()))
    monkeypatch.setattr(tts, "request_with_retry", lambda *a, **k: FakeResponse(content=tone_mp3))

    assert main.main(["run-daily", "--date", "2026-09-28"]) == 0
    lessons = fake.tabs["lessons"].rows
    assert lessons[0] == sheets_sync.LESSONS_HEADER
    assert lessons[1][1] == "1" and lessons[1][2] == "Hos vårdcentralen"
    assert json.loads(lessons[1][8])[0]["word"] == "en remiss (remisser)"
    ordbank = fake.tabs["ordbank"].rows
    words = [r[1] for r in ordbank[2:]]
    assert "en remiss (remisser)" not in words          # already in bank as 'remiss' → skipped
    assert len(words) == 8 and all(r[4] == "0" and r[5] == "" for r in ordbank[2:])

    # re-sync updates the same row instead of duplicating
    assert main.main(["sync-sheets", "--lesson-id", "1"]) == 0
    assert len(fake.tabs["lessons"].rows) == 2
    assert len(fake.tabs["ordbank"].rows) == 10


def test_sheets_failure_is_reported_but_lesson_saved(env, monkeypatch, tone_mp3):
    import sheets_sync
    monkeypatch.setenv("SVENSKA_SHEET_ID", "sheet123")
    monkeypatch.setenv("GCP_SERVICE_ACCOUNT_JSON", '{"type": "service_account"}')

    def boom(s):
        raise RuntimeError("403 permission denied")

    monkeypatch.setattr(sheets_sync, "_open", boom)
    monkeypatch.setattr(generator, "request_with_retry", lambda *a, **k: _claude_reply(sample_lesson_dict()))
    monkeypatch.setattr(tts, "request_with_retry", lambda *a, **k: FakeResponse(content=tone_mp3))
    assert main.main(["run-daily", "--date", "2026-09-28"]) == 2
    assert json.loads(env.state_path.read_text())["last_lesson_id"] == 1


def test_reads_keys_from_app_secrets(tmp_path, monkeypatch):
    import settings as st_mod
    secrets = tmp_path / "secrets.toml"
    secrets.write_text('svenska_sheet_id = "S1"\n[claude]\napi_key = "sk-ant-x"\n'
                       '[gcp_service_account]\ntype = "service_account"\n'
                       '[gdrive_oauth]\nclient_id = "c"\nclient_secret = "s"\nrefresh_token = "r"\n',
                       encoding="utf-8")
    monkeypatch.setattr(st_mod, "APP_SECRETS", secrets)
    monkeypatch.delenv("IGNORE_APP_SECRETS", raising=False)
    for k in ["LLM_API_KEY", "SVENSKA_SHEET_ID", "GCP_SERVICE_ACCOUNT_JSON", "GDRIVE_CLIENT_ID",
              "GDRIVE_CLIENT_SECRET", "GDRIVE_REFRESH_TOKEN", "LLM_PROVIDER"]:
        monkeypatch.delenv(k, raising=False)
    st_mod.app_secrets.cache_clear()
    s = st_mod.get_settings()
    st_mod.app_secrets.cache_clear()
    assert s.llm_api_key == "sk-ant-x" and s.sheet_id == "S1"
    assert s.sheets_enabled and s.gdrive_enabled


def test_headers_match_app_sheets_helper():
    """The app (../sheets_helper.py) and the pipeline must agree on column names."""
    import ast
    from pathlib import Path
    import sheets_sync
    app_helper = Path(__file__).resolve().parents[2] / "sheets_helper.py"
    if not app_helper.exists():
        pytest.skip("not inside the Svenska Coach repo")
    tree = ast.parse(app_helper.read_text(encoding="utf-8"))
    tabs = next(ast.literal_eval(n.value) for n in ast.walk(tree)
                if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "SHEET_TABS")
    assert tabs["lessons"] == sheets_sync.LESSONS_HEADER
    assert tabs["ordbank"] == sheets_sync.ORDBANK_HEADER
