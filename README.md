<<<<<<< HEAD
# AI Job Fit Analyzer API

FastAPI backend for normalizing job descriptions and analyzing candidate CV fit using Gemini or OpenAI structured JSON outputs.
=======
# CV Fit Analyst Agent API

FastAPI backend for normalizing job descriptions and analyzing candidate CV fit using Gemini structured outputs.
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144

## Features

- Public web UI for non-technical users.
- Normalize JD text or a public job URL into structured fields.
- Analyze CV-to-JD fit with score, recommendation, evidence, gaps, CV rewrite suggestions, and interview questions.
<<<<<<< HEAD
- Search and rank jobs from multiple public job boards: TopCV, JobOKO, VietnamWorks, Glints, and ITviec.
=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
- Extract text from `.txt`, `.pdf`, and `.docx` uploads.
- Optional public demo mode with per-IP daily quota.
- API key protection with `X-API-Key`.
- Basic in-memory rate limiting.
- Docker and Render deployment config.
<<<<<<< HEAD
- Optional Playwright Chromium crawler for Render/container deployments where local Edge is unavailable.
=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
```

Edit `.env` and set:

```bash
<<<<<<< HEAD
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.5-flash
GEMINI_RESPONSE_SCHEMA_ENABLED=false
=======
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.5-flash
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
APP_API_KEY=your-client-api-key
PUBLIC_DEMO_ENABLED=false
PUBLIC_DEMO_DAILY_LIMIT=10
DEMO_MAX_INPUT_CHARS=12000
<<<<<<< HEAD
LOCAL_ANALYSIS_FALLBACK_ENABLED=true
JOB_BROWSER_CRAWLER_ENABLED=false
JOB_BROWSER_TIMEOUT_SECONDS=18
=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
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

<<<<<<< HEAD
Use `LLM_PROVIDER=gemini` with `GEMINI_API_KEY` for Google Gemini, or `LLM_PROVIDER=openai` with `OPENAI_API_KEY` for OpenAI. `GEMINI_RESPONSE_SCHEMA_ENABLED=false` keeps Gemini faster by validating JSON with Pydantic after generation instead of forcing strict schema decoding at the API layer. For production, keep `LOCAL_ANALYSIS_FALLBACK_ENABLED=false` so users see a real service error instead of a rough local estimate when the LLM is unavailable.

=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
Public demo endpoints:

- `POST /api/v1/demo/files/extract`
- `POST /api/v1/demo/analyze/full`
<<<<<<< HEAD
- `POST /api/v1/demo/jobs/search`
- `POST /api/v1/demo/jobs/recommend`

Private API endpoints still support `X-API-Key`. On a public Render deploy, set `APP_API_KEY` so private endpoints cannot bypass the public demo quota.
=======

Private API endpoints still support `X-API-Key`. If the web app user enters an access code, the browser calls the private endpoints instead of the public demo endpoints.
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144

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

<<<<<<< HEAD
### Search Jobs Across Sources

```bash
curl -X POST http://localhost:8000/api/v1/jobs/search ^
  -H "Content-Type: application/json" ^
  -H "X-API-Key: your-client-api-key" ^
  -d "{\"keyword\":\"python backend\",\"sources\":[\"topcv\",\"joboko\",\"vietnamworks\",\"glints\",\"itviec\"],\"cv_text\":\"Paste CV here\",\"analyze_results\":true}"
```

Use `POST /api/v1/jobs/recommend` with `cv_text` and `sources` when you want the API to derive search keywords from the CV.

=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
## Deploy To Render

For step-by-step local, Render, and Hugging Face Spaces instructions, see [`DEPLOYMENT.md`](DEPLOYMENT.md).

1. Push this repository to GitHub.
2. In Render, create a new Web Service from the repo.
3. Select Docker runtime, or use the included `render.yaml` blueprint.
4. Set environment variables:
<<<<<<< HEAD
   - `LLM_PROVIDER=gemini`
   - `GEMINI_API_KEY`
   - `GEMINI_MODEL=gemini-3.5-flash`
   - `APP_API_KEY`
=======
   - `GEMINI_API_KEY`
   - `APP_API_KEY`
   - `GEMINI_MODEL`
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
   - `ALLOWED_ORIGINS`
   - `PUBLIC_DEMO_ENABLED`
   - `PUBLIC_DEMO_DAILY_LIMIT`
   - `DEMO_MAX_INPUT_CHARS`
<<<<<<< HEAD
   - `LOCAL_ANALYSIS_FALLBACK_ENABLED=false`
   - `JOB_BROWSER_CRAWLER_ENABLED=true`
   - `TOPCV_ENABLE_EDGE_CRAWLER=false`
=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
5. Set health check path to `/health`.

The Dockerfile starts the app with:

```bash
<<<<<<< HEAD
python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
```

For a public beta, the included `render.yaml` enables public demo mode with a small daily quota. Keep this quota low until you know your LLM cost per analysis.
=======
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
```

For a public beta, the included `render.yaml` enables public demo mode with a small daily quota. Keep this quota low because Gemini free tier still has rate limits.
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144

## Free Deployment Options

Recommended MVP path:

- Render Free Web Service: simplest for this repo because Docker and `render.yaml` are already included. Free services can spin down after inactivity, so the first request after idle can be slow.
- Hugging Face Spaces with Docker: good for public AI demos and can run FastAPI in a Docker Space, but the app must listen on the Space port and should not rely on local disk persistence.

<<<<<<< HEAD
Hosting can be free, but OpenAI API usage is not free unless your OpenAI account has trial credits. Use public demo quotas, rate limits, and monitoring before sharing widely.
=======
Hosting can be free, and Gemini API has a free tier for developers and small projects, but free usage still has model access and rate-limit constraints. Use public demo quotas, rate limits, and monitoring before sharing widely.

If you see a Gemini quota/rate-limit error, check the Gemini API key, free tier limits, and billing/quota settings for the project that owns `GEMINI_API_KEY`; Render cannot solve that part. See [`DEPLOYMENT.md`](DEPLOYMENT.md) for the checklist.
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144

## Notes

- Some job sites block scraping. If URL extraction returns incomplete content, ask the user to paste the JD manually.
<<<<<<< HEAD
- Multi-source job search tries public HTML first. On Render, `JOB_BROWSER_CRAWLER_ENABLED=true` lets the Docker container use headless Chromium for JavaScript-rendered pages. If a source still returns login, CAPTCHA, or anti-bot checks, the API keeps the request successful and returns source-specific warnings instead of bypassing those controls.
=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
- Image OCR is not included in v1. Users can paste OCR text into `job_description` with `source_type` set to `image_ocr`.
- Do not log raw CV/JD text in production because it can contain personal data.
