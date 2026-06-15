from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_web_app_is_served() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "AI Job Fit Analyzer" in response.text


def test_public_demo_is_disabled_by_default() -> None:
    response = client.post(
        "/api/v1/demo/analyze/full",
        json={
            "cv_text": "Experienced backend developer with Python, FastAPI, APIs, testing, and deployment work.",
            "job_description": "We need a Python backend developer with FastAPI and API deployment experience.",
            "source_type": "text",
            "output_language": "vi",
        },
    )
    assert response.status_code == 404


def test_file_extract_rejects_unsupported_extension() -> None:
    response = client.post(
        "/api/v1/files/extract",
        files={"file": ("image.png", b"fake", "image/png")},
    )
    assert response.status_code == 415
