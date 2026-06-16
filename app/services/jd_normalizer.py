from app.prompts import JD_NORMALIZER_SYSTEM_PROMPT
<<<<<<< HEAD
from app.config import get_settings
from app.schemas import JDNormalizeRequest, NormalizedJobDescription
from app.services.local_analyzer import normalize_jd_locally
from app.services.openai_client import parse_with_llm
from app.services.source_loader import clean_text, ensure_text_within_limit, fetch_url_text
from fastapi import HTTPException, status
=======
from app.schemas import JDNormalizeRequest, NormalizedJobDescription
from app.services.gemini_client import parse_with_gemini
from app.services.source_loader import clean_text, ensure_text_within_limit, fetch_url_text
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
from starlette.concurrency import run_in_threadpool


async def normalize_jd(request: JDNormalizeRequest) -> NormalizedJobDescription:
    warnings: list[str] = []
    source_type = request.source_type

    if request.job_url is not None:
        source_type = "url"
        raw_text, url_warnings = await fetch_url_text(str(request.job_url))
        warnings.extend(url_warnings)
    elif request.job_description:
        raw_text = request.job_description
    else:
<<<<<<< HEAD
=======
        from fastapi import HTTPException, status

>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either job_description or job_url.",
        )

    raw_text = ensure_text_within_limit(raw_text, "job_description")
<<<<<<< HEAD
    settings = get_settings()
    if settings.local_analysis_fallback_enabled and not settings.has_llm_credentials:
        return normalize_jd_locally(raw_text, source_type=source_type, warnings=warnings)

=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
    user_prompt = f"""
Requested output language: {request.output_language}
Detected source type: {source_type}
Extraction warnings from API layer: {warnings}

Raw job description input:
{clean_text(raw_text)}
"""

<<<<<<< HEAD
    try:
        normalized = await run_in_threadpool(
            parse_with_llm,
            system_prompt=JD_NORMALIZER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            output_model=NormalizedJobDescription,
        )
    except HTTPException as exc:
        if not settings.local_analysis_fallback_enabled or exc.status_code < 500:
            raise
        warnings.append(f"LLM normalization failed; used local fallback. Reason: {exc.detail}")
        return normalize_jd_locally(raw_text, source_type=source_type, warnings=warnings)
=======
    normalized = await run_in_threadpool(
        parse_with_gemini,
        system_prompt=JD_NORMALIZER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        output_model=NormalizedJobDescription,
    )
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144

    merged_warnings = list(dict.fromkeys([*normalized.quality_warnings, *warnings]))
    return normalized.model_copy(update={"source_type": source_type, "quality_warnings": merged_warnings})
