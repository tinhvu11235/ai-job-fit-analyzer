from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


SourceType = Literal["text", "url", "pdf", "docx", "image_ocr", "email", "unknown"]
ConfidenceLevel = Literal["High", "Medium", "Low"]
Recommendation = Literal["Apply Now", "Maybe", "Not Recommended"]
WorkMode = Literal["onsite", "hybrid", "remote", "unknown"]
EmploymentType = Literal["full-time", "part-time", "internship", "contract", "unknown"]
MatchStrength = Literal["Strong", "Partial", "Weak"]


class JDNormalizeRequest(BaseModel):
    job_description: str | None = Field(default=None, description="Raw pasted JD or already extracted OCR/file text.")
    job_url: HttpUrl | None = Field(default=None, description="Optional job URL to fetch and clean.")
    source_type: SourceType = "unknown"
    output_language: str = Field(default="vi", description="Language for generated explanatory text.")

    @field_validator("job_description")
    @classmethod
    def strip_empty_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        return value or None


class NormalizedJobDescription(BaseModel):
    source_type: SourceType
    is_complete: bool
    confidence: ConfidenceLevel
    job_title: str | None
    company_name: str | None
    location: str | None
    work_mode: WorkMode
    employment_type: EmploymentType
    seniority_level: str | None
    salary_range: str | None
    main_responsibilities: list[str]
    must_have_requirements: list[str]
    nice_to_have_requirements: list[str]
    technical_skills: list[str]
    soft_skills: list[str]
    tools_or_platforms: list[str]
    domain_or_industry: str | None
    language_requirements: list[str]
    education_requirements: list[str]
    years_of_experience: str | None
    benefits: list[str]
    missing_information: list[str]
    quality_warnings: list[str]
    cleaned_job_description: str


class AnalyzeRequest(BaseModel):
    cv_text: str = Field(min_length=20)
    normalized_job_description: NormalizedJobDescription
    user_preferences: str | None = None
    output_language: str = Field(default="vi")


class AnalyzeFullRequest(BaseModel):
    cv_text: str = Field(min_length=20)
    job_description: str | None = None
    job_url: HttpUrl | None = None
    source_type: SourceType = "unknown"
    user_preferences: str | None = None
    output_language: str = Field(default="vi")


class RequirementSummary(BaseModel):
    must_have_requirements: list[str]
    nice_to_have_requirements: list[str]
    main_responsibilities: list[str]
    seniority_expectations: str | None
    domain_or_industry: str | None


class EvidenceMatch(BaseModel):
    requirement: str
    cv_evidence: str
    reasoning: str
    strength: MatchStrength


class MissingSkill(BaseModel):
    requirement: str
    why_it_matters: str
    evidence_status: Literal["Missing", "Weak", "Unclear"]


class CVAdjustmentSuggestions(BaseModel):
    what_to_emphasize: list[str]
    what_to_reorder: list[str]
    what_not_to_claim: list[str]


class ScoreBreakdown(BaseModel):
    must_have_technical_skills: int = Field(ge=0, le=30)
    relevant_experience: int = Field(ge=0, le=25)
    responsibility_alignment: int = Field(ge=0, le=15)
    seniority_fit: int = Field(ge=0, le=10)
    domain_fit: int = Field(ge=0, le=10)
    user_preferences_fit: int = Field(ge=0, le=10)


class FitAnalysisResponse(BaseModel):
    match_score: int = Field(ge=0, le=100)
    score_breakdown: ScoreBreakdown
    confidence: ConfidenceLevel
    recommendation: Recommendation
    candidate_profile_summary: str
    job_requirement_summary: RequirementSummary
    strong_matches: list[EvidenceMatch]
    partial_matches: list[EvidenceMatch]
    missing_or_weak_skills: list[MissingSkill]
    cv_adjustment_suggestions: CVAdjustmentSuggestions
    rewritten_cv_bullet_points: list[str]
    skills_to_highlight: list[str]
    suggested_learning_or_preparation_areas: list[str]
    interview_questions: list[str]
    final_advice: str
    reliability_notes: list[str]


class AnalyzeFullResponse(BaseModel):
    normalized_job_description: NormalizedJobDescription
    analysis: FitAnalysisResponse


class FileExtractResponse(BaseModel):
    filename: str
    source_type: SourceType
    text: str
    character_count: int
    warnings: list[str]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str

