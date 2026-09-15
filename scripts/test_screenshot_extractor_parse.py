"""Regression checks for tolerant Qwen screenshot JSON parsing."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.providers.screenshot_extractor import ScreenshotExtractor


def parse(payload: dict):
    extractor = object.__new__(ScreenshotExtractor)
    return extractor._parse_json_response(json.dumps(payload, ensure_ascii=False))


def main() -> None:
    result = parse(
        {
            "messages": [
                {"speaker": "对方", "role_guess": "other", "text": "你好"},
                {"speaker": None, "role_guess": None, "text": None, "media_kind": "image"},
                {"speaker": "我", "role_guess": "user", "text": "再见"},
            ],
            "warnings": [],
        }
    )
    assert len(result.messages) == 3
    assert result.messages[1].speaker == "对方"
    assert result.messages[1].text == "[图片]"
    assert result.messages[1].role_guess == "unknown"
    assert result.messages[1].needs_review is True
    assert result.messages[1].confidence == 0.5
    print("screenshot extractor nullable-field regression: PASS")


if __name__ == "__main__":
    main()
