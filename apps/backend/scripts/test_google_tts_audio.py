import logging
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv

    dotenv_path = project_root / '.env'
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path)
except ImportError:
    pass

from app.services.google_tts_service import google_tts_service
from app.services.voice_style import normalize_voice_style
from app.services.language_utils import DEFAULT_LANGUAGE_CODE


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("--- Starting Google Cloud TTS connectivity test ---")

    test_text = "你好，TaleWeave！这是一次 Google TTS 连通性测试。"
    tale_id = "google-tts-test"
    voice_style = normalize_voice_style("female")
    target_language = DEFAULT_LANGUAGE_CODE

    try:
        audio_url = google_tts_service.generate_single_audio_clip(
            text=test_text,
            tale_id=tale_id,
            file_name="connectivity_test",
            voice_style=voice_style,
            target_language=target_language,
        )
        logger.info("Audio uploaded to: %s", audio_url)
        logger.info("--- TEST SUCCEEDED ---")
    except Exception:
        logger.exception("--- TEST FAILED ---")


if __name__ == "__main__":
    main()
