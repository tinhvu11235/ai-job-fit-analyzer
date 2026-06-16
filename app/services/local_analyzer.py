import re

from app.schemas import (
    AnalyzeRequest,
    CVAdjustmentSuggestions,
    EvidenceMatch,
    FitAnalysisResponse,
    MissingSkill,
    NormalizedJobDescription,
    RequirementSummary,
    ScoreBreakdown,
)
from app.services.source_loader import clean_text


TECH_SKILLS = (
    "python",
    "fastapi",
    "django",
    "flask",
    "javascript",
    "typescript",
    "react",
    "vue",
    "angular",
    "node.js",
    "nodejs",
    "java",
    "spring",
    "c#",
    ".net",
    "go",
    "golang",
    "php",
    "laravel",
    "ruby",
    "rails",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "kafka",
    "rabbitmq",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "ci/cd",
    "git",
    "linux",
    "machine learning",
    "ai",
    "llm",
    "openai",
    "langchain",
    "rag",
    "vector database",
    "pandas",
    "numpy",
    "airflow",
    "dbt",
    "tableau",
    "power bi",
    "excel",
    "figma",
    "jira",
    "agile",
    "scrum",
)

SOFT_SKILLS = (
    "communication",
    "collaboration",
    "teamwork",
    "problem solving",
    "leadership",
    "ownership",
    "mentoring",
    "analytical",
    "stakeholder",
    "giao tiep",
    "lam viec nhom",
    "tu duy",
    "lanh dao",
)

TOOLS = (
    "git",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "jira",
    "figma",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "linux",
)

STOPWORDS = {
    "and",
    "the",
    "for",
    "with",
    "you",
    "your",
    "are",
    "will",
    "this",
    "that",
    "have",
    "has",
    "job",
    "role",
    "can",
    "our",
    "from",
    "into",
    "ung",
    "vien",
    "cong",
    "viec",
    "kinh",
    "nghiem",
    "yeu",
    "cau",
    "lam",
    "voi",
    "cac",
    "cho",
    "trong",
    "duoc",
    "co",
}


def _split_lines(text: str) -> list[str]:
    values: list[str] = []
    for line in re.split(r"[\r\n]+|(?<=[.;:])\s+", text):
        line = re.sub(r"^[\s\-*•+0-9.)]+", "", line).strip()
        line = clean_text(line)
        if 8 <= len(line) <= 260:
            values.append(line)
    return values


def _dedupe(items: list[str], limit: int = 8) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        item = clean_text(item)
        key = item.lower()
        if item and key not in seen:
            seen.add(key)
            result.append(item)
        if len(result) >= limit:
            break
    return result


def _extract_keywords(text: str, candidates: tuple[str, ...]) -> list[str]:
    lowered = text.lower()
    found: list[str] = []
    for skill in candidates:
        pattern = re.escape(skill).replace(r"\ ", r"\s+")
        if re.search(rf"(?<![\w.+#]){pattern}(?![\w.+#])", lowered):
            found.append(skill.upper() if skill in {"sql", "ai", "aws", "gcp"} else skill.title())
    return _dedupe(found, limit=14)


def _line_matches(line: str, needles: tuple[str, ...]) -> bool:
    lowered = line.lower()
    return any(needle in lowered for needle in needles)


