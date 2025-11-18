from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, Iterable, List

import anyio
from google.cloud import texttospeech

from app.services.storage_client import MinioStorageClient
from app.services.voice_style import normalize_voice_style
from app.services.language_utils import (
    DEFAULT_LANGUAGE_CODE,
    SUPPORTED_LANGUAGES,
    normalize_language_code,
)


logger = logging.getLogger(__name__)


class GoogleTextToSpeechService:
    def __init__(self) -> None:
        self.client = texttospeech.TextToSpeechClient()
        self.storage_client = MinioStorageClient()
        self.voice_overrides = self._load_voice_overrides()

    def _load_voice_overrides(self) -> Dict[tuple[str, str], str]:
        mapping: Dict[tuple[str, str], str] = {}
        for language_code in SUPPORTED_LANGUAGES.keys():
            for style in ("female", "male"):
                env_key = self._env_key(style, language_code)
                voice_name = os.getenv(env_key)
                if voice_name:
                    mapping[(style, language_code)] = voice_name
        return mapping

    def _env_key(self, voice_style: str, language_code: str) -> str:
        return f"GOOGLE_TTS_VOICE_{voice_style.upper()}_{language_code.upper()}"

    def _resolve_voice_name(self, voice_style: str, language_code: str) -> str:
        normalized_style = normalize_voice_style(voice_style)
        normalized_language = normalize_language_code(language_code) or DEFAULT_LANGUAGE_CODE
        key = (normalized_style, normalized_language)
        if key in self.voice_overrides:
            return self.voice_overrides[key]
        env_key = self._env_key(normalized_style, normalized_language)
        raise ValueError(
            f"缺少 {normalized_style}/{normalized_language} 的 Google 语音配置，请在环境变量中设置 {env_key}."
        )

    def _derive_language_code_from_voice(self, voice_name: str) -> str:
        parts = voice_name.split("-")
        if len(parts) < 2:
            raise ValueError(f"无法从语音 {voice_name} 推导语言代码，请使用形如 en-US-Neural2-F 的名称。")
        return "-".join(parts[:2])

    def _synthesize_audio(self, text: str, voice_style: str, target_language: str) -> List[bytes]:
        if not text:
            raise ValueError("缺少可合成的文本内容。")

        voice_name = self._resolve_voice_name(voice_style, target_language)
        language_code = self._derive_language_code_from_voice(voice_name)

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice_params = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
        )

        logger.debug(
            "Synthesizing audio via Google TTS (voice=%s, language=%s)",
            voice_name,
            language_code,
        )
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config,
        )
        return [response.audio_content]

    async def generate_and_upload_audio_for_pages(
        self,
        tale_id: str,
        pages: Iterable[Dict[str, Any]],
        voice_style: str,
        target_language: str,
    ) -> List[Dict[str, Any]]:
        logger.info(
            "Starting Google TTS audio generation for tale %s (%s/%s)",
            tale_id,
            voice_style,
            target_language,
        )

        async def _generate_single(page: Dict[str, Any]) -> Dict[str, Any] | None:
            page_number = page.get("page_number")
            text = page.get("audio_text") or page.get("display_text")
            if not text:
                logger.info("Skipping page %s of tale %s due to missing audio_text.", page_number, tale_id)
                return None

            try:
                audio_chunks = await anyio.to_thread.run_sync(
                    self._synthesize_audio,
                    text,
                    voice_style,
                    target_language,
                )

                file_path = f"stories/{tale_id}/audio_page_{page_number}.mp3"
                audio_url = self.storage_client.upload_audio_stream(audio_chunks, file_path)
                logger.info("Generated Google TTS audio for tale %s page %s", tale_id, page_number)
                return {"page_number": page_number, "audio_url": audio_url}
            except Exception as exc:
                logger.exception("Failed to synthesize audio for tale %s page %s", tale_id, page_number)
                return {"page_number": page_number, "audio_url": None, "error": str(exc)}

        tasks = [_generate_single(page) for page in pages]
        results = await asyncio.gather(*tasks)
        return [result for result in results if result]

    def generate_single_audio_clip(
        self,
        text: str | None,
        tale_id: str,
        file_name: str,
        voice_style: str,
        target_language: str,
    ) -> str | None:
        if not text:
            return None

        audio_chunks = self._synthesize_audio(text, voice_style, target_language)
        file_path = f"stories/{tale_id}/{file_name}_audio.mp3"
        return self.storage_client.upload_audio_stream(audio_chunks, file_path)


google_tts_service = GoogleTextToSpeechService()
