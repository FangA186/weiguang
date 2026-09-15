#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import math
import struct
import sys
import tempfile
import wave
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.audio_denoiser import denoise_audio
from fastapi import HTTPException


def executable(path: Path, source: str) -> str:
    path.write_text(source)
    path.chmod(0o755)
    return str(path)


async def check() -> None:
    with tempfile.TemporaryDirectory(prefix="weiguang-denoise-test-") as temp:
        root = Path(temp)
        source = root / "source.wav"
        with wave.open(str(source), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(48000)
            wav.writeframes(b"".join(struct.pack("<h", int(math.sin(i / 20) * 8000)) for i in range(4800)))
        deep_filter = executable(
            root / "deep-filter",
            "#!/bin/sh\nout=\nwhile [ $# -gt 0 ]; do [ \"$1\" = -o ] && { shift; out=$1; }; input=$1; shift; done\ncp \"$input\" \"$out/$(basename \"$input\")\"\n",
        )
        cleaned, duration = await denoise_audio(
            source.read_bytes(),
            source_suffix=".wav",
            deep_filter_binary=deep_filter,
        )
        assert cleaned.startswith(b"RIFF")
        assert 0.09 <= duration <= 0.11
        try:
            await denoise_audio(b"", source_suffix=".wav", deep_filter_binary=deep_filter)
        except ValueError:
            pass
        else:
            raise AssertionError("empty audio must be rejected")


async def check_endpoint() -> None:
    from backend import app as service

    uploaded: list[tuple[str, bytes]] = []

    class FakeOSS:
        def __init__(self, _settings: object) -> None:
            pass

        def download_object(self, object_key: str, *, max_bytes: int) -> bytes:
            assert object_key == "voice-references/user-a/source.wav"
            assert max_bytes == 10 * 1024 * 1024
            return b"source"

        def upload_object(self, object_key: str, data: bytes, *, content_type: str) -> None:
            assert object_key.startswith("voice-references/user-a/denoised/")
            assert content_type == "audio/wav"
            uploaded.append((object_key, data))

        def presign_object_download(self, object_key: str) -> str:
            return f"https://example.invalid/{object_key}"

    async def fake_denoise(source: bytes, *, source_suffix: str) -> tuple[bytes, float]:
        assert source == b"source" and source_suffix == ".wav"
        return b"RIFFclean", 1.25

    original_oss = service.OSSProvider
    original_denoise = service.denoise_audio
    original_rate_limiter = service.rate_limiter
    service.OSSProvider = FakeOSS
    service.denoise_audio = fake_denoise
    service.rate_limiter = None
    request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))
    try:
        result = await service.denoise_voice_upload(
            service.VoiceDenoiseRequest(object_key="voice-references/user-a/source.wav"),
            request,
            user_id="user-a",
        )
        assert result["engine"] == "DeepFilterNet" and result["duration"] == 1.25
        assert uploaded and uploaded[0][1] == b"RIFFclean"
        try:
            await service.denoise_voice_upload(
                service.VoiceDenoiseRequest(object_key="voice-references/user-b/source.wav"),
                request,
                user_id="user-a",
            )
        except HTTPException as exc:
            assert exc.status_code == 403
        else:
            raise AssertionError("cross-account audio must be rejected")
    finally:
        service.OSSProvider = original_oss
        service.denoise_audio = original_denoise
        service.rate_limiter = original_rate_limiter


if __name__ == "__main__":
    asyncio.run(check())
    asyncio.run(check_endpoint())
    print("audio denoiser checks passed")
