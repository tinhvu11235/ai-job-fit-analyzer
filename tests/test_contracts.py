<<<<<<< HEAD
import os
import asyncio

os.environ["LLM_PROVIDER"] = "openai"
os.environ["OPENAI_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""
os.environ["LOCAL_ANALYSIS_FALLBACK_ENABLED"] = "true"

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import JobResult, JobSearchResponse, TopCVJobResult, TopCVJobSearchRequest, TopCVJobSearchResponse
from app.services.job_search import parse_job_search_html_for_source
from app.services.topcv_jobs import (
    analyze_topcv_response,
    derive_topcv_keywords_from_cv,
    parse_topcv_search_html,
    search_topcv_jobs,
)
=======
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import FitAnalysisResponse, NormalizedJobDescription
from app.services.gemini_client import _gemini_schema
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_web_app_is_served() -> None:
    response = client.get("/")
    assert response.status_code == 200
<<<<<<< HEAD
    assert "AI Job Fit Analyzer" in response.text


def test_runtime_config_is_public() -> None:
    response = client.get("/api/v1/runtime")
    assert response.status_code == 200
    body = response.json()
    assert body["llm_provider"] == "openai"
    assert body["llm_configured"] is False
    assert body["public_demo_enabled"] is False
    assert body["private_api_key_required"] is False
    assert body["local_analysis_fallback_enabled"] is True


def test_full_analysis_accepts_pasted_jd_without_openai_key() -> None:
    response = client.post(
        "/api/v1/analyze/full",
        json={
            "cv_text": (
                "Backend developer with Python, FastAPI, PostgreSQL, Docker, APIs, testing, "
                "and deployment experience on cloud projects."
            ),
            "job_description": (
                "Job title: Backend Engineer. Requirements: Python, FastAPI, PostgreSQL, Docker, "
                "API development, testing, and deployment experience. Responsibilities: build "
                "backend services and collaborate with product teams."
            ),
            "source_type": "text",
            "output_language": "vi",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["normalized_job_description"]["source_type"] == "text"
    assert body["analysis"]["match_score"] >= 40
    assert body["analysis"]["recommendation"] in {"Apply Now", "Maybe", "Not Recommended"}


def test_full_analysis_accepts_url_jd_with_local_fallback(monkeypatch) -> None:
    async def fake_fetch_url_text(url: str) -> tuple[str, list[str]]:
        assert url == "https://example.com/jobs/backend"
        return (
            "Job title: Senior Backend Developer. Requirements: Python, FastAPI, PostgreSQL, "
            "Docker, AWS, CI/CD, and API design. Responsibilities: design and maintain services.",
            ["mocked fetch"],
        )

    monkeypatch.setattr("app.services.jd_normalizer.fetch_url_text", fake_fetch_url_text)

    response = client.post(
        "/api/v1/analyze/full",
        json={
            "cv_text": (
                "Senior backend developer with Python, FastAPI, PostgreSQL, Docker, AWS, "
                "CI/CD pipelines, API design, testing, and production deployment."
            ),
            "job_url": "https://example.com/jobs/backend",
            "source_type": "url",
            "output_language": "vi",
        },
    )

    assert response.status_code == 200
    body = response.json()
    jd = body["normalized_job_description"]
    assert jd["source_type"] == "url"
    assert any("mocked fetch" in warning for warning in jd["quality_warnings"])
=======
    assert "CV Fit Analyst Agent" in response.text
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144


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


<<<<<<< HEAD
=======
def test_gemini_schema_is_flattened_for_structured_output() -> None:
    fit_schema = _gemini_schema(FitAnalysisResponse)
    jd_schema = _gemini_schema(NormalizedJobDescription)
    serialized = f"{fit_schema}{jd_schema}"
    assert "$defs" not in serialized
    assert "anyOf" not in serialized


>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
def test_file_extract_rejects_unsupported_extension() -> None:
    response = client.post(
        "/api/v1/files/extract",
        files={"file": ("image.png", b"fake", "image/png")},
    )
    assert response.status_code == 415
<<<<<<< HEAD


def test_topcv_parser_extracts_public_job_cards() -> None:
    html = """
    <html>
      <body>
        <div class="job-card">
          <a href="/viec-lam/backend-python-developer/123456.html">Backend Python Developer</a>
          <div>CÔNG TY TNHH CÔNG NGHỆ ABC</div>
          <span>20 triệu - 35 triệu</span>
          <span>Hà Nội</span>
        </div>
      </body>
    </html>
    """

    results, warnings = parse_topcv_search_html(
        html,
        search_url="https://www.topcv.vn/viec-lam?keyword=python",
        keyword="python backend",
        cv_text="Python FastAPI backend developer",
    )

    assert warnings == []
    assert len(results) == 1
    assert results[0].title == "Backend Python Developer"
    assert results[0].company_name == "CÔNG TY TNHH CÔNG NGHỆ ABC"
    assert results[0].location == "Hà Nội"
    assert results[0].fit_score > 50


def test_multi_source_parser_extracts_vietnamworks_cards() -> None:
    html = """
    <html>
      <body>
        <article class="job-card">
          <a href="https://www.vietnamworks.com/python-backend-engineer-123456-jv?utm_source_navi=test">
            Python Backend Engineer
          </a>
          <div>ABC Tech Company</div>
          <span>Hà Nội</span>
          <span>20 triệu - 35 triệu</span>
        </article>
      </body>
    </html>
    """

    results, warnings = parse_job_search_html_for_source(
        "vietnamworks",
        html,
        search_url="https://www.vietnamworks.com/viec-lam?q=python",
        keyword="python backend",
        cv_text="Python FastAPI backend developer",
    )

    assert warnings == []
    assert len(results) == 1
    assert results[0].source == "vietnamworks"
    assert results[0].source_label == "VietnamWorks"
    assert results[0].title == "Python Backend Engineer"
    assert results[0].url == "https://www.vietnamworks.com/python-backend-engineer-123456-jv"
    assert results[0].fit_score > 50


def test_multi_source_parser_extracts_joboko_cards() -> None:
    html = """
    <html>
      <body>
        <li class="job-item">
          <a href="/viec-lam-python-developer-xvi6532758">Python Developer</a>
          <p>CÔNG TY TNHH CÔNG NGHỆ ABC</p>
          <span>Remote</span>
        </li>
      </body>
    </html>
    """

    results, warnings = parse_job_search_html_for_source(
        "joboko",
        html,
        search_url="https://vn.joboko.com/tim-viec-lam?keywords=python",
        keyword="python",
        cv_text="Python developer with APIs",
    )

    assert warnings == []
    assert len(results) == 1
    assert results[0].source == "joboko"
    assert results[0].company_name == "CÔNG TY TNHH CÔNG NGHỆ ABC"
    assert results[0].location == "Remote"


def test_topcv_search_endpoint_returns_normalized_results(monkeypatch) -> None:
    async def fake_search_topcv_jobs(payload):
        return TopCVJobSearchResponse(
            query=payload.keyword,
            search_url="https://www.topcv.vn/viec-lam?keyword=python",
            results=[
                TopCVJobResult(
                    title="Python Backend Engineer",
                    company_name="ABC Tech",
                    location="Hà Nội",
                    salary="Thỏa thuận",
                    url="https://www.topcv.vn/viec-lam/python-backend/123.html",
                    fit_score=82,
                    fit_reasons=["Khớp từ khóa tìm kiếm"],
                )
            ],
            warnings=[],
        )

    monkeypatch.setattr("app.main.search_topcv_jobs", fake_search_topcv_jobs)

    response = client.post(
        "/api/v1/jobs/topcv/search",
        json={"keyword": "python", "cv_text": "Python backend developer"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "topcv"
    assert body["results"][0]["fit_score"] == 82


def test_multi_source_search_endpoint_returns_normalized_results(monkeypatch) -> None:
    async def fake_search_jobs(payload):
        return JobSearchResponse(
            sources=payload.sources,
            query=payload.keyword,
            search_url="https://itviec.com/it-jobs?query=python",
            search_urls={"itviec": "https://itviec.com/it-jobs?query=python"},
            results=[
                JobResult(
                    source="itviec",
                    source_label="ITviec",
                    title="Python Backend Engineer",
                    company_name="ABC Tech",
                    location="Hà Nội",
                    salary="Thỏa thuận",
                    url="https://itviec.com/it-jobs/python-backend-engineer-123",
                    fit_score=84,
                    fit_reasons=["Khớp Python"],
                )
            ],
            warnings=[],
        )

    monkeypatch.setattr("app.main.search_jobs", fake_search_jobs)

    response = client.post(
        "/api/v1/jobs/search",
        json={"keyword": "python", "sources": ["itviec"], "cv_text": "Python backend developer"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "multi"
    assert body["sources"] == ["itviec"]
    assert body["results"][0]["source_label"] == "ITviec"
    assert body["results"][0]["fit_score"] == 84


def test_topcv_search_falls_back_to_edge_crawler_after_blocked_http(monkeypatch) -> None:
    class FakeSettings:
        topcv_enable_edge_crawler = True

    class FakeResponse:
        status_code = 403
        text = ""

        def raise_for_status(self) -> None:
            raise AssertionError("raise_for_status should not be called for blocked responses")

    class FakeAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args) -> None:
            return None

        async def get(self, url: str):
            return FakeResponse()

    async def fake_fetch_topcv_with_edge(search_url: str):
        return (
            """
            <html><body>
              <div class="job-card">
                <a href="/viec-lam/ai-engineer/123.html">AI Engineer</a>
                <div>ABC AI Lab</div>
                <span>Remote</span>
              </div>
            </body></html>
            """,
            None,
        )

    monkeypatch.setattr("app.services.topcv_jobs.get_settings", lambda: FakeSettings())
    monkeypatch.setattr("app.services.topcv_jobs.httpx.AsyncClient", FakeAsyncClient)
    monkeypatch.setattr("app.services.topcv_jobs.fetch_topcv_with_edge", fake_fetch_topcv_with_edge)

    response = asyncio.run(search_topcv_jobs(TopCVJobSearchRequest(keyword="AI Engineer", cv_text="AI Engineer Python")))

    assert len(response.results) == 1
    assert response.results[0].title == "AI Engineer"
    assert any("Edge" in warning for warning in response.warnings)


def test_topcv_keyword_derivation_from_ai_engineer_cv() -> None:
    keywords = derive_topcv_keywords_from_cv(
        "Vu Duc Tinh AI Engineer Python Machine Learning Deep Learning Computer Vision NLP RAG PyTorch TensorFlow"
    )

    assert keywords[0] == "AI Engineer Python Machine Learning"
    assert "Machine Learning" in keywords


def test_topcv_response_can_attach_job_fit_analysis() -> None:
    response = TopCVJobSearchResponse(
        query="python",
        search_url="https://www.topcv.vn/tim-viec-lam-python",
        results=[
            TopCVJobResult(
                title="Python Backend Engineer",
                company_name="ABC Tech",
                location="Hà Nội",
                salary="Thỏa thuận",
                url="https://www.topcv.vn/viec-lam/python-backend/123.html",
                snippet=(
                    "Job title: Python Backend Engineer. Requirements: Python, FastAPI, Docker, SQL. "
                    "Responsibilities: build APIs and backend services."
                ),
                fit_score=82,
                fit_reasons=["Khớp Python"],
            )
        ],
        warnings=[],
    )

    analyzed = asyncio.run(
        analyze_topcv_response(
            response,
            cv_text="Backend developer with Python, FastAPI, Docker, SQL, APIs, testing, and deployment.",
            analyze_limit=1,
            output_language="vi",
        )
    )

    job = analyzed.results[0]
    assert job.analysis_status == "ready"
    assert job.analysis is not None
    assert job.normalized_job_description is not None
    assert job.analysis.match_score >= 40


def test_topcv_recommend_endpoint_uses_cv(monkeypatch) -> None:
    async def fake_recommend_topcv_jobs_from_cv(payload):
        return TopCVJobSearchResponse(
            query="AI Engineer Python Machine Learning",
            suggested_keywords=["AI Engineer Python Machine Learning", "AI Engineer", "Python"],
            search_url="https://www.topcv.vn/viec-lam?keyword=AI+Engineer+Python+Machine+Learning",
            results=[],
            warnings=["Từ khóa suy ra từ CV: AI Engineer Python Machine Learning"],
        )

    monkeypatch.setattr("app.main.recommend_topcv_jobs_from_cv", fake_recommend_topcv_jobs_from_cv)

    response = client.post(
        "/api/v1/jobs/topcv/recommend",
        json={"cv_text": "AI Engineer with Python Machine Learning and RAG experience."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["suggested_keywords"][0] == "AI Engineer Python Machine Learning"
=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