def _first_match(text: str, patterns: tuple[str, ...]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return clean_text(match.group(1))
    return None


def _extract_job_title(lines: list[str]) -> str | None:
    patterns = (
        r"(?:job title|position|role|vi tri|chuc danh)\s*[:\-]\s*(.+)",
        r"(?:tuyen dung|hiring)\s*[:\-]?\s*(.+)",
    )
    joined = "\n".join(lines[:8])
    matched = _first_match(joined, patterns)
    if matched:
        return matched[:90]
    for line in lines[:6]:
        lowered = line.lower()
        if len(line) <= 90 and not _line_matches(lowered, ("about ", "company", "benefit", "salary")):
            return line
    return None


def _extract_company(lines: list[str]) -> str | None:
    joined = "\n".join(lines[:16])
    return _first_match(
        joined,
        (
            r"(?:company|organization|employer|cong ty)\s*[:\-]\s*(.+)",
            r"(?:at|tai)\s+([A-Z][A-Za-z0-9 &.,-]{2,70})",
        ),
    )


def _extract_work_mode(text: str) -> str:
    lowered = text.lower()
    if "remote" in lowered or "work from home" in lowered or "lam viec tu xa" in lowered:
        return "remote"
    if "hybrid" in lowered or "ket hop" in lowered:
        return "hybrid"
    if "onsite" in lowered or "on-site" in lowered or "van phong" in lowered:
        return "onsite"
    return "unknown"


def _extract_employment_type(text: str) -> str:
    lowered = text.lower()
    if "intern" in lowered or "thuc tap" in lowered:
        return "internship"
    if "part-time" in lowered or "part time" in lowered:
        return "part-time"
    if "contract" in lowered or "freelance" in lowered:
        return "contract"
    if "full-time" in lowered or "full time" in lowered or "toan thoi gian" in lowered:
        return "full-time"
    return "unknown"


def _extract_requirements(lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    must_have: list[str] = []
    nice_to_have: list[str] = []
    responsibilities: list[str] = []
    for line in lines:
        lowered = line.lower()
        if _line_matches(
            lowered,
            (
                "nice to have",
                "preferred",
                "plus",
                "bonus",
                "uu tien",
                "loi the",
            ),
        ):
            nice_to_have.append(line)
            continue
        if _line_matches(
            lowered,
            (
                "require",
                "must",
                "qualification",
                "experience",
                "proficient",
                "strong knowledge",
                "yeu cau",
                "bat buoc",
                "thanh thao",
                "kinh nghiem",
            ),
        ):
            must_have.append(line)
            continue
        if _line_matches(
            lowered,
            (
                "responsib",
                "you will",
                "build",
                "develop",
                "design",
                "maintain",
                "collaborate",
                "trach nhiem",
                "mo ta",
                "tham gia",
                "phat trien",
                "xay dung",
            ),
        ):
            responsibilities.append(line)

    if not must_have:
        must_have = [line for line in lines if _extract_keywords(line, TECH_SKILLS)]
    if not responsibilities:
        responsibilities = lines[:3]
    return _dedupe(must_have, 8), _dedupe(nice_to_have, 6), _dedupe(responsibilities, 8)


def _extract_salary(text: str) -> str | None:
    patterns = (
        r"((?:\$|usd\s*)\s?\d[\d,.kK]*(?:\s?[-–]\s?(?:\$|usd\s*)?\d[\d,.kK]*)?)",
        r"(\d{1,3}\s?(?:trieu|million|m|mio)\s?(?:vnd|dong)?(?:\s?[-–]\s?\d{1,3}\s?(?:trieu|million|m|mio)\s?(?:vnd|dong)?)?)",
    )
    return _first_match(text, patterns)


def _extract_years(text: str) -> str | None:
    return _first_match(
        text,
        (
            r"(\d+\+?\s*(?:years|yrs|year|nam)\s+(?:of\s+)?experience)",
            r"(\d+\+?\s*(?:years|yrs|year|nam))",
        ),
    )


def _content_words(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.]{2,}", text.lower())
    return {word for word in words if word not in STOPWORDS}


def normalize_jd_locally(
    raw_text: str,
    *,
    source_type: str = "unknown",
    warnings: list[str] | None = None,
) -> NormalizedJobDescription:
    cleaned = clean_text(raw_text)
    lines = _split_lines(raw_text)
    must_have, nice_to_have, responsibilities = _extract_requirements(lines)
    technical_skills = _extract_keywords(cleaned, TECH_SKILLS)
    soft_skills = _extract_keywords(cleaned, SOFT_SKILLS)
    tools = _extract_keywords(cleaned, TOOLS)
    job_title = _extract_job_title(lines)
    company_name = _extract_company(lines)
    years = _extract_years(cleaned)

    missing_information = []
    for value, label in (
        (job_title, "job_title"),
        (company_name, "company_name"),
        (responsibilities, "main_responsibilities"),
        (must_have, "must_have_requirements"),
    ):
        if not value:
            missing_information.append(label)

    quality_warnings = list(warnings or [])
    quality_warnings.append("LLM chưa khả dụng; hệ thống đã dùng bộ phân tích cục bộ.")
    if len(cleaned) < 200:
        quality_warnings.append("JD khá ngắn, một số trường có thể chưa đầy đủ.")

    return NormalizedJobDescription(
        source_type=source_type,  # type: ignore[arg-type]
        is_complete=not missing_information,
        confidence="Medium" if len(cleaned) >= 400 and technical_skills else "Low",
        job_title=job_title,
        company_name=company_name,
        location=_first_match(cleaned, (r"(?:location|dia diem)\s*[:\-]\s*([^.;]+)",)),
        work_mode=_extract_work_mode(cleaned),  # type: ignore[arg-type]
        employment_type=_extract_employment_type(cleaned),  # type: ignore[arg-type]
        seniority_level=_first_match(cleaned, (r"(senior|middle|mid-level|junior|lead|principal|intern)",)),
        salary_range=_extract_salary(cleaned),
        main_responsibilities=responsibilities,
        must_have_requirements=must_have,
        nice_to_have_requirements=nice_to_have,
        technical_skills=technical_skills,
        soft_skills=soft_skills,
        tools_or_platforms=tools,
        domain_or_industry=_first_match(cleaned, (r"(fintech|ecommerce|e-commerce|healthcare|education|saas|banking|retail|logistics)",)),
        language_requirements=_extract_keywords(cleaned, ("english", "vietnamese", "japanese", "korean", "chinese")),
        education_requirements=[
            line
            for line in lines
            if _line_matches(line, ("degree", "bachelor", "master", "university", "dai hoc", "cu nhan"))
        ][:4],
        years_of_experience=years,
        benefits=[
            line
            for line in lines
            if _line_matches(line, ("benefit", "salary", "insurance", "bonus", "phuc loi", "bao hiem", "thuong"))
        ][:6],
        missing_information=missing_information,
        quality_warnings=_dedupe(quality_warnings, 8),
        cleaned_job_description=clean_text(cleaned, max_chars=6000),
    )


def _requirement_match(requirement: str, cv_text: str, cv_words: set[str], cv_skills: set[str]) -> tuple[str, str] | None:
    requirement_words = _content_words(requirement)
    requirement_skills = {skill.lower() for skill in _extract_keywords(requirement, TECH_SKILLS)}
    matched_skills = sorted(skill for skill in requirement_skills if skill in cv_skills)
    if matched_skills:
        return "Strong", f"CV có nhắc đến {', '.join(matched_skills)}."

    overlap = sorted(requirement_words & cv_words)
    if len(overlap) >= 3:
        return "Partial", f"CV có phần giao nhau ở {', '.join(overlap[:5])}."
    return None


def _score_ratio(matches: int, total: int, points: int) -> int:
    if total <= 0:
        return max(points // 2, 1)
    return round(points * matches / total)


def analyze_fit_locally(request: AnalyzeRequest, reason: str | None = None) -> FitAnalysisResponse:
    cv_text = clean_text(request.cv_text)
    jd = request.normalized_job_description
    cv_words = _content_words(cv_text)
    jd_words = _content_words(jd.cleaned_job_description)
    cv_skills = {skill.lower() for skill in _extract_keywords(cv_text, TECH_SKILLS)}
    jd_skills = {skill.lower() for skill in jd.technical_skills}

    strong_matches: list[EvidenceMatch] = []
    partial_matches: list[EvidenceMatch] = []
    missing: list[MissingSkill] = []

    requirements = _dedupe([*jd.must_have_requirements, *jd.technical_skills], 14)
    for requirement in requirements:
        matched = _requirement_match(requirement, cv_text, cv_words, cv_skills)
        if matched is None:
            missing.append(
                MissingSkill(
                    requirement=requirement,
                    why_it_matters="Đây là yêu cầu quan trọng trong JD nhưng CV chưa có bằng chứng rõ.",
                    evidence_status="Missing",
                )
            )
            continue
        strength, evidence = matched
        item = EvidenceMatch(
            requirement=requirement,
            cv_evidence=evidence,
            reasoning="Đánh giá được tạo bằng heuristic cục bộ dựa trên từ khóa và độ giao nhau của nội dung.",
            strength=strength,  # type: ignore[arg-type]
        )
        if strength == "Strong":
            strong_matches.append(item)
        else:
            partial_matches.append(item)

    matched_skill_count = len(jd_skills & cv_skills)
    common_word_count = len((jd_words & cv_words) - STOPWORDS)
    responsibility_matches = sum(1 for item in jd.main_responsibilities if _content_words(item) & cv_words)

    breakdown = ScoreBreakdown(
        must_have_technical_skills=_score_ratio(matched_skill_count, len(jd_skills), 30),
        relevant_experience=min(25, 5 + common_word_count * 2),
        responsibility_alignment=_score_ratio(responsibility_matches, len(jd.main_responsibilities), 15),
        seniority_fit=7 if jd.years_of_experience else 5,
        domain_fit=8 if jd.domain_or_industry and jd.domain_or_industry.lower() in cv_text.lower() else 5,
        user_preferences_fit=7 if request.user_preferences else 5,
    )
    score = sum(breakdown.model_dump().values())
    score = max(0, min(100, score))
    recommendation = "Apply Now" if score >= 70 and len(missing) <= 2 else "Maybe" if score >= 45 else "Not Recommended"

    skills_to_highlight = sorted(jd_skills & cv_skills)[:8]
    if not skills_to_highlight:
        skills_to_highlight = sorted(cv_skills)[:5]

    reliability_notes = ["Hệ thống đang dùng fallback cục bộ, vì vậy hãy xem đây là ước lượng nhanh."]
    if reason:
        reliability_notes.append(reason)

    return FitAnalysisResponse(
        match_score=score,
        score_breakdown=breakdown,
        confidence="Medium" if cv_skills and jd_skills else "Low",
        recommendation=recommendation,  # type: ignore[arg-type]
        candidate_profile_summary=(
            f"CV có {len(cv_skills)} kỹ năng kỹ thuật nhận diện được; "
            f"khớp {matched_skill_count}/{len(jd_skills) or 1} kỹ năng nổi bật trong JD."
        ),
        job_requirement_summary=RequirementSummary(
            must_have_requirements=jd.must_have_requirements,
            nice_to_have_requirements=jd.nice_to_have_requirements,
            main_responsibilities=jd.main_responsibilities,
            seniority_expectations=jd.years_of_experience or jd.seniority_level,
            domain_or_industry=jd.domain_or_industry,
        ),
        strong_matches=strong_matches[:8],
        partial_matches=partial_matches[:8],
        missing_or_weak_skills=missing[:8],
        cv_adjustment_suggestions=CVAdjustmentSuggestions(
            what_to_emphasize=[
                f"Làm nổi bật kinh nghiệm liên quan đến {skill}." for skill in skills_to_highlight[:5]
            ]
            or ["Bổ sung các thành tựu và công nghệ gần với JD."],
            what_to_reorder=["Đưa các dự án/kinh nghiệm liên quan nhất lên đầu CV."],
            what_not_to_claim=["Không ghi nhận kỹ năng chưa có bằng chứng trong CV."],
        ),
        rewritten_cv_bullet_points=[
            f"Nhấn mạnh kinh nghiệm sử dụng {skill} trong dự án có kết quả đo lường được."
            for skill in skills_to_highlight[:4]
        ]
        or ["Thêm bullet về tác động cụ thể: vấn đề, hành động, kết quả."],
        skills_to_highlight=[skill.title() for skill in skills_to_highlight],
        suggested_learning_or_preparation_areas=[
            item.requirement for item in missing[:5]
        ]
        or ["Chuẩn bị ví dụ cụ thể cho các kỹ năng chính trong JD."],
        interview_questions=[
            f"Bạn đã ứng dụng {skill.title()} trong dự án nào và kết quả ra sao?"
            for skill in list(jd_skills)[:4]
        ]
        or ["Hãy mô tả một dự án gần nhất và vai trò của bạn trong dự án đó."],
        final_advice=(
            "Nên ứng tuyển nếu bạn có thể bổ sung bằng chứng rõ hơn cho các khoảng trống."
            if recommendation != "Not Recommended"
            else "Nên bổ sung thêm bằng chứng kỹ năng trước khi ứng tuyển vai trò này."
        ),
        reliability_notes=reliability_notes,
    )
