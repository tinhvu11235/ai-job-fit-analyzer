const form = document.querySelector("#analysis-form");
const cvText = document.querySelector("#cv-text");
const cvFile = document.querySelector("#cv-file");
const jdText = document.querySelector("#jd-text");
const jdUrl = document.querySelector("#jd-url");
const accessCode = document.querySelector("#access-code");
const outputLanguage = document.querySelector("#output-language");
const userPreferences = document.querySelector("#user-preferences");
const analyzeButton = document.querySelector("#analyze-button");
const clearButton = document.querySelector("#clear-button");
const fileStatus = document.querySelector("#file-status");
const modeChip = document.querySelector("#mode-chip");
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
const matchesPanel = document.querySelector("#matches-panel");
const gapsPanel = document.querySelector("#gaps-panel");
const rewritePanel = document.querySelector("#rewrite-panel");
const interviewPanel = document.querySelector("#interview-panel");
const copySummary = document.querySelector("#copy-summary");
const downloadJson = document.querySelector("#download-json");

let jdMode = "text";
let latestResult = null;

function endpoint(path) {
  const key = accessCode.value.trim();
  if (key) {
    return `/api/v1${path}`;
  }
  return `/api/v1/demo${path}`;
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

function showAlert(message) {
  alertBox.textContent = message;
  alertBox.classList.remove("is-hidden");
}

function clearAlert() {
  alertBox.textContent = "";
  alertBox.classList.add("is-hidden");
}

function setBusy(isBusy) {
  analyzeButton.disabled = isBusy;
  analyzeButton.textContent = isBusy ? "Dang phan tich..." : "Phan tich";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function readError(response) {
  try {
    const body = await response.json();
    if (Array.isArray(body.detail)) {
      return body.detail.map((item) => item.msg || JSON.stringify(item)).join("; ");
    }
    return body.detail || body.message || response.statusText;
  } catch {
    return response.statusText;
  }
}

function itemHtml(title, body, meta, tone = "") {
  const tag = meta ? `<span class="tag ${tone}">${escapeHtml(meta)}</span>` : "";
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
    return itemHtml("Chua thay khoang trong lon", "", "");
  }
  return items
    .map((item) => {
      return itemHtml(item.requirement, item.why_it_matters, item.evidence_status, "partial");
    })
    .join("");
}

function renderScoreBreakdown(breakdown) {
  const labels = {
    must_have_technical_skills: "Ky nang bat buoc",
    relevant_experience: "Kinh nghiem lien quan",
    responsibility_alignment: "Trach nhiem cong viec",
    seniority_fit: "Cap bac",
    domain_fit: "Linh vuc",
    user_preferences_fit: "Uu tien ca nhan",
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

function renderResult(payload) {
  latestResult = payload;
  const analysis = payload.analysis;
  const score = analysis.match_score ?? 0;

  emptyState.classList.add("is-hidden");
  resultContent.classList.remove("is-hidden");
  resultTitle.textContent = payload.normalized_job_description?.job_title || "Ket qua phan tich";
  scoreRing.style.setProperty("--score", score);
  scoreValue.textContent = score;
  recommendation.textContent = analysis.recommendation || "Maybe";
  recommendation.className = "recommendation";
  if (analysis.recommendation === "Apply Now") {
    recommendation.classList.add("apply");
  }
  if (analysis.recommendation === "Not Recommended") {
    recommendation.classList.add("no");
  }
  candidateSummary.textContent = analysis.candidate_profile_summary || "";
  finalAdvice.textContent = analysis.final_advice || "";
  renderScoreBreakdown(analysis.score_breakdown);

  matchesPanel.innerHTML = [
    renderEvidence(analysis.strong_matches, "Chua co diem phu hop manh", "strong"),
    renderEvidence(analysis.partial_matches, "Chua co diem phu hop mot phan", "partial"),
  ].join("");
  gapsPanel.innerHTML = renderGaps(analysis.missing_or_weak_skills);
  rewritePanel.innerHTML = [
    listHtml(analysis.cv_adjustment_suggestions?.what_to_emphasize, "Chua co diem can nhan manh"),
    listHtml(analysis.rewritten_cv_bullet_points, "Chua co bullet goi y"),
    listHtml(analysis.suggested_learning_or_preparation_areas, "Chua co muc can chuan bi"),
  ].join("");
  interviewPanel.innerHTML = listHtml(analysis.interview_questions, "Chua co cau hoi phong van");
  copySummary.disabled = false;
  downloadJson.disabled = false;
}

async function uploadCvFile(file) {
  const data = new FormData();
  data.append("file", file);
  fileStatus.textContent = "Dang doc tep...";
  const response = await fetch(endpoint("/files/extract"), {
    method: "POST",
    headers: headers(false),
    body: data,
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const extracted = await response.json();
  cvText.value = extracted.text || "";
  fileStatus.textContent = `${extracted.filename}: ${extracted.character_count} ky tu`;
  if (extracted.warnings?.length) {
    fileStatus.textContent += ` (${extracted.warnings.join("; ")})`;
  }
}

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
    showAlert(error.message);
  }
});

accessCode.addEventListener("input", () => {
  modeChip.textContent = accessCode.value.trim() ? "Private" : "Demo";
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
    output_language: outputLanguage.value,
  };

  try {
    const response = await fetch(endpoint("/analyze/full"), {
      method: "POST",
      headers: headers(true),
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(await readError(response));
    }
    renderResult(await response.json());
  } catch (error) {
    showAlert(error.message || "Khong the phan tich luc nay.");
  } finally {
    setBusy(false);
  }
});

clearButton.addEventListener("click", () => {
  form.reset();
  fileStatus.textContent = "";
  latestResult = null;
  clearAlert();
  resultContent.classList.add("is-hidden");
  emptyState.classList.remove("is-hidden");
  resultTitle.textContent = "Chua co phan tich";
  copySummary.disabled = true;
  downloadJson.disabled = true;
  modeChip.textContent = "Demo";
});

copySummary.addEventListener("click", async () => {
  if (!latestResult) {
    return;
  }
  const analysis = latestResult.analysis;
  const text = [
    `Score: ${analysis.match_score}/100`,
    `Recommendation: ${analysis.recommendation}`,
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
