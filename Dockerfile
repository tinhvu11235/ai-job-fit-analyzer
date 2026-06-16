FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
<<<<<<< HEAD
ENV PORT=10000
=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
<<<<<<< HEAD
RUN python -m playwright install --with-deps chromium

COPY app ./app

EXPOSE 10000

CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
=======

COPY app ./app

EXPOSE 7860

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
