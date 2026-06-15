# CV Fit Analyst Agent API

FastAPI backend for normalizing job descriptions and analyzing candidate CV fit using Gemini structured outputs.

## Features

- Public web UI for non-technical users.
- Normalize JD text or a public job URL into structured fields.
- Analyze CV-to-JD fit with score, recommendation, evidence, gaps, CV rewrite suggestions, and interview questions.
- Extract text from `.txt`, `.pdf`, and `.docx` uploads.
- Optional public demo mode with per-IP daily quota.
- API key protection with `X-API-Key`.
- Basic in-memory rate limiting.
- Docker and Render deployment config.

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
```

Edit `.env` and set:

```bash
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.5-flash
APP_API_KEY=your-client-api-key
PUBLIC_DEMO_ENABLED=false
PUBLIC_DEMO_DAILY_LIMIT=10
DEMO_MAX_INPUT_CHARS=12000
```

Run the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

- Web app: `http://localhost:8000/`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## Public Web Demo

The root route `/` serves a lightweight web app for end users. It supports:

- Paste CV text or upload `.txt`, `.pdf`, `.docx`.
- Paste JD text or provide a public job URL.
- Run one-step analysis.
- Copy a short summary or download the full JSON result.

By default, public demo endpoints are disabled locally. To allow visitors to use the app without entering `X-API-Key`, set:

```bash
PUBLIC_DEMO_ENABLED=true
PUBLIC_DEMO_DAILY_LIMIT=10
DEMO_MAX_INPUT_CHARS=12000
```

Public demo endpoints:

- `POST /api/v1/demo/files/extract`
- `POST /api/v1/demo/analyze/full`

Private API endpoints still support `X-API-Key`. If the web app user enters an access code, the browser calls the private endpoints instead of the public demo endpoints.

## Main Endpoints

### Normalize JD

```bash
curl -X POST http://localhost:8000/api/v1/jd/normalize ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: your-client-api-key" ^
  -d "{\"job_description\":\"Paste JD here\",\"source_type\":\"text\",\"output_language\":\"vi\"}"
```

### Analyze CV Against Normalized JD

```bash
curl -X POST http://localhost:8000/api/v1/analyze ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: your-client-api-key" ^
  -d "{\"cv_text\":\"Paste CV here\",\"normalized_job_description\":{...},\"user_preferences\":\"Remote preferred\",\"output_language\":\"vi\"}"
```

### One-Step Full Analysis

```bash
curl -X POST http://localhost:8000/api/v1/analyze/full ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: your-client-api-key" ^
  -d "{\"cv_text\":\"Paste CV here\",\"job_description\":\"Paste JD here\",\"source_type\":\"text\",\"output_language\":\"vi\"}"
```

### Extract File Text

```bash
curl -X POST http://localhost:8000/api/v1/files/extract ^
  -H "X-API-Key: your-client-api-key" ^
  -F "file=@candidate_cv.pdf"
```

## Deploy To Render

For step-by-step local, Render, and Hugging Face Spaces instructions, see [`DEPLOYMENT.md`](DEPLOYMENT.md).

1. Push this repository to GitHub.
2. In Render, create a new Web Service from the repo.
3. Select Docker runtime, or use the included `render.yaml` blueprint.
4. Set environment variables:
   - `GEMINI_API_KEY`
   - `APP_API_KEY`
   - `GEMINI_MODEL`
   - `ALLOWED_ORIGINS`
   - `PUBLIC_DEMO_ENABLED`
   - `PUBLIC_DEMO_DAILY_LIMIT`
   - `DEMO_MAX_INPUT_CHARS`
5. Set health check path to `/health`.

The Dockerfile starts the app with:

```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
```

For a public beta, the included `render.yaml` enables public demo mode with a small daily quota. Keep this quota low because Gemini free tier still has rate limits.

## Free Deployment Options

Recommended MVP path:

- Render Free Web Service: simplest for this repo because Docker and `render.yaml` are already included. Free services can spin down after inactivity, so the first request after idle can be slow.
- Hugging Face Spaces with Docker: good for public AI demos and can run FastAPI in a Docker Space, but the app must listen on the Space port and should not rely on local disk persistence.

Hosting can be free, and Gemini API has a free tier for developers and small projects, but free usage still has model access and rate-limit constraints. Use public demo quotas, rate limits, and monitoring before sharing widely.

If you see a Gemini quota/rate-limit error, check the Gemini API key, free tier limits, and billing/quota settings for the project that owns `GEMINI_API_KEY`; Render cannot solve that part. See [`DEPLOYMENT.md`](DEPLOYMENT.md) for the checklist.

## Notes

- Some job sites block scraping. If URL extraction returns incomplete content, ask the user to paste the JD manually.
- Image OCR is not included in v1. Users can paste OCR text into `job_description` with `source_type` set to `image_ocr`.
- Do not log raw CV/JD text in production because it can contain personal data.
