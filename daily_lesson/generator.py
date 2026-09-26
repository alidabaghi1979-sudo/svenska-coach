"""LLM lesson generation with strict JSON output (Claude / Gemini / OpenAI)."""
from __future__ import annotations

import copy
import json
import logging
import re
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, field_validator

from curriculum import Topic
from http_utils import APIError, request_with_retry
from settings import Settings

log = logging.getLogger(__name__)

MIN_SCRIPT_WORDS = 550   # ≈ 5 min at a calm learner pace
MAX_SCRIPT_WORDS = 1100
SPEAKER_RE = re.compile(r"^\s*([A-ZÅÄÖ][A-ZÅÄÖ\- ]{1,20}):\s*(.*)$")


# ─────────────────────────── Schema (pydantic) ───────────────────────────
class GrammarExample(BaseModel):
    sv: str = Field(min_length=1)
    fa: str = Field(min_length=1)


class GrammarFocus(BaseModel):
    rule_name: str = Field(min_length=1)
    explanation_fa: str = Field(min_length=20)
    examples: list[GrammarExample] = Field(min_length=2)


WordClass = Literal["substantiv", "verb", "adjektiv", "fras"]


class VocabItem(BaseModel):
    word: str = Field(min_length=1)
    word_class: WordClass
    translation_fa: str = Field(min_length=1)
    example_sentence_sv: str = Field(min_length=1)
    example_sentence_fa: str = Field(min_length=1)

    @field_validator("word_class", mode="before")
    @classmethod
    def _normalize_class(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.strip().lower()
            aliases = {"noun": "substantiv", "adjective": "adjektiv", "phrase": "fras",
                       "uttryck": "fras", "adverb": "fras", "partikelverb": "verb"}
            return aliases.get(v, v)
        return v


class Lesson(BaseModel):
    lesson_id: int
    title_sv: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    grammar_focus: GrammarFocus
    vocabulary: list[VocabItem] = Field(min_length=8, max_length=12)
    audio_script: str = Field(min_length=200)

    @field_validator("vocabulary", mode="before")
    @classmethod
    def _cap_vocab(cls, v: Any) -> Any:
        return v[:12] if isinstance(v, list) else v

    @property
    def word_count(self) -> int:
        return len(self.audio_script.split())


# Hand-written JSON schema (no $refs) so all three providers accept it.
LESSON_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "lesson_id": {"type": "integer"},
        "title_sv": {"type": "string"},
        "topic": {"type": "string"},
        "grammar_focus": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "rule_name": {"type": "string"},
                "explanation_fa": {"type": "string"},
                "examples": {
                    "type": "array",
                    "minItems": 3,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {"sv": {"type": "string"}, "fa": {"type": "string"}},
                        "required": ["sv", "fa"],
                    },
                },
            },
            "required": ["rule_name", "explanation_fa", "examples"],
        },
        "vocabulary": {
            "type": "array",
            "minItems": 8,
            "maxItems": 12,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "word": {"type": "string"},
                    "word_class": {"type": "string", "enum": ["substantiv", "verb", "adjektiv", "fras"]},
                    "translation_fa": {"type": "string"},
                    "example_sentence_sv": {"type": "string"},
                    "example_sentence_fa": {"type": "string"},
                },
                "required": ["word", "word_class", "translation_fa", "example_sentence_sv", "example_sentence_fa"],
            },
        },
        "audio_script": {"type": "string"},
    },
    "required": ["lesson_id", "title_sv", "topic", "grammar_focus", "vocabulary", "audio_script"],
}


def _strip_keys(schema: Any, keys: set[str]) -> Any:
    s = copy.deepcopy(schema)

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for k in list(node):
                if k in keys:
                    del node[k]
                else:
                    walk(node[k])
        elif isinstance(node, list):
            for x in node:
                walk(x)

    walk(s)
    return s


