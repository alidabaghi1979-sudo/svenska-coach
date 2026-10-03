"""تمرین‌های خودکارِ هر درس — تولید با LLM (گرامر + درک مطلب) و ساخت محلی (واژگان).

مثل تایم‌استمپِ کارائوکه، این مرحله کاملاً best-effort است: اگه تولید تمرین‌ها خطا
بده، فقط اون درس تمرین نداره — پایپ‌لاین اصلی (درس + صدا) هیچ‌وقت به خاطر این خراب
نمی‌شه.
"""
from __future__ import annotations

import logging
import random
import re
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from generator import Lesson, VocabItem, _parse_json_text, _strip_keys
from http_utils import APIError, request_with_retry
from settings import Settings

log = logging.getLogger(__name__)


# ─────────────────────────── Schema (pydantic) ───────────────────────────
class GrammarQuestion(BaseModel):
    sentence_sv: str = Field(min_length=3)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    explanation_fa: str = Field(min_length=5)


class ComprehensionQuestion(BaseModel):
    question_fa: str = Field(min_length=3)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)


class VocabQuestion(BaseModel):
    word_sv: str
    options: list[str]
    correct_index: int = Field(ge=0)


class ExerciseSet(BaseModel):
    lesson_id: int
    grammar: list[GrammarQuestion] = Field(min_length=1)
    comprehension: list[ComprehensionQuestion] = Field(min_length=1)
    vocab: list[VocabQuestion] = Field(default_factory=list)


GRAMMAR_COUNT = 5
COMPREHENSION_COUNT = 4

# Hand-written JSON schema (no $refs) so all three providers accept it.
EXERCISES_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "grammar": {
            "type": "array",
            "minItems": GRAMMAR_COUNT,
            "maxItems": GRAMMAR_COUNT,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "sentence_sv": {"type": "string"},
                    "options": {"type": "array", "minItems": 4, "maxItems": 4, "items": {"type": "string"}},
                    "correct_index": {"type": "integer"},
                    "explanation_fa": {"type": "string"},
                },
                "required": ["sentence_sv", "options", "correct_index", "explanation_fa"],
            },
        },
        "comprehension": {
            "type": "array",
            "minItems": COMPREHENSION_COUNT,
            "maxItems": COMPREHENSION_COUNT,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "question_fa": {"type": "string"},
                    "options": {"type": "array", "minItems": 4, "maxItems": 4, "items": {"type": "string"}},
                    "correct_index": {"type": "integer"},
                },
                "required": ["question_fa", "options", "correct_index"],
            },
        },
    },
    "required": ["grammar", "comprehension"],
}


# ─────────────────────────── Prompt ───────────────────────────
SYSTEM_PROMPT = """You are an experienced SFI/SAS teacher creating short practice exercises for an \
adult Persian-speaking (Farsi) learner of Swedish, based on a lesson dialogue they just studied.

Create EXACTLY {grammar_count} grammar questions and EXACTLY {comp_count} reading-comprehension \
questions as structured data. No markdown, no extra commentary.

GRAMMAR QUESTIONS test the lesson's grammar focus: "{rule_name}". Each question is a Swedish \
sentence — from the dialogue or a brand-new one using the same grammar rule — with exactly one \
blank written as "___". Give 4 Swedish options to fill the blank: exactly one is grammatically \
correct, the other three are plausible near-misses (wrong tense/form/word order) a Persian \
speaker would realistically pick. correct_index is the 0-based index of the right option. \
explanation_fa is one short Persian sentence explaining why that option is correct, written for \
the learner (mention the mistake Persian speakers typically make, if relevant).

READING-COMPREHENSION QUESTIONS test whether the learner understood the dialogue below — ask \
about concrete facts or events stated in it (who said/did what, in what order, why). Write both \
question_fa and all 4 options ENTIRELY in Persian, so understanding is tested, not Swedish \
reading. Exactly one option is correct; the other three are plausible but wrong.

Do not reuse the exact example sentences already given as grammar examples — write new sentences."""

USER_PROMPT = """Lesson dialogue (Swedish):
{audio_script}

Grammar focus: {rule_name}
Grammar explanation (context, for you only — do not translate it into the output): {explanation_fa}

Return ONLY the structured exercise object."""


def build_exercise_prompts(lesson: Lesson) -> tuple[str, str]:
    g = lesson.grammar_focus
    system = SYSTEM_PROMPT.format(grammar_count=GRAMMAR_COUNT, comp_count=COMPREHENSION_COUNT,
                                  rule_name=g.rule_name)
    user = USER_PROMPT.format(audio_script=lesson.audio_script, rule_name=g.rule_name,
                              explanation_fa=g.explanation_fa)
    return system, user


