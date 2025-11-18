from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Iterable

from langdetect import DetectorFactory, LangDetectException, detect


DetectorFactory.seed = 42


@dataclass(frozen=True)
class LanguageSpec:
    code: str
    native_name: str
    english_name: str


SUPPORTED_LANGUAGES: Final[dict[str, LanguageSpec]] = {
    "zh": LanguageSpec(code="zh", native_name="中文", english_name="Chinese"),
    "en": LanguageSpec(code="en", native_name="英文", english_name="English"),
}

DEFAULT_LANGUAGE_CODE: Final[str] = "zh"


def normalize_language_code(raw: str | None) -> str | None:
    if not raw:
        return None
    normalized = raw.strip().lower()
    if not normalized:
        return None
    if "_" in normalized:
        normalized = normalized.replace("_", "-")
    if "-" in normalized:
        normalized = normalized.split("-", 1)[0]
    return normalized


def detect_language_from_text(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = text.strip()
    if not cleaned:
        return None
    try:
        detected = detect(cleaned)
    except LangDetectException:
        return None
    return normalize_language_code(detected)


def parse_accept_language(header_value: str | None) -> str | None:
    if not header_value:
        return None
    items = []
    for part in header_value.split(','):
        token = part.strip()
        if not token:
            continue
        segments = token.split(';')
        lang = segments[0].strip()
        q = 1.0
        if len(segments) > 1:
            for seg in segments[1:]:
                seg = seg.strip()
                if seg.startswith('q='):
                    try:
                        q = float(seg[2:])
                    except ValueError:
                        q = 0.0
        items.append((normalize_language_code(lang), q))
    if not items:
        return None
    items.sort(key=lambda item: item[1], reverse=True)
    for code, _ in items:
        if code in SUPPORTED_LANGUAGES:
            return code
    return None


def resolve_target_language(
    preferred_language: str | None,
    *,
    texts: Iterable[str | None] = (),
    accept_language: str | None = None,
) -> str:
    candidates: list[str | None] = [preferred_language]
    candidates.extend(detect_language_from_text(text) for text in texts)
    candidates.append(parse_accept_language(accept_language))

    for candidate in candidates:
        normalized = normalize_language_code(candidate)
        if normalized and normalized in SUPPORTED_LANGUAGES:
            return normalized

    return DEFAULT_LANGUAGE_CODE


def get_language_spec(code: str | None) -> LanguageSpec:
    normalized = normalize_language_code(code) or DEFAULT_LANGUAGE_CODE
    return SUPPORTED_LANGUAGES.get(normalized, SUPPORTED_LANGUAGES[DEFAULT_LANGUAGE_CODE])
