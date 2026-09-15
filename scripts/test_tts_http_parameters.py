"""Validate outgoing HTTP/SSE JSON against the official input parameter schema. No network."""
import asyncio
import base64
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.providers.qwen_tts import BailianTTSProvider


async def main():
    requests = []
    def respond(request):
        body = json.loads(request.content)
        requests.append(body)
        assert "instruction" not in body
        if body['model'] != 'cosyvoice-v3.5-plus':
            assert body["input"]["instruction"] == "平静自然"
        if body['model'] != 'cosyvoice-v3.5-plus':
            assert body["input"]["rate"] == 0.85
            assert body["input"]["sample_rate"] == 48000
        if body['model'] == 'cosyvoice-v3.5-plus':
            assert body['input']['text'] == '你好'
            if 'rate' in body['input']:
                assert set(body['input']) == {'text', 'voice', 'format', 'rate', 'volume', 'pitch', 'instruction'}
                assert body['input']['rate'] == .85 and body['input']['volume'] == 0
                assert body['input']['pitch'] == 1.2
                assert sum(1 if c.isascii() else 2 for c in body['input']['instruction']) <= 100
            else:
                assert set(body['input']) == {'text', 'voice', 'format'}
        payload = {"output": {"type": "sentence-synthesis", "audio": {"data": base64.b64encode(bytes(960)).decode()}}}
        if request.headers.get("X-DashScope-SSE"):
            return httpx.Response(200, text="data: " + json.dumps(payload) + "\n\n")
        return httpx.Response(200, json=payload)
    real_client = httpx.AsyncClient
    settings = SimpleNamespace(tts_model="qwen-audio-3.0-tts-flash", tts_voice="test-voice", api_key="test-key", tts_url="https://example.invalid/tts", request_timeout_seconds=10)
    with patch("backend.providers.qwen_tts.httpx.AsyncClient", side_effect=lambda **kwargs: real_client(transport=httpx.MockTransport(respond), **kwargs)):
        provider = BailianTTSProvider(settings)
        result = await provider.synthesize("你好", instruction="平静自然", rate=0.85, sample_rate=48000, audio_format="pcm")
        assert result["audio_duration_seconds"] == 0.01
        chunks = [chunk async for chunk in provider.stream_synthesize("你好", instruction="平静自然", rate=0.85, sample_rate=48000)]
        assert chunks[0]["audio_duration_seconds"] == 0.01
        await provider.synthesize('[sad]你好[sighing]', model='cosyvoice-v3.5-plus', instruction='温柔'*100, rate=.85, volume=0, pitch=1.2, sample_rate=48000)
        cosy = [chunk async for chunk in provider.stream_synthesize('[sad]你好', model='cosyvoice-v3.5-plus', instruction='平静自然', rate=.85, volume=0, pitch=1.2, sample_rate=48000)]
        assert cosy[0]['audio_data']
        assert cosy[0]['audio_duration_seconds'] == 960 / (22050 * 2)
        await provider.synthesize('你好',model='cosyvoice-v3.5-plus',use_defaults=True,instruction='温柔',rate=.7,volume=70,pitch=1.4)
        raw = [chunk async for chunk in provider.stream_synthesize('你好',model='cosyvoice-v3.5-plus',use_defaults=True,instruction='温柔',rate=.7,volume=70,pitch=1.4)]
        assert raw[0]['audio_data']
    assert len(requests) == 6
    print("PASS HTTP and SSE input.instruction/rate/sample_rate, 48 kHz duration")


if __name__ == "__main__":
    asyncio.run(main())
