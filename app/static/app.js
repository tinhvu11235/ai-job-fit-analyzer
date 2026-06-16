const form = document.querySelector("#analysis-form");
const cvText = document.querySelector("#cv-text");
const cvFile = document.querySelector("#cv-file");
const jdText = document.querySelector("#jd-text");
const jdUrl = document.querySelector("#jd-url");
const accessCode = document.querySelector("#access-code");
<<<<<<< HEAD
const accessCodeField = document.querySelector("#access-code-field");
const outputLanguage = document.querySelector("#output-language");
const userPreferences = document.querySelector("#user-preferences");
const runtimeFields = document.querySelector("#runtime-fields");
const analyzeButton = document.querySelector("#analyze-button");
const clearButton = document.querySelector("#clear-button");
const fileStatus = document.querySelector("#file-status");
const modeChip = document.querySelector("#mode-chip");
const runtimeNote = document.querySelector("#runtime-note");
const cvCounter = document.querySelector("#cv-counter");
const jdCounter = document.querySelector("#jd-counter");
const jdSourceNote = document.querySelector("#jd-source-note");
=======
const outputLanguage = document.querySelector("#output-language");
const userPreferences = document.querySelector("#user-preferences");
const analyzeButton = document.querySelector("#analyze-button");
const analyzeButtonLabel = document.querySelector("#analyze-button .button-label");
const analyzeButtonIcon = document.querySelector("#analyze-button .button-icon");
const clearButton = document.querySelector("#clear-button");
const fileStatus = document.querySelector("#file-status");
const modeChip = document.querySelector("#mode-chip");
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
const alertBox = document.querySelector("#alert-box");
const emptyState = document.querySelector("#empty-state");
const resultContent = document.querySelector("#result-content");
const resultTitle = document.querySelector("#result-title");
const scoreRing = document.querySelector("#score-ring");
const scoreValue = document.querySelector("#score-value");
const recommendation = document.querySelector("#recommendation");
const candidateSummary = document.querySelector("#candidate-summary");
const finalAdvice = document.querySelector("#final-advice");
const scoreBreakdown = document.querySelector("#score-breakdown");
<<<<<<< HEAD
const qualityStrip = document.querySelector("#quality-strip");
=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
const matchesPanel = document.querySelector("#matches-panel");
const gapsPanel = document.querySelector("#gaps-panel");
const rewritePanel = document.querySelector("#rewrite-panel");
const interviewPanel = document.querySelector("#interview-panel");
const copySummary = document.querySelector("#copy-summary");
const downloadJson = document.querySelector("#download-json");
<<<<<<< HEAD
const topcvSearchForm = document.querySelector("#topcv-search-form");
const topcvKeyword = document.querySelector("#topcv-keyword");
const topcvLocation = document.querySelector("#topcv-location");
const topcvSearchButton = document.querySelector("#topcv-search-button");
const topcvSearchStatus = document.querySelector("#topcv-search-status");
const topcvResultsSection = document.querySelector("#topcv-results-section");
const topcvResults = document.querySelector("#topcv-results");
const topcvOpenSearch = document.querySelector("#topcv-open-search");
const jobSourceInputs = document.querySelectorAll('input[name="job-source"]');

let jdMode = "text";
let latestResult = null;
let latestJobPayload = null;
let runtimeConfig = null;
const sourceLabels = {
  topcv: "TopCV",
  joboko: "JobOKO",
  vietnamworks: "VietnamWorks",
  glints: "Glints",
  itviec: "ITviec",
};

function currentBasePath() {
  const key = accessCode.value.trim();
  if (key) {
    return "/api/v1";
  }
  if (runtimeConfig?.public_demo_enabled) {
    return "/api/v1/demo";
  }
  if (runtimeConfig && !runtimeConfig.private_api_key_required) {
    return "/api/v1";
  }
  return "/api/v1/demo";
}

