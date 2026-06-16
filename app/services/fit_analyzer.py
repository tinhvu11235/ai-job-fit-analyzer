from app.prompts import FIT_ANALYZER_SYSTEM_PROMPT
<<<<<<< HEAD
from app.config import get_settings
from app.schemas import AnalyzeFullRequest, AnalyzeFullResponse, AnalyzeRequest, FitAnalysisResponse, JDNormalizeRequest
from app.services.jd_normalizer import normalize_jd
from app.services.local_analyzer import analyze_fit_locally
from app.services.openai_client import parse_with_llm
from app.services.source_loader import clean_text, ensure_text_within_limit
from fastapi import HTTPException
=======
from app.schemas import AnalyzeFullRequest, AnalyzeFullResponse, AnalyzeRequest, FitAnalysisResponse, JDNormalizeRequest
from app.services.jd_normalizer import normalize_jd
from app.services.gemini_client import parse_with_gemini
from app.services.source_loader import clean_text, ensure_text_within_limit
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
from starlette.concurrency import run_in_threadpool


def analyze_fit(request: AnalyzeRequest) -> FitAnalysisResponse:
    cv_text = ensure_text_within_limit(request.cv_text, "cv_text")
<<<<<<< HEAD
    settings = get_settings()
    if settings.local_analysis_fallback_enabled and not settings.has_llm_credentials:
        return analyze_fit_locally(request)

=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
    jd_json = request.normalized_job_description.model_dump_json(indent=2)
    preferences = request.user_preferences or "No explicit user preferences provided."

    user_prompt = f"""
Requested output language: {request.output_language}

Candidate CV:
{clean_text(cv_text)}

Normalized Job Description:
{jd_json}

User Preferences:
{clean_text(preferences)}

Return a practical, honest, job-specific analysis. Every rewritten CV bullet must be
based only on evidence present in the CV. If a requirement has no evidence, mark it
missing instead of implying the candidate has it.
"""

<<<<<<< HEAD
    try:
        return parse_with_llm(
            system_prompt=FIT_ANALYZER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            output_model=FitAnalysisResponse,
        )
    except HTTPException as exc:
        if not settings.local_analysis_fallback_enabled or exc.status_code < 500:
            raise
        return analyze_fit_locally(request, reason=f"LLM analysis failed: {exc.detail}")
=======
    return parse_with_gemini(
        system_prompt=FIT_ANALYZER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        output_model=FitAnalysisResponse,
    )
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144


async def analyze_full(request: AnalyzeFullRequest) -> AnalyzeFullResponse:
    normalized = await normalize_jd(
        JDNormalizeRequest(
            job_description=request.job_description,
            job_url=request.job_url,
            source_type=request.source_type,
            output_language=request.output_language,
        )
    )
    analysis = await run_in_threadpool(
        analyze_fit,
        AnalyzeRequest(
            cv_text=request.cv_text,
            normalized_job_description=normalized,
            user_preferences=request.user_preferences,
            output_language=request.output_language,
        )
    )
    return AnalyzeFullResponse(normalized_job_description=normalized, analysis=analysis)