# ─────────────────────────── Providers ───────────────────────────
def _call_claude(system: str, user: str, settings: Settings) -> dict:
    body = {
        "model": settings.llm_model,
        "max_tokens": 4000,
        "system": system,
        "messages": [{"role": "user", "content": user}],
        "tools": [{
            "name": "save_exercises",
            "description": "Save the generated grammar and reading-comprehension exercises.",
            "input_schema": EXERCISES_JSON_SCHEMA,
        }],
        "tool_choice": {"type": "tool", "name": "save_exercises"},
    }
    resp = request_with_retry(
        "POST", "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": settings.llm_api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json=body,
    ).json()
    if resp.get("stop_reason") == "max_tokens":
        raise APIError("Claude hit max_tokens — exercises output truncated")
    for block in resp.get("content", []):
        if block.get("type") == "tool_use" and block.get("name") == "save_exercises":
            return block["input"]
    raise APIError(f"Claude returned no tool_use block: {str(resp)[:300]}")


def _call_gemini(system: str, user: str, settings: Settings) -> dict:
    schema = _strip_keys(EXERCISES_JSON_SCHEMA, {"additionalProperties"})
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4096,
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
    schema = _strip_keys(EXERCISES_JSON_SCHEMA, {"minItems", "maxItems"})
    body = {
        "model": settings.llm_model,
        "temperature": 0.7,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": "exercises", "strict": True, "schema": schema}},
    }
    resp = request_with_retry(
        "POST", "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.llm_api_key}"}, json=body,
    ).json()
    choice = resp["choices"][0]
    if choice.get("finish_reason") == "length":
        raise APIError("OpenAI output truncated (finish_reason=length)")
    return _parse_json_text(choice["message"]["content"])


PROVIDERS = {"claude": _call_claude, "gemini": _call_gemini, "openai": _call_openai}


# ─────────────────────────── واژگان (محلی، بدون LLM) ───────────────────────────
def build_vocab_quiz(vocabulary: list[VocabItem]) -> list[VocabQuestion]:
    """از همون ترجمه‌های موجودِ واژه‌های درس، یه آزمونِ تطبیقِ کلمه-معنیِ چهارگزینه‌ای
    می‌سازه — بدون نیاز به تماس جدید با LLM (معنی‌ها رو خودِ تولیدِ درس قبلاً داده)."""
    translations = [v.translation_fa for v in vocabulary]
    questions: list[VocabQuestion] = []
    for v in vocabulary:
        others = [t for t in translations if t != v.translation_fa]
        distractors = random.sample(others, k=min(3, len(others)))
        options = distractors + [v.translation_fa]
        random.shuffle(options)
        questions.append(VocabQuestion(
            word_sv=v.word, options=options, correct_index=options.index(v.translation_fa),
        ))
    return questions


# ─────────────────────────── Public API ───────────────────────────
def generate_exercises(lesson: Lesson, settings: Settings, max_attempts: int = 4) -> ExerciseSet:
    """Generate and validate grammar + comprehension questions; build vocab quiz locally."""
    if settings.llm_provider not in PROVIDERS:
        raise ValueError(f"Unknown LLM_PROVIDER '{settings.llm_provider}'. Use: {', '.join(PROVIDERS)}")
    if not settings.llm_api_key:
        raise ValueError("LLM_API_KEY is not set")

    call = PROVIDERS[settings.llm_provider]
    system, user = build_exercise_prompts(lesson)
    feedback = ""
    last_problem = ""

    for attempt in range(1, max_attempts + 1):
        log.info("Generating exercises for lesson %d (attempt %d)", lesson.lesson_id, attempt)
        raw = call(system, user + feedback, settings)
        try:
            grammar = [GrammarQuestion.model_validate(g) for g in raw.get("grammar", [])]
            comprehension = [ComprehensionQuestion.model_validate(c) for c in raw.get("comprehension", [])]
            if not grammar or not comprehension:
                raise ValueError("empty grammar or comprehension list")
            for g in grammar:
                if len(g.options) != 4 or not (0 <= g.correct_index <= 3):
                    raise ValueError(f"bad grammar options/correct_index: {g}")
            for c in comprehension:
                if len(c.options) != 4 or not (0 <= c.correct_index <= 3):
                    raise ValueError(f"bad comprehension options/correct_index: {c}")
        except (ValidationError, ValueError) as exc:
            last_problem = str(exc)[:300]
        else:
            exercise_set = ExerciseSet(
                lesson_id=lesson.lesson_id, grammar=grammar, comprehension=comprehension,
                vocab=build_vocab_quiz(lesson.vocabulary),
            )
            log.info("Exercises OK: %d grammar, %d comprehension, %d vocab", len(exercise_set.grammar),
                     len(exercise_set.comprehension), len(exercise_set.vocab))
            return exercise_set
        log.warning("Attempt %d rejected: %s", attempt, last_problem)
        feedback = f"\n\nIMPORTANT — your previous answer was rejected: {last_problem}. Fix this."

    raise RuntimeError(f"Could not generate valid exercises after {max_attempts} attempts: {last_problem}")
