from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.providers.qwen_llm import BailianLLMProvider, LLM_OUTPUT_TOKEN_LIMITS


class FakeCompletions:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("stream"):
            async def events():
                yield SimpleNamespace(
                    id="stream-id",
                    choices=[SimpleNamespace(delta=SimpleNamespace(content="好"))],
                    usage=None,
                )
            return events()
        return SimpleNamespace(
            id="complete-id",
            model="qwen3.5-flash",
            choices=[SimpleNamespace(message=SimpleNamespace(content="好"))],
            usage=None,
        )


async def main() -> None:
    assert LLM_OUTPUT_TOKEN_LIMITS == {
        "chat": 512,
        "voice": 1024,
        "correction": 1024,
        "ocr": 4096,
        "persona": 8192,
    }
    completions = FakeCompletions()
    provider = object.__new__(BailianLLMProvider)
    provider.model = "qwen3.5-flash"
    provider.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

    history = [{"role": "assistant", "content": "旧消息" * 4000} for _ in range(8)]
    result = await provider.complete_with_usage([
        {"role": "system", "content": "你是微光。"},
        *history,
        {"role": "user", "content": "你好"},
    ], scenario="chat")
    events = [event async for event in provider.stream_events(
        [{"role": "user", "content": "你好"}], scenario="voice"
    )]
    assert events
    assert len(completions.calls) == 2
    assert all(call["extra_body"] == {"enable_thinking": False} for call in completions.calls)
    assert completions.calls[0]["max_completion_tokens"] == 512
    assert completions.calls[1]["max_completion_tokens"] == 1024
    assert result["context_trimmed_messages"] > 0
    assert result["input_bytes"] <= 96 * 1024
    assert len(completions.calls[0]["messages"]) < len(history) + 2
    try:
        await provider.complete_with_usage([{"role": "system", "content": "x" * (24 * 1024 + 1)}, {"role": "user", "content": "你好"}], scenario="chat")
    except ValueError:
        pass
    else:
        raise AssertionError("oversized system prompt was accepted")
    try:
        await provider.complete_with_usage([{"role": "user", "content": "长" * 2001}], scenario="chat")
    except ValueError:
        pass
    else:
        raise AssertionError("oversized user message was accepted")
    print("qwen LLM scenario limits and context trimming: OK")


if __name__ == "__main__":
    asyncio.run(main())
