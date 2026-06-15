# Deployment Guide

This project can run as one service: FastAPI serves both the web UI and the API.

## Option 1: Use It On Your Own Computer

Use this when only you need to test the web interface.

1. Create `.env` from `.env.example`.
2. Set at least:

```bash
OPENAI_API_KEY=sk-your-key
APP_API_KEY=your-private-access-code
PUBLIC_DEMO_ENABLED=false
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
OPENAI_API_KEY=sk-your-key
APP_API_KEY=your-private-access-code
OPENAI_MODEL=gpt-5.5
PUBLIC_DEMO_ENABLED=true
PUBLIC_DEMO_DAILY_LIMIT=10
DEMO_MAX_INPUT_CHARS=12000
RATE_LIMIT_PER_MINUTE=30
ALLOWED_ORIGINS=*
```

5. Set health check path:

```text
/health
```

6. After deploy finishes, open the Render URL. The root page `/` is the web UI.

Render free services can sleep after inactivity, so the first visit after idle may take about a minute. Keep `PUBLIC_DEMO_DAILY_LIMIT` low until you know your OpenAI cost per run.

## Option 3: Deploy To Hugging Face Spaces

Use this when you want an AI-demo-style public page. Docker Spaces can run FastAPI.

1. Create a new Hugging Face Space.
2. Select Docker as the SDK.
3. In the Space README YAML, use:

```yaml
---
title: AI Job Fit Analyzer
sdk: docker
app_port: 7860
---
```

4. Push this project into the Space repository.
5. In Space Settings, add runtime secrets/variables:

```bash
OPENAI_API_KEY=sk-your-key
APP_API_KEY=your-private-access-code
OPENAI_MODEL=gpt-5.5
PUBLIC_DEMO_ENABLED=true
PUBLIC_DEMO_DAILY_LIMIT=10
DEMO_MAX_INPUT_CHARS=12000
RATE_LIMIT_PER_MINUTE=30
ALLOWED_ORIGINS=*
```

6. Wait for the Space to build, then open its public URL.

## Which One Should You Choose?

For this project, start with Render. It matches the existing `render.yaml`, gives you a normal public web URL, and needs only one service.

Use Hugging Face Spaces if you want to present it as an AI demo portfolio project.

## Cost Note

The hosting can be free, but OpenAI API calls are billed by OpenAI unless your account has trial credits. Public demo mode only limits usage; it does not make the model calls free.