# ─────────────────────────── Prompt ───────────────────────────
SYSTEM_PROMPT = """You are an experienced SFI/SAS teacher and Swedish podcast host who writes \
listening lessons for adult immigrants in Sweden. The learner's native language is Persian (Farsi).

Write natural, idiomatic, everyday Swedish as it is really spoken in Sweden today — not textbook \
Swedish. Always use correct Swedish characters (å, ä, ö).

AUDIO SCRIPT RULES (the script is sent directly to a text-to-speech engine):
- Length: {min_words}-{max_words} words (5-7 minutes at a calm, clear educational pace).
- EVERY line starts with a speaker tag in CAPITALS followed by a colon. Allowed speakers:
  BERÄTTARE (the podcast host/narrator) and exactly TWO dialogue characters with common Swedish \
first names written in capitals (e.g. JOHAN:, SARA:).
  The FIRST character who speaks in the dialogue is a MAN, the SECOND is a WOMAN.
- Put a line containing only [paus] where a listener needs a short pause to think or repeat.
- Structure:
  1. BERÄTTARE: warm welcome, says the title and today's situation (simple Swedish).
  2. A realistic dialogue (the core, ~60% of the script) in the situation. The grammar focus must \
appear naturally and often. Use most of the vocabulary items.
  3. BERÄTTARE: slowly highlights 4-6 key phrases from the dialogue, repeats each one, adds [paus] \
after each so the listener can repeat aloud.
  4. BERÄTTARE: short, simple explanation of the grammar point IN SWEDISH with 2-3 examples.
  5. BERÄTTARE: a short recap and a friendly goodbye ("Vi hörs i morgon!").
- No stage directions, no markdown, no emojis, no Persian inside audio_script.
- Write numbers the way they are spoken when it matters (e.g. "halv tre", "tjugo kronor").

OTHER FIELDS:
- title_sv: short, catchy Swedish title.
- grammar_focus.explanation_fa: clear explanation in Persian (Farsi) for an adult learner, \
including the rule, word order notes and a typical mistake Persian speakers make. 80-200 words.
- grammar_focus.examples: 3-5 examples taken from or inspired by the script, each with a Persian translation.
- vocabulary: 8-12 of the most useful items from the script. 'word' must include the article for \
nouns (en/ett + plural hint, e.g. "en remiss (remisser)"), all four forms for verbs \
(e.g. "boka (bokar, bokade, bokat)"), and base form for adjectives (with -t/-a forms when irregular). \
word_class is one of: substantiv, verb, adjektiv, fras. \
example_sentence_sv must contain the word (in some form) and should ideally be quoted from the script.
"""

USER_PROMPT = """Create lesson number {lesson_id}.

Topic (situation): {topic}
Grammar focus: {grammar}
Category: {category}
Learner level: {target_level} (topic suggested level: {topic_level}). Keep the language \
comprehensible for this level, but authentic. Slightly challenging is good.
{extra}
Return ONLY the structured lesson object."""


def build_prompts(topic: Topic, lesson_id: int, settings: Settings) -> tuple[str, str]:
    extra = ""
    if topic.round > 1:
        extra = (f"This topic has been covered before (round {topic.round}). Choose a NEW, different "
                 "sub-situation, new characters and new vocabulary than a typical first lesson on it.")
    if topic.category == "sfi_prov":
        extra += ("\nMake it exam-oriented: the narrator explains what the examiner looks for and the "
                  "dialogue models a strong candidate answer.")
    system = SYSTEM_PROMPT.format(min_words=MIN_SCRIPT_WORDS + 50, max_words=MAX_SCRIPT_WORDS - 150)
    user = USER_PROMPT.format(
        lesson_id=lesson_id, topic=topic.topic, grammar=topic.grammar_focus, category=topic.category,
        target_level=settings.target_level, topic_level=topic.level, extra=extra.strip(),
    )
    return system, user


# ─────────────────────────── Providers ───────────────────────────
def _call_claude(system: str, user: str, settings: Settings) -> dict:
    body = {
        "model": settings.llm_model,
        "max_tokens": 12000,
        "system": system,
        "messages": [{"role": "user", "content": user}],
        "tools": [{
            "name": "save_lesson",
            "description": "Save the complete generated Swedish lesson.",
            "input_schema": LESSON_JSON_SCHEMA,
        }],
        "tool_choice": {"type": "tool", "name": "save_lesson"},
    }
    resp = request_with_retry(
        "POST", "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": settings.llm_api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json=body,
    ).json()
    if resp.get("stop_reason") == "max_tokens":
        raise APIError("Claude hit max_tokens — output truncated")
    for block in resp.get("content", []):
        if block.get("type") == "tool_use" and block.get("name") == "save_lesson":
            return block["input"]
    raise APIError(f"Claude returned no tool_use block: {str(resp)[:300]}")


