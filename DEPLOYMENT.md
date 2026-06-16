# Deployment Guide

This project can run as one service: FastAPI serves both the web UI and the API.

<<<<<<< HEAD
=======
The model provider is Gemini API through the Google GenAI SDK.

>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
## Option 1: Use It On Your Own Computer

Use this when only you need to test the web interface.

1. Create `.env` from `.env.example`.
2. Set at least:

```bash
<<<<<<< HEAD
OPENAI_API_KEY=sk-your-key
LLM_PROVIDER=auto
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.5-flash
GEMINI_RESPONSE_SCHEMA_ENABLED=false
APP_API_KEY=your-private-access-code
PUBLIC_DEMO_ENABLED=false
LOCAL_ANALYSIS_FALLBACK_ENABLED=true
=======
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.5-flash
APP_API_KEY=your-private-access-code
PUBLIC_DEMO_ENABLED=false
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
```

3. Start the app:

```bash
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

4. Open:

```text
http://127.0.0.1:8000/
```

Because `PUBLIC_DEMO_ENABLED=false`, enter your `APP_API_KEY` in the Access code field before analyzing.
<<<<<<< HEAD
If you leave `OPENAI_API_KEY` empty, local heuristic fallback can still exercise the UI and JD extraction flow.
=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144

## Option 2: Deploy To Render

Use this when you want a public web link like:

```text
https://your-service-name.onrender.com/
```

1. Push this project to GitHub.
2. Open Render and create a new Web Service from the GitHub repo.
3. Choose Docker runtime, or use the included `render.yaml` blueprint.
4. Set environment variables:

```bash
<<<<<<< HEAD
OPENAI_API_KEY=sk-your-key
APP_API_KEY=your-private-access-code
LLM_PROVIDER=auto
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.5-flash
GEMINI_RESPONSE_SCHEMA_ENABLED=false
OPENAI_MODEL=gpt-5.5
PUBLIC_DEMO_ENABLED=true
PUBLIC_DEMO_DAILY_LIMIT=10
DEMO_MAX_INPUT_CHARS=12000
LOCAL_ANALYSIS_FALLBACK_ENABLED=true
JOB_BROWSER_CRAWLER_ENABLED=true
JOB_BROWSER_TIMEOUT_SECONDS=20
TOPCV_ENABLE_EDGE_CRAWLER=false
=======
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.5-flash
APP_API_KEY=your-private-access-code
PUBLIC_DEMO_ENABLED=true
PUBLIC_DEMO_DAILY_LIMIT=10
DEMO_MAX_INPUT_CHARS=12000
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
RATE_LIMIT_PER_MINUTE=30
ALLOWED_ORIGINS=*
```

5. Set health check path:

```text
/health
```

6. After deploy finishes, open the Render URL. The root page `/` is the web UI.

<<<<<<< HEAD
Render free services can sleep after inactivity, so the first visit after idle may take about a minute. Keep `PUBLIC_DEMO_DAILY_LIMIT` low until you know your OpenAI cost per run.

The web UI can search TopCV, JobOKO, VietnamWorks, Glints, and ITviec through public pages. Keep `TOPCV_ENABLE_EDGE_CRAWLER=false` on Render because a hosted container does not have a local desktop Edge browser. Use `JOB_BROWSER_CRAWLER_ENABLED=true` to let the Docker container run headless Chromium for JavaScript-rendered pages. If a job board still blocks server traffic or shows CAPTCHA/login, the API will return a warning for that source and still show results from the sources that responded.
=======
Render free services can sleep after inactivity, so the first visit after idle may take about a minute. Keep `PUBLIC_DEMO_DAILY_LIMIT` low because Gemini free tier has rate limits.
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144

## Option 3: Deploy To Hugging Face Spaces

Use this when you want an AI-demo-style public page. Docker Spaces can run FastAPI.

1. Create a new Hugging Face Space.
2. Select Docker as the SDK.
3. In the Space README YAML, use:

```yaml
---
<<<<<<< HEAD
title: AI Job Fit Analyzer
=======
title: CV Fit Analyst Agent
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
sdk: docker
app_port: 7860
---
```

4. Push this project into the Space repository.
5. In Space Settings, add runtime secrets/variables:

```bash
<<<<<<< HEAD
OPENAI_API_KEY=sk-your-key
APP_API_KEY=your-private-access-code
LLM_PROVIDER=auto
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.5-flash
GEMINI_RESPONSE_SCHEMA_ENABLED=false
OPENAI_MODEL=gpt-5.5
PUBLIC_DEMO_ENABLED=true
PUBLIC_DEMO_DAILY_LIMIT=10
DEMO_MAX_INPUT_CHARS=12000
LOCAL_ANALYSIS_FALLBACK_ENABLED=true
JOB_BROWSER_CRAWLER_ENABLED=true
JOB_BROWSER_TIMEOUT_SECONDS=20
TOPCV_ENABLE_EDGE_CRAWLER=false
=======
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3.5-flash
APP_API_KEY=your-private-access-code
PUBLIC_DEMO_ENABLED=true
PUBLIC_DEMO_DAILY_LIMIT=10
DEMO_MAX_INPUT_CHARS=12000
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
RATE_LIMIT_PER_MINUTE=30
ALLOWED_ORIGINS=*
```

6. Wait for the Space to build, then open its public URL.

## Which One Should You Choose?

For this project, start with Render. It matches the existing `render.yaml`, gives you a normal public web URL, and needs only one service.

Use Hugging Face Spaces if you want to present it as an AI demo portfolio project.

<<<<<<< HEAD
## Cost Note

The hosting can be free, but OpenAI API calls are billed by OpenAI unless your account has trial credits. Public demo mode only limits usage; it does not make the model calls free.
=======
## Gemini Free Tier Note

Gemini API currently has a free tier for developers and small projects, with free input and output tokens for supported models. Free tier access is still limited by model availability and rate limits, and Google says free-tier content can be used to improve their products.

For a public demo, keep:

```bash
PUBLIC_DEMO_DAILY_LIMIT=3
```

or another low number until you know the traffic pattern.

## Gemini Quota Or Rate Limit Error

If the app returns a Gemini quota/rate-limit error, the problem is usually not Render and not the FastAPI code. The Gemini API key cannot serve more requests at the moment.

Check these items:

1. Confirm `GEMINI_API_KEY` is valid and belongs to the project you expect.
2. Check Gemini API rate limits/quota in Google AI Studio or Google Cloud.
3. Wait for free tier quota to reset, reduce public demo traffic, or enable billing for higher usage.
4. If you created a new API key, update `GEMINI_API_KEY` in Render Environment and redeploy.
5. Keep `PUBLIC_DEMO_DAILY_LIMIT` low while testing publicly.

The app catches this upstream error and shows a readable message in the web UI.
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
