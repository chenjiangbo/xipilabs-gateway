from __future__ import annotations

from typing import Final


DEFAULT_VOICE_STYLE: Final[str] = "female"
SUPPORTED_VOICE_STYLES: Final[set[str]] = {"female", "male"}

_ALIASES: Final[dict[str, str]] = {
    "default": DEFAULT_VOICE_STYLE,
    "mom": "female",
    "mother": "female",
    "xiaoyajie": "female",
    "sister": "female",
    "grandma": "female",
    "dad": "male",
    "father": "male",
    "grandpa": "male",
    "dagege": "male",
    "brother": "male",
}


def normalize_voice_style(raw: str | None) -> str:
    """Normalizes legacy voice style IDs to the supported set."""
    if not raw:
        return DEFAULT_VOICE_STYLE

    key = raw.strip().lower()
    if not key:
        return DEFAULT_VOICE_STYLE

    normalized = _ALIASES.get(key, key)
    if normalized not in SUPPORTED_VOICE_STYLES:
        allowed = ", ".join(sorted(SUPPORTED_VOICE_STYLES))
        raise ValueError(f"Unsupported voiceStyle '{raw}'. Allowed values: {allowed}.")

    return normalized
