from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.auth import InMemoryDailyQuota, InMemoryRateLimiter, require_api_key, require_public_demo_enabled
from app.config import get_settings
from app.schemas import (
    AnalyzeFullRequest,
    AnalyzeFullResponse,
    AnalyzeRequest,
    FileExtractResponse,
    FitAnalysisResponse,
    HealthResponse,
    JDNormalizeRequest,
    NormalizedJobDescription,
)
from app.services.fit_analyzer import analyze_fit, analyze_full
from app.services.jd_normalizer import normalize_jd
from app.services.source_loader import clean_text
from app.services.text_extractor import extract_upload_text


settings = get_settings()
static_dir = Path(__file__).resolve().parent / "static"
public_demo_quota = InMemoryDailyQuota()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API for normalizing job descriptions and analyzing candidate CV fit.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(InMemoryRateLimiter())
app.mount("/static", StaticFiles(directory=static_dir), name="static")


def _validate_demo_input_size(request: AnalyzeFullRequest) -> None:
    limit = settings.demo_max_input_chars
    fields = {
        "cv_text": request.cv_text,
        "job_description": request.job_description or "",
        "user_preferences": request.user_preferences or "",
    }
    for field_name, value in fields.items():
        if len(clean_text(value)) > limit:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"{field_name} is too long for the public demo. Limit is {limit} characters.",
            )


@app.get("/", include_in_schema=False)
async def web_app() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service=settings.app_name, environment=settings.environment)


@app.post(
    "/api/v1/jd/normalize",
    response_model=NormalizedJobDescription,
    dependencies=[Depends(require_api_key)],
    tags=["job-description"],
)
async def normalize_job_description(request: JDNormalizeRequest) -> NormalizedJobDescription:
    return await normalize_jd(request)


@app.post(
    "/api/v1/analyze",
    response_model=FitAnalysisResponse,
    dependencies=[Depends(require_api_key)],
    tags=["analysis"],
)
def analyze_candidate_fit(request: AnalyzeRequest) -> FitAnalysisResponse:
    return analyze_fit(request)


@app.post(
    "/api/v1/analyze/full",
    response_model=AnalyzeFullResponse,
    dependencies=[Depends(require_api_key)],
    tags=["analysis"],
)
async def analyze_candidate_fit_full(request: AnalyzeFullRequest) -> AnalyzeFullResponse:
    return await analyze_full(request)


@app.post(
    "/api/v1/files/extract",
    response_model=FileExtractResponse,
    dependencies=[Depends(require_api_key)],
    tags=["files"],
)
async def extract_file_text(file: UploadFile = File(...)) -> FileExtractResponse:
    return await extract_upload_text(file)


@app.post(
    "/api/v1/demo/analyze/full",
    response_model=AnalyzeFullResponse,
    dependencies=[Depends(require_public_demo_enabled)],
    tags=["public-demo"],
)
async def analyze_candidate_fit_public_demo(request: Request, payload: AnalyzeFullRequest) -> AnalyzeFullResponse:
    public_demo_quota.consume(request)
    _validate_demo_input_size(payload)
    return await analyze_full(payload)


@app.post(
    "/api/v1/demo/files/extract",
    response_model=FileExtractResponse,
    dependencies=[Depends(require_public_demo_enabled)],
    tags=["public-demo"],
)
async def extract_file_text_public_demo(file: UploadFile = File(...)) -> FileExtractResponse:
    return await extract_upload_text(file)