def _call_gemini(system: str, user: str, settings: Settings) -> dict:
    schema = _strip_keys(LESSON_JSON_SCHEMA, {"additionalProperties"})
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 16384,
            "responseMimeType": "application/json",
            "responseSchema": schema,
        },
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.llm_model}:generateContent"
    resp = request_with_retry("POST", url, headers={"x-goog-api-key": settings.llm_api_key}, json=body).json()
    try:
        cand = resp["candidates"][0]
        if cand.get("finishReason") not in (None, "STOP"):
            raise APIError(f"Gemini finishReason={cand.get('finishReason')}")
        text = "".join(p.get("text", "") for p in cand["content"]["parts"])
    except (KeyError, IndexError) as exc:
        raise APIError(f"Unexpected Gemini response: {str(resp)[:300]}") from exc
    return _parse_json_text(text)


def _call_openai(system: str, user: str, settings: Settings) -> dict:
    schema = _strip_keys(LESSON_JSON_SCHEMA, {"minItems", "maxItems"})
    body = {
        "model": settings.llm_model,
        "temperature": 0.8,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": "lesson", "strict": True, "schema": schema}},
    }
    resp = request_with_retry(
        "POST", "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.llm_api_key}"}, json=body,
    ).json()
    choice = resp["choices"][0]
    if choice.get("finish_reason") == "length":
        raise APIError("OpenAI output truncated (finish_reason=length)")
    return _parse_json_text(choice["message"]["content"])


def _parse_json_text(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise APIError(f"Model did not return valid JSON: {exc}") from exc


PROVIDERS = {"claude": _call_claude, "gemini": _call_gemini, "openai": _call_openai}


# ─────────────────────────── Public API ───────────────────────────
def check_script_format(script: str) -> list[str]:
    """Return a list of problems with the audio script (empty = OK)."""
    problems = []
    words = len(script.split())
    if words < MIN_SCRIPT_WORDS:
        problems.append(f"audio_script too short ({words} words, need ≥ {MIN_SCRIPT_WORDS})")
    if words > MAX_SCRIPT_WORDS:
        problems.append(f"audio_script too long ({words} words, max {MAX_SCRIPT_WORDS})")
    lines = [ln for ln in script.splitlines() if ln.strip() and ln.strip().lower() != "[paus]"]
    tagged = sum(1 for ln in lines if SPEAKER_RE.match(ln))
    if lines and tagged / len(lines) < 0.8:
        problems.append("most lines must start with a SPEAKER: tag")
    speakers = {SPEAKER_RE.match(ln).group(1).strip() for ln in lines if SPEAKER_RE.match(ln)}
    if len(speakers - {"BERÄTTARE"}) > 2:
        problems.append(f"too many dialogue speakers: {sorted(speakers)}")
    return problems


def generate_lesson(topic: Topic, lesson_id: int, settings: Settings, max_attempts: int = 3) -> Lesson:
    """Generate and validate a lesson. Re-prompts with feedback if validation fails."""
    if settings.llm_provider not in PROVIDERS:
        raise ValueError(f"Unknown LLM_PROVIDER '{settings.llm_provider}'. Use: {', '.join(PROVIDERS)}")
    if not settings.llm_api_key:
        raise ValueError("LLM_API_KEY is not set")

    call = PROVIDERS[settings.llm_provider]
    system, user = build_prompts(topic, lesson_id, settings)
    feedback = ""
    last_problem = ""

    for attempt in range(1, max_attempts + 1):
        log.info("Generating lesson %d with %s/%s (attempt %d): %s",
                 lesson_id, settings.llm_provider, settings.llm_model, attempt, topic.topic)
        raw = call(system, user + feedback, settings)
        raw["lesson_id"] = lesson_id  # we own the id, not the model
        try:
            lesson = Lesson.model_validate(raw)
        except ValidationError as exc:
            last_problem = f"schema validation failed: {exc.errors()[:5]}"
        else:
            problems = check_script_format(lesson.audio_script)
            if not problems:
                log.info("Lesson OK: '%s' — %d words, %d vocab", lesson.title_sv, lesson.word_count,
                         len(lesson.vocabulary))
                return lesson
            last_problem = "; ".join(problems)
        log.warning("Attempt %d rejected: %s", attempt, last_problem)
        feedback = f"\n\nIMPORTANT — your previous answer was rejected: {last_problem}. Fix this."

    raise RuntimeError(f"Could not generate a valid lesson after {max_attempts} attempts: {last_problem}")
