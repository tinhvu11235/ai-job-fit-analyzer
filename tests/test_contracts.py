from fastapi.testclient import TestClient

from app.main import app
from app.schemas import FitAnalysisResponse, NormalizedJobDescription
from app.services.gemini_client import _gemini_schema


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_web_app_is_served() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "CV Fit Analyst Agent" in response.text


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


def test_gemini_schema_is_flattened_for_structured_output() -> None:
    fit_schema = _gemini_schema(FitAnalysisResponse)
    jd_schema = _gemini_schema(NormalizedJobDescription)
    serialized = f"{fit_schema}{jd_schema}"
    assert "$defs" not in serialized
    assert "anyOf" not in serialized


def test_file_extract_rejects_unsupported_extension() -> None:
    response = client.post(
        "/api/v1/files/extract",
        files={"file": ("image.png", b"fake", "image/png")},
    )
    assert response.status_code == 415
