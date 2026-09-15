from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv

from backend.config import Settings
from backend.providers.qwen_llm import BailianLLMProvider
from backend.providers.qwen_tts import BailianTTSProvider


async def main() -> int:
    parser = argparse.ArgumentParser(description="Run a real Bailian LLM/TTS smoke test.")
    parser.add_argument("--text", default="你好，这是微光的百炼语音接入测试。")
    parser.add_argument("--voice", default=None)
    parser.add_argument("--tts-only", action="store_true")
    args = parser.parse_args()

    load_dotenv()
    settings = Settings.from_env()
    missing = settings.missing()
    if missing:
        print(f"配置不完整：{', '.join(missing)}", file=sys.stderr)
        return 2

    if not args.tts_only:
        answer = await BailianLLMProvider(settings).complete([
            {"role": "system", "content": "你是微光语音助手，请用一句话回答。"},
            {"role": "user", "content": args.text},
        ], scenario="chat")
        print(f"LLM: {answer}")
        tts_text = answer
    else:
        tts_text = args.text

    try:
        result = await BailianTTSProvider(settings).synthesize(tts_text, voice=args.voice)
    except Exception as exc:
        print(f"TTS failed: {exc}", file=sys.stderr)
        return 1
    print(f"TTS model: {result['model']}")
    print(f"audio_url: {result['audio_url'] or '(response did not contain an audio URL)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