function endpoint(path) {
  return `${currentBasePath()}${path}`;
=======

let jdMode = "text";
let latestResult = null;

function endpoint(path) {
  const key = accessCode.value.trim();
  if (key) {
    return `/api/v1${path}`;
  }
  return `/api/v1/demo${path}`;
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
}

function headers(json = true) {
  const value = {};
  const key = accessCode.value.trim();
  if (json) {
    value["Content-Type"] = "application/json";
  }
  if (key) {
    value["X-API-Key"] = key;
  }
  return value;
}

<<<<<<< HEAD
function showAlert(message) {
  alertBox.textContent = message;
=======
function normalizeErrorDetail(detail) {
  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    return {
      title: detail.title || "Không thể hoàn tất yêu cầu",
      message: detail.message || JSON.stringify(detail),
      actions: detail.actions || [],
    };
  }

  const message = String(detail || "Không thể phân tích lúc này.");
  const normalizedMessage = message.toLowerCase();
  if (
    message.includes("insufficient_quota") ||
    normalizedMessage.includes("exceeded your current quota") ||
    normalizedMessage.includes("gemini") && (normalizedMessage.includes("quota") || normalizedMessage.includes("rate"))
  ) {
    return {
      title: "Gemini đang hết quota hoặc bị giới hạn tốc độ",
      message: "API key Gemini hiện tại đã chạm giới hạn free tier/rate limit hoặc chưa bật billing cho mức dùng cao hơn.",
      actions: [
        "Kiểm tra quota/rate limit của Gemini API trong Google AI Studio hoặc Google Cloud.",
        "Giảm PUBLIC_DEMO_DAILY_LIMIT nếu đang mở demo công khai.",
        "Chờ quota free tier reset hoặc nâng cấp billing nếu cần dùng nhiều hơn.",
      ],
    };
  }

  return {
    title: "Không thể phân tích",
    message,
    actions: [],
  };
}

function showAlert(detail) {
  const error = normalizeErrorDetail(detail);
  const actions = error.actions?.length
    ? `<ul>${error.actions.map((action) => `<li>${escapeHtml(action)}</li>`).join("")}</ul>`
    : "";
  alertBox.innerHTML = `
    <strong>${escapeHtml(error.title)}</strong>
    <span>${escapeHtml(error.message)}</span>
    ${actions}
  `;
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
  alertBox.classList.remove("is-hidden");
}

function clearAlert() {
  alertBox.textContent = "";
  alertBox.classList.add("is-hidden");
}

function setBusy(isBusy) {
  analyzeButton.disabled = isBusy;
  analyzeButton.classList.toggle("is-loading", isBusy);
<<<<<<< HEAD
  const icon = isBusy ? "bi-arrow-repeat" : "bi-stars";
  analyzeButton.innerHTML = `<i class="bi ${icon} button-glyph" aria-hidden="true"></i>${isBusy ? "Đang phân tích..." : "Phân tích"}`;
=======
  analyzeButtonLabel.textContent = isBusy ? "Đang phân tích..." : "Phân tích";
  analyzeButtonIcon.textContent = isBusy ? "" : "→";
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

<<<<<<< HEAD
function translateLabel(value) {
  const labels = {
    "Apply Now": "Nên ứng tuyển",
    Maybe: "Cân nhắc",
    "Not Recommended": "Không nên ứng tuyển",
    Strong: "Mạnh",
    Partial: "Một phần",
    Weak: "Yếu",
    Missing: "Thiếu",
    Unclear: "Chưa rõ",
  };
  return labels[value] || value;
}

function selectedJobSources() {
  const sources = Array.from(jobSourceInputs)
    .filter((input) => input.checked)
    .map((input) => input.value);
  return sources.length ? sources : ["topcv"];
}

function sourceLabel(source) {
  return sourceLabels[source] || source || "Nguồn";
}

async function readError(response) {
  try {
    const body = await response.json();
    const detail = Array.isArray(body.detail)
      ? body.detail.map((item) => item.msg || JSON.stringify(item)).join("; ")
      : body.detail || body.message || response.statusText;

    if (response.status === 404 && String(detail).includes("Public demo is not enabled")) {
      return "Demo đang tắt. Hãy nhập mã truy cập, hoặc bật PUBLIC_DEMO_ENABLED=true khi chạy public demo.";
    }
    if (response.status === 401) {
      return "Mã truy cập không đúng hoặc đang thiếu.";
    }
    if (response.status === 503 && String(detail).includes("OPENAI_API_KEY")) {
      return "OPENAI_API_KEY chưa được cấu hình. Local fallback có thể đang tắt trên server.";
    }
    return detail;
=======
async function readError(response) {
  try {
    const body = await response.json();
    if (Array.isArray(body.detail)) {
      return {
        title: "Dữ liệu chưa hợp lệ",
        message: body.detail.map((item) => item.msg || JSON.stringify(item)).join("; "),
      };
    }
    if (body.detail && typeof body.detail === "object") {
      return body.detail;
    }
    return body.detail || body.message || response.statusText;
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
  } catch {
    return response.statusText;
  }
}

<<<<<<< HEAD
function formatCount(value) {
  return `${value.length.toLocaleString("vi-VN")} ký tự`;
}

function updateCounters() {
  cvCounter.textContent = formatCount(cvText.value);
  jdCounter.textContent = jdMode === "url" ? (jdUrl.value.trim() ? "URL sẵn sàng" : "Đang chờ URL") : formatCount(jdText.value);
}

function updateModeChip() {
  const key = accessCode.value.trim();
  const requiresAccessCode = Boolean(runtimeConfig?.private_api_key_required && !runtimeConfig?.public_demo_enabled);
  if (accessCodeField) {
    accessCodeField.classList.toggle("is-hidden", !requiresAccessCode);
  }
  if (runtimeFields) {
    runtimeFields.classList.toggle("access-code-hidden", !requiresAccessCode);
  }

  if (key) {
    modeChip.textContent = "Riêng tư";
  } else if (!runtimeConfig) {
    modeChip.textContent = "Đang tải";
  } else if (runtimeConfig.public_demo_enabled) {
    modeChip.textContent = "Demo";
  } else if (!runtimeConfig.private_api_key_required) {
    modeChip.textContent = "Cục bộ";
  } else {
    modeChip.textContent = "Cần mã";
  }

  if (!runtimeConfig) {
    runtimeNote.textContent = "Đang kiểm tra cấu hình...";
    return;
  }

  const parts = [];
  if (runtimeConfig.public_demo_enabled) {
    parts.push("Demo công khai đang bật.");
  } else if (!runtimeConfig.private_api_key_required) {
    parts.push("API riêng đang mở cho local.");
  } else {
    parts.push("Demo đang tắt; cần mã truy cập để phân tích.");
  }
  if (runtimeConfig.llm_configured) {
    parts.push(`Đang dùng ${runtimeConfig.llm_provider}.`);
  } else {
    parts.push("Chưa có LLM key.");
  }
  if (runtimeConfig.local_analysis_fallback_enabled) {
    parts.push("Fallback cục bộ sẵn sàng khi thiếu LLM key.");
  }
  runtimeNote.textContent = parts.join(" ");
}

async function loadRuntimeConfig() {
  try {
    const response = await fetch("/api/v1/runtime");
    if (!response.ok) {
      throw new Error(await readError(response));
    }
    runtimeConfig = await response.json();
  } catch (error) {
    runtimeConfig = null;
    runtimeNote.textContent = error.message || "Không đọc được cấu hình runtime.";
  } finally {
    updateModeChip();
  }
}

function itemHtml(title, body, meta, tone = "") {
  const tag = meta ? `<span class="tag ${tone}">${escapeHtml(translateLabel(meta))}</span>` : "";
=======
function itemHtml(title, body, meta, tone = "") {
  const tag = meta ? `<span class="tag ${tone}">${escapeHtml(meta)}</span>` : "";
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
  return `
    <article class="item">
      <strong>${escapeHtml(title)}</strong>
      ${body ? `<p>${escapeHtml(body)}</p>` : ""}
      ${tag}
    </article>
  `;
}

function listHtml(items, emptyText) {
  if (!items || items.length === 0) {
    return itemHtml(emptyText, "", "");
  }
  return items.map((item) => itemHtml(item, "", "")).join("");
}

function renderEvidence(items, emptyText, tone) {
  if (!items || items.length === 0) {
    return itemHtml(emptyText, "", "");
  }
  return items
    .map((item) => {
      const body = [item.cv_evidence, item.reasoning].filter(Boolean).join(" ");
      return itemHtml(item.requirement, body, item.strength, tone);
    })
    .join("");
}

function renderGaps(items) {
  if (!items || items.length === 0) {
    return itemHtml("Chưa thấy khoảng trống lớn", "", "");
  }
  return items
<<<<<<< HEAD
    .map((item) => itemHtml(item.requirement, item.why_it_matters, item.evidence_status, "partial"))
=======
    .map((item) => {
      return itemHtml(item.requirement, item.why_it_matters, item.evidence_status, "partial");
    })
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
    .join("");
}

function renderScoreBreakdown(breakdown) {
  const labels = {
    must_have_technical_skills: "Kỹ năng bắt buộc",
    relevant_experience: "Kinh nghiệm liên quan",
    responsibility_alignment: "Trách nhiệm công việc",
    seniority_fit: "Cấp bậc",
    domain_fit: "Lĩnh vực",
    user_preferences_fit: "Ưu tiên cá nhân",
  };

  scoreBreakdown.innerHTML = Object.entries(labels)
    .map(([key, label]) => {
      const value = breakdown?.[key] ?? 0;
      return `
        <div class="metric">
          <strong>${escapeHtml(value)}</strong>
          <span>${escapeHtml(label)}</span>
        </div>
      `;
    })
    .join("");
}

<<<<<<< HEAD
function renderQualityNotes(payload) {
  const notes = [
    ...(payload.normalized_job_description?.quality_warnings || []),
    ...(payload.analysis?.reliability_notes || []),
  ].filter(Boolean);
  if (!notes.length) {
    qualityStrip.classList.add("is-hidden");
    qualityStrip.textContent = "";
    return;
  }
  qualityStrip.textContent = notes.slice(0, 4).join(" | ");
  qualityStrip.classList.remove("is-hidden");
=======
function recommendationLabel(value) {
  const labels = {
    "Apply Now": "Nên ứng tuyển",
    Maybe: "Cân nhắc",
    "Not Recommended": "Chưa nên ứng tuyển",
  };
  return labels[value] || value || "Cân nhắc";
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
}

function renderResult(payload) {
  latestResult = payload;
  const analysis = payload.analysis;
  const score = analysis.match_score ?? 0;

  emptyState.classList.add("is-hidden");
  resultContent.classList.remove("is-hidden");
  resultTitle.textContent = payload.normalized_job_description?.job_title || "Kết quả phân tích";
  scoreRing.style.setProperty("--score", score);
  scoreValue.textContent = score;
<<<<<<< HEAD
  recommendation.textContent = translateLabel(analysis.recommendation || "Maybe");
=======
  recommendation.textContent = recommendationLabel(analysis.recommendation);
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
  recommendation.className = "recommendation";
  if (analysis.recommendation === "Apply Now") {
    recommendation.classList.add("apply");
  }
  if (analysis.recommendation === "Not Recommended") {
    recommendation.classList.add("no");
  }
  candidateSummary.textContent = analysis.candidate_profile_summary || "";
  finalAdvice.textContent = analysis.final_advice || "";
<<<<<<< HEAD
  renderQualityNotes(payload);
=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
  renderScoreBreakdown(analysis.score_breakdown);

  matchesPanel.innerHTML = [
    renderEvidence(analysis.strong_matches, "Chưa có điểm phù hợp mạnh", "strong"),
    renderEvidence(analysis.partial_matches, "Chưa có điểm phù hợp một phần", "partial"),
  ].join("");
  gapsPanel.innerHTML = renderGaps(analysis.missing_or_weak_skills);
  rewritePanel.innerHTML = [
    listHtml(analysis.cv_adjustment_suggestions?.what_to_emphasize, "Chưa có điểm cần nhấn mạnh"),
    listHtml(analysis.rewritten_cv_bullet_points, "Chưa có bullet gợi ý"),
    listHtml(analysis.suggested_learning_or_preparation_areas, "Chưa có mục cần chuẩn bị"),
  ].join("");
  interviewPanel.innerHTML = listHtml(analysis.interview_questions, "Chưa có câu hỏi phỏng vấn");
  copySummary.disabled = false;
  downloadJson.disabled = false;
}

<<<<<<< HEAD
function setTopCVBusy(isBusy) {
  topcvSearchButton.disabled = isBusy;
  topcvSearchButton.innerHTML = isBusy
    ? `<i class="bi bi-arrow-repeat button-glyph" aria-hidden="true"></i>Đang tìm...`
    : `<i class="bi bi-search" aria-hidden="true"></i>Tìm từ CV`;
  topcvSearchButton.classList.toggle("is-loading", isBusy);
}

function renderTopCVResults(payload) {
  latestJobPayload = payload;
  topcvResultsSection.classList.remove("is-hidden");
  topcvOpenSearch.href = payload.search_url || "#";
  topcvOpenSearch.classList.toggle("is-hidden", !payload.search_url);

  const warnings = payload.warnings || [];
  const suggestions = payload.suggested_keywords?.length ? `Gợi ý: ${payload.suggested_keywords.slice(0, 4).join(", ")}. ` : "";
  const analyzedCount = (payload.results || []).filter((job) => job.analysis_status === "ready").length;
  const analyzedText = analyzedCount ? `Đã phân tích ${analyzedCount} việc làm. ` : "";
  topcvSearchStatus.textContent = warnings.length
    ? `${suggestions}${analyzedText}${warnings.join(" ")}`
    : `${suggestions}${analyzedText}Tìm thấy ${payload.results.length} việc làm.`;

  if (!payload.results.length) {
    topcvResults.innerHTML = itemHtml(
      "Chưa đọc được việc làm từ các nguồn đã chọn",
      "Bạn có thể mở link tìm kiếm gốc hoặc thử ít nguồn hơn.",
      ""
    );
    return;
  }

  topcvResults.innerHTML = payload.results
    .map((job, index) => {
      const meta = [job.source_label || sourceLabel(job.source), job.company_name, job.location, job.salary].filter(Boolean).join(" • ");
      const reasons = (job.fit_reasons || []).map((reason) => `<span class="tag strong">${escapeHtml(reason)}</span>`).join("");
      const canViewAnalysis = job.analysis_status === "ready" && job.analysis && job.normalized_job_description;
      const analysisBadge = canViewAnalysis
        ? `<span class="analysis-pill">AI ${escapeHtml(job.analysis.match_score)}/100</span>`
        : job.analysis_status === "failed"
          ? `<span class="tag partial">Phân tích lỗi</span>`
          : "";
      const analysisButton = canViewAnalysis
        ? `<button class="btn btn-sm btn-primary topcv-analysis-button" type="button" data-job-index="${index}">
            <i class="bi bi-graph-up-arrow" aria-hidden="true"></i>
            Xem phân tích
          </button>`
        : "";
      const detailText = job.detail_text
        ? `<details class="job-detail">
            <summary>Thông tin dùng để phân tích</summary>
            <p>${escapeHtml(job.detail_text)}</p>
          </details>`
        : "";
      return `
        <article class="job-card">
          <div class="job-score">${escapeHtml(job.fit_score)}</div>
          <div class="job-card-body">
            <div class="job-title-row">
              <h3>${escapeHtml(job.title)}</h3>
              ${analysisBadge}
            </div>
            ${meta ? `<p class="job-meta">${escapeHtml(meta)}</p>` : ""}
            ${job.snippet ? `<p>${escapeHtml(job.snippet)}</p>` : ""}
            <div class="job-reasons">${reasons}</div>
            ${detailText}
            <div class="job-actions">
              ${analysisButton}
              <a class="btn btn-sm btn-outline-primary" href="${escapeHtml(job.url)}" target="_blank" rel="noopener noreferrer">
                Xem trên ${escapeHtml(job.source_label || sourceLabel(job.source))}
              </a>
            </div>
          </div>
        </article>
      `;
    })
    .join("");

  topcvResults.querySelectorAll(".topcv-analysis-button").forEach((button) => {
    button.addEventListener("click", () => {
      const job = latestJobPayload?.results?.[Number(button.dataset.jobIndex)];
      if (!job?.analysis || !job?.normalized_job_description) {
        showAlert("Chưa có dữ liệu phân tích cho việc làm này.");
        return;
      }
      renderResult({
        normalized_job_description: job.normalized_job_description,
        analysis: job.analysis,
      });
      resultTitle.textContent = job.title || resultTitle.textContent;
      document.querySelector(".results-panel")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
  animateDynamicCards();
}

=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
async function uploadCvFile(file) {
  const data = new FormData();
  data.append("file", file);
  fileStatus.textContent = "Đang đọc tệp...";
  const response = await fetch(endpoint("/files/extract"), {
    method: "POST",
    headers: headers(false),
    body: data,
  });
  if (!response.ok) {
<<<<<<< HEAD
    throw new Error(await readError(response));
  }
  const extracted = await response.json();
  cvText.value = extracted.text || "";
  updateCounters();
=======
    throw await readError(response);
  }
  const extracted = await response.json();
  cvText.value = extracted.text || "";
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
  fileStatus.textContent = `${extracted.filename}: ${extracted.character_count} ký tự`;
  if (extracted.warnings?.length) {
    fileStatus.textContent += ` (${extracted.warnings.join("; ")})`;
  }
}

<<<<<<< HEAD
function setJdMode(mode) {
  jdMode = mode;
  document.querySelectorAll(".segment").forEach((item) => {
    item.classList.toggle("is-active", item.dataset.mode === mode);
  });
  const useUrl = jdMode === "url";
  jdText.classList.toggle("is-hidden", useUrl);
  jdUrl.classList.toggle("is-hidden", !useUrl);
  jdText.required = !useUrl;
  jdUrl.required = useUrl;
  jdSourceNote.textContent = useUrl ? "URL JD" : "Văn bản JD";
  updateCounters();
}

function validateSubmission() {
  const hasKey = Boolean(accessCode.value.trim());
  if (cvText.value.trim().length < 20) {
    showAlert("CV cần tối thiểu 20 ký tự để phân tích.");
    return false;
  }
  if (jdMode === "text" && jdText.value.trim().length < 20) {
    showAlert("JD quá ngắn. Hãy dán mô tả công việc đầy đủ hơn.");
    return false;
  }
  if (jdMode === "url" && !jdUrl.value.trim()) {
    showAlert("Hãy nhập URL JD hợp lệ.");
    return false;
  }
  if (!hasKey && runtimeConfig && !runtimeConfig.public_demo_enabled && runtimeConfig.private_api_key_required) {
    showAlert("Demo đang tắt. Hãy nhập mã truy cập để dùng API riêng.");
    return false;
  }
  return true;
}

document.querySelectorAll(".segment").forEach((button) => {
  button.addEventListener("click", () => {
    setJdMode(button.dataset.mode);
=======
document.querySelectorAll(".segment").forEach((button) => {
  button.addEventListener("click", () => {
    jdMode = button.dataset.mode;
    document.querySelectorAll(".segment").forEach((item) => item.classList.remove("is-active"));
    button.classList.add("is-active");
    const useUrl = jdMode === "url";
    jdText.classList.toggle("is-hidden", useUrl);
    jdUrl.classList.toggle("is-hidden", !useUrl);
    jdText.required = !useUrl;
    jdUrl.required = useUrl;
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
  });
});

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    const tab = button.dataset.tab;
    document.querySelectorAll(".tab").forEach((item) => item.classList.remove("is-active"));
    button.classList.add("is-active");
    document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.add("is-hidden"));
    document.querySelector(`#${tab}-panel`).classList.remove("is-hidden");
  });
});

cvFile.addEventListener("change", async () => {
  clearAlert();
  const file = cvFile.files?.[0];
  if (!file) {
    return;
  }
  try {
    await uploadCvFile(file);
  } catch (error) {
    fileStatus.textContent = "";
<<<<<<< HEAD
    showAlert(error.message);
=======
    showAlert(error.message || error);
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
  }
});

accessCode.addEventListener("input", () => {
<<<<<<< HEAD
  updateModeChip();
});

cvText.addEventListener("input", updateCounters);
jdText.addEventListener("input", updateCounters);
jdUrl.addEventListener("input", updateCounters);

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearAlert();

  if (!validateSubmission()) {
    return;
  }

  setBusy(true);

  const payload = {
    cv_text: cvText.value.trim(),
    job_description: jdMode === "text" ? jdText.value.trim() : null,
    job_url: jdMode === "url" ? jdUrl.value.trim() : null,
    source_type: jdMode === "url" ? "url" : "text",
    user_preferences: userPreferences.value.trim() || null,
=======
  modeChip.textContent = accessCode.value.trim() ? "Riêng tư" : "Demo";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearAlert();
  setBusy(true);

  const payload = {
    cv_text: cvText.value,
    job_description: jdMode === "text" ? jdText.value : null,
    job_url: jdMode === "url" ? jdUrl.value : null,
    source_type: jdMode === "url" ? "url" : "text",
    user_preferences: userPreferences.value || null,
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
    output_language: outputLanguage.value,
  };

  try {
    const response = await fetch(endpoint("/analyze/full"), {
      method: "POST",
      headers: headers(true),
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
<<<<<<< HEAD
      throw new Error(await readError(response));
    }
    renderResult(await response.json());
  } catch (error) {
    showAlert(error.message || "Không thể phân tích lúc này.");
=======
      throw await readError(response);
    }
    renderResult(await response.json());
  } catch (error) {
    showAlert(error.message || error);
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
  } finally {
    setBusy(false);
  }
});

<<<<<<< HEAD
topcvSearchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  clearAlert();

  const keyword = topcvKeyword.value.trim();
  const cv = cvText.value.trim();
  const sources = selectedJobSources();
  const hasKey = Boolean(accessCode.value.trim());
  if (!hasKey && runtimeConfig && !runtimeConfig.public_demo_enabled && runtimeConfig.private_api_key_required) {
    topcvSearchStatus.textContent = "Demo đang tắt. Hãy nhập mã truy cập trước khi tìm việc.";
    return;
  }
  if (keyword && keyword.length < 2) {
    topcvSearchStatus.textContent = "Từ khóa cần ít nhất 2 ký tự.";
    return;
  }
  if (!keyword && cv.length < 20) {
    topcvSearchStatus.textContent = "Hãy dán hoặc tải CV trước, hoặc nhập từ khóa tìm kiếm.";
    return;
  }

  setTopCVBusy(true);
  topcvSearchStatus.textContent =
    cv.length >= 20 ? "Đang tìm và phân tích việc làm từ các nguồn đã chọn..." : "Đang tìm việc từ các nguồn đã chọn...";

  try {
    const shouldAnalyze = cv.length >= 20;
    const response = await fetch(endpoint(keyword ? "/jobs/search" : "/jobs/recommend"), {
      method: "POST",
      headers: headers(true),
      body: JSON.stringify(
        keyword
          ? {
              keyword,
              location: topcvLocation.value.trim() || null,
              sources,
              cv_text: cv || null,
              limit: 8,
              analyze_results: shouldAnalyze,
              analyze_limit: 3,
              output_language: outputLanguage.value,
              user_preferences: userPreferences.value.trim() || null,
            }
          : {
              location: topcvLocation.value.trim() || null,
              sources,
              cv_text: cv,
              limit: 8,
              analyze_results: true,
              analyze_limit: 3,
              output_language: outputLanguage.value,
              user_preferences: userPreferences.value.trim() || null,
            }
      ),
    });
    if (!response.ok) {
      throw new Error(await readError(response));
    }
    renderTopCVResults(await response.json());
  } catch (error) {
    topcvSearchStatus.textContent = "";
    showAlert(error.message || "Không thể tìm việc lúc này.");
  } finally {
    setTopCVBusy(false);
  }
});

clearButton.addEventListener("click", () => {
  form.reset();
  setJdMode("text");
  fileStatus.textContent = "";
  latestResult = null;
  latestJobPayload = null;
  clearAlert();
  resultContent.classList.add("is-hidden");
  emptyState.classList.remove("is-hidden");
  qualityStrip.classList.add("is-hidden");
  qualityStrip.textContent = "";
  resultTitle.textContent = "Chưa có phân tích";
  copySummary.disabled = true;
  downloadJson.disabled = true;
  updateModeChip();
  updateCounters();
  topcvSearchStatus.textContent = "";
  topcvResultsSection.classList.add("is-hidden");
  topcvResults.innerHTML = "";
=======
clearButton.addEventListener("click", () => {
  form.reset();
  fileStatus.textContent = "";
  latestResult = null;
  clearAlert();
  resultContent.classList.add("is-hidden");
  emptyState.classList.remove("is-hidden");
  resultTitle.textContent = "Chưa có phân tích";
  copySummary.disabled = true;
  downloadJson.disabled = true;
  modeChip.textContent = "Demo";
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
});

copySummary.addEventListener("click", async () => {
  if (!latestResult) {
    return;
  }
  const analysis = latestResult.analysis;
  const text = [
<<<<<<< HEAD
    `Điểm: ${analysis.match_score}/100`,
    `Khuyến nghị: ${translateLabel(analysis.recommendation)}`,
=======
    `Score: ${analysis.match_score}/100`,
    `Recommendation: ${analysis.recommendation}`,
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
    analysis.candidate_profile_summary,
    analysis.final_advice,
  ]
    .filter(Boolean)
    .join("\n");
  await navigator.clipboard.writeText(text);
});

downloadJson.addEventListener("click", () => {
  if (!latestResult) {
    return;
  }
  const blob = new Blob([JSON.stringify(latestResult, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "job-fit-analysis.json";
  link.click();
  URL.revokeObjectURL(url);
});
<<<<<<< HEAD

function initMotion() {
  if (!window.gsap || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return;
  }
  const { gsap } = window;
  if (window.ScrollTrigger) {
    gsap.registerPlugin(window.ScrollTrigger);
  }

  gsap.from(".topbar", {
    y: -18,
    opacity: 0,
    duration: 0.7,
    ease: "power3.out",
  });
  gsap.from(".hero-copy > *", {
    y: 26,
    opacity: 0,
    stagger: 0.08,
    duration: 0.85,
    ease: "power3.out",
    delay: 0.08,
  });
  gsap.from(".bento-card, .workflow-accordion article", {
    y: 18,
    opacity: 0,
    scale: 0.96,
    stagger: 0.05,
    duration: 0.7,
    ease: "power3.out",
    delay: 0.18,
  });
  gsap.from(".input-panel", {
    y: 24,
    opacity: 0,
    scale: 0.985,
    duration: 0.8,
    ease: "power3.out",
    delay: 0.08,
  });
  gsap.from(".results-panel", {
    y: 30,
    opacity: 0,
    scale: 0.985,
    duration: 0.8,
    ease: "power3.out",
    delay: 0.18,
  });
  gsap.from(".signal-tile", {
    y: 14,
    opacity: 0,
    stagger: 0.06,
    duration: 0.55,
    ease: "power2.out",
    delay: 0.18,
  });

  if (window.ScrollTrigger) {
    gsap.to(".scrub-word", {
      opacity: 1,
      stagger: 0.06,
      ease: "none",
      scrollTrigger: {
        trigger: ".experience-hero",
        start: "top 24%",
        end: "bottom 46%",
        scrub: true,
      },
    });
    gsap.fromTo(
      ".hero-image-tile",
      { scale: 0.86, opacity: 0.72 },
      {
        scale: 1,
        opacity: 1,
        ease: "none",
        scrollTrigger: {
          trigger: ".experience-hero",
          start: "top top",
          end: "bottom 42%",
          scrub: true,
        },
      }
    );
    gsap.utils.toArray(".field-group, .topcv-search-block, .metric, .item").forEach((element) => {
      gsap.from(element, {
        scrollTrigger: {
          trigger: element,
          start: "top 88%",
          toggleActions: "play none none reverse",
        },
        y: 18,
        opacity: 0,
        duration: 0.55,
        ease: "power2.out",
      });
    });
  }
}

function animateDynamicCards() {
  if (!window.gsap || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return;
  }
  window.gsap.from(".job-card", {
    y: 24,
    opacity: 0,
    scale: 0.98,
    stagger: 0.05,
    duration: 0.55,
    ease: "power2.out",
  });
}

setJdMode("text");
updateCounters();
loadRuntimeConfig();
initMotion();
=======
>>>>>>> 1abd64238dd59fa1eea4d5d339a8a961b005c144
