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
    question_sv: str = Field(min_length=3)
    options: list[str] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    explanation_fa: str = Field(min_length=3)


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
                    "question_sv": {"type": "string"},
                    "options": {"type": "array", "minItems": 4, "maxItems": 4, "items": {"type": "string"}},
                    "correct_index": {"type": "integer"},
                    "explanation_fa": {"type": "string"},
                },
                "required": ["question_sv", "options", "correct_index", "explanation_fa"],
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
about concrete facts or events stated in it (who said/did what, in what order, why). Write the \
question (question_sv) and all 4 options in simple, clear Swedish (CEFR A2-B1: short sentences, \
common words, no idioms), like a real SFI listening/reading test. Exactly one option is correct; \
the other three are plausible but clearly wrong according to the dialogue. explanation_fa is one \
short Persian sentence saying why the correct option is right (quote the Swedish phrase from the \
dialogue if useful).

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
def _call_claude(system: str, user: str, settings: Settings, schema: dict | None = None,
                 tool_name: str = "save_exercises") -> dict:
    schema = schema or EXERCISES_JSON_SCHEMA
    body = {
        "model": settings.llm_model,
        "max_tokens": 4000,
        "system": system,
        "messages": [{"role": "user", "content": user}],
        "tools": [{
            "name": tool_name,
            "description": "Save the structured result.",
            "input_schema": schema,
        }],
        "tool_choice": {"type": "tool", "name": tool_name},
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
        if block.get("type") == "tool_use" and block.get("name") == tool_name:
            return block["input"]
    raise APIError(f"Claude returned no tool_use block: {str(resp)[:300]}")


def _call_gemini(system: str, user: str, settings: Settings, schema: dict | None = None,
                 tool_name: str = "save_exercises") -> dict:
    schema = _strip_keys(schema or EXERCISES_JSON_SCHEMA, {"additionalProperties"})
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


def _call_openai(system: str, user: str, settings: Settings, schema: dict | None = None,
                 tool_name: str = "save_exercises") -> dict:
    schema = _strip_keys(schema or EXERCISES_JSON_SCHEMA, {"minItems", "maxItems"})
    body = {
        "model": settings.llm_model,
        "temperature": 0.7,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": tool_name, "strict": True, "schema": schema}},
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


# ─────────────────────────── بازبینی خودکار ───────────────────────────
MIN_GRAMMAR_KEPT = 3
MIN_COMP_KEPT = 2

REVIEW_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "answers": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "integer"},
                    "correct_indexes": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["id", "correct_indexes"],
            },
        },
    },
    "required": ["answers"],
}

REVIEW_SYSTEM = """You are a strict Swedish language examiner checking a quiz written by someone else. \
For every numbered question, decide which options are FULLY CORRECT. For grammar questions: an option \
is correct if the completed sentence is natural, grammatical Swedish (check verb form, word order, \
agreement, imperative vs infinitive vs present, etc.). For comprehension questions: an option is correct \
only if it is stated in or clearly follows from the dialogue. Return, for each question id, the list of \
0-based indexes of ALL correct options (usually exactly one; return an empty list if none is correct). \
Do not guess what the quiz author intended — judge each option on its own."""


def _review_prompt(lesson: Lesson, grammar: list, comprehension: list) -> str:
    lines = [f"Dialogue:\n{lesson.audio_script}\n", "Questions:"]
    for i, g in enumerate(grammar):
        opts = " | ".join(f"{j}: {o}" for j, o in enumerate(g.options))
        lines.append(f"[G{i}] (grammar) {g.sentence_sv}\n   {opts}")
    for i, c in enumerate(comprehension):
        opts = " | ".join(f"{j}: {o}" for j, o in enumerate(c.options))
        lines.append(f"[C{i}] (comprehension) {c.question_sv}\n   {opts}")
    lines.append("\nUse the ids exactly as shown, but as integers: G0..Gn → 0..n; C0..Cm → 100..100+m.")
    return "\n".join(lines)


def review_exercises(lesson: Lesson, grammar: list, comprehension: list, settings: Settings):
    """Blind second pass: an independent solve of every question. Keeps only questions where the
    reviewer's correct set is exactly {correct_index}. Returns (grammar, comprehension, dropped)."""
    call = PROVIDERS[settings.llm_provider]
    raw = call(REVIEW_SYSTEM, _review_prompt(lesson, grammar, comprehension), settings,
               schema=REVIEW_SCHEMA, tool_name="review_answers")
    answers = {int(a["id"]): sorted(set(a.get("correct_indexes", []))) for a in raw.get("answers", [])}
    dropped = []
    g_ok = []
    for i, g in enumerate(grammar):
        if answers.get(i) == [g.correct_index]:
            g_ok.append(g)
        else:
            dropped.append(f"G{i} '{g.sentence_sv}' (author={g.correct_index}, reviewer={answers.get(i)})")
    c_ok = []
    for i, c in enumerate(comprehension):
        if answers.get(100 + i) == [c.correct_index]:
            c_ok.append(c)
        else:
            dropped.append(f"C{i} '{c.question_sv}' (author={c.correct_index}, reviewer={answers.get(100 + i)})")
    return g_ok, c_ok, dropped


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
            # بازبینی مستقل: سؤال‌هایی که جوابشون با نظر بازبین نمی‌خونه حذف می‌شن
            try:
                g2, c2, dropped = review_exercises(lesson, grammar, comprehension, settings)
            except Exception as rexc:  # noqa: BLE001 — بازبینی best-effort، تمرین‌ها بدونش هم ذخیره می‌شن
                log.warning("Exercise review failed (%s) — keeping unreviewed questions", rexc)
            else:
                for d in dropped:
                    log.warning("Review dropped question: %s", d)
                if len(g2) < MIN_GRAMMAR_KEPT or len(c2) < MIN_COMP_KEPT:
                    raise ValueError(f"review rejected too many questions ({len(dropped)} dropped): "
                                     + "; ".join(dropped)[:250])
                grammar, comprehension = g2, c2
                log.info("Review OK: %d dropped, kept %d grammar + %d comprehension",
                         len(dropped), len(grammar), len(comprehension))
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
