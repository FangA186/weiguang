from __future__ import annotations

import argparse
import sys
from urllib.parse import urlsplit
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.config import Settings
from backend.providers.oss import OSSProvider


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an OSS signed audio upload URL without printing credentials")
    parser.add_argument("--filename", default="sample.wav")
    parser.add_argument("--content-type", default="audio/wav")
    args = parser.parse_args()

    result = OSSProvider(Settings.from_env()).presign_audio_upload(
        filename=args.filename,
        content_type=args.content_type,
    )
    host = urlsplit(str(result["upload_url"])).netloc
    print(f"OSS presign: ok bucket={result['bucket']} object={result['object_key']} host={host}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
