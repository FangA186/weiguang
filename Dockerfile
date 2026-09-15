# Build the SPA once; the API image serves the immutable dist directory.
FROM node:22-alpine AS frontend-build
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# The story-card component imports these two curated assets from the repository root.
COPY marketing_assets/2026-08-24/04-lifestyle-v2.png /src/marketing_assets/2026-08-24/04-lifestyle-v2.png
COPY marketing_assets/2026-09-08/holo-card-experiment/weiguang-subject-transparent.png /src/marketing_assets/2026-09-08/holo-card-experiment/weiguang-subject-transparent.png
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
ARG DEEP_FILTER_URL=https://github.com/Rikorose/DeepFilterNet/releases/download/v0.5.6/deep-filter-0.5.6-x86_64-unknown-linux-musl
ARG DEEP_FILTER_SHA256=70775e251eee44c0f2451a1e833326cf8bcbbe304d3e7cd12851e6fce72ef7da
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WEB_DIR=/app/frontend/dist \
    APP_ENV=production \
    COOKIE_SECURE=true

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "import hashlib,pathlib,urllib.request; data=urllib.request.urlopen('$DEEP_FILTER_URL', timeout=60).read(); assert hashlib.sha256(data).hexdigest() == '$DEEP_FILTER_SHA256'; path=pathlib.Path('/usr/local/bin/deep-filter'); path.write_bytes(data); path.chmod(0o755)"
RUN python -c "import hashlib,pathlib,urllib.request; root=pathlib.Path('/usr/share/licenses/deepfilternet'); root.mkdir(parents=True); items=[('LICENSE-MIT','https://raw.githubusercontent.com/Rikorose/DeepFilterNet/v0.5.6/LICENSE-MIT','24e6bb09c928af8d8e56268082f87413247ce36b39dd5d33add2f9893968065e'),('LICENSE-APACHE','https://raw.githubusercontent.com/Rikorose/DeepFilterNet/v0.5.6/LICENSE-APACHE','1eaee808c5fb6b4e895ba30425285a5cdc5dd25bba2cd230f264c2200c331aec')]; [(lambda data,name,expected: (hashlib.sha256(data).hexdigest() == expected or (_ for _ in ()).throw(AssertionError(name)), (root/name).write_bytes(data)))(urllib.request.urlopen(url, timeout=30).read(),name,expected) for name,url,expected in items]"
COPY backend/ ./backend/
COPY internal/ ./internal/
COPY --from=frontend-build /src/frontend/dist ./frontend/dist/

EXPOSE 8080
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips=*"]
