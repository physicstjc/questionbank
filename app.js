const state = {
  syllabus: [],
  questions: [],
  filtered: [],
  selectedId: null,
  selectedQuestion: null,
  currentPdfUrl: "",
};

const topicFilter = document.querySelector("#topicFilter");
const loFilter = document.querySelector("#loFilter");
const schoolFilter = document.querySelector("#schoolFilter");
const paperFilter = document.querySelector("#paperFilter");
const yearFilter = document.querySelector("#yearFilter");
const searchInput = document.querySelector("#searchInput");
const questionList = document.querySelector("#questionList");
const resultCount = document.querySelector("#resultCount");
const activeClass = document.querySelector("#activeClass");
const stats = document.querySelector("#stats");
const pdfFrame = document.querySelector("#pdfFrame");
const viewerTitle = document.querySelector("#viewerTitle");
const viewerSubtitle = document.querySelector("#viewerSubtitle");
const openPdf = document.querySelector("#openPdf");
const answerPdf = document.querySelector("#answerPdf");
const appShell = document.querySelector(".app-shell");
const layoutResizer = document.querySelector("#layoutResizer");

const SUBJECTS = {
  physics: {
    label: "Physics",
    syllabusUrl: "data/syllabus.json",
    questionsUrl: "data/questions.json",
  },
  chem: {
    label: "Chemistry",
    syllabusUrl: "data/chem-syllabus.json",
    questionsUrl: "data/chem-questions.json",
  },
  bio: {
    label: "Biology",
    syllabusUrl: "data/bio-syllabus.json",
    questionsUrl: "data/bio-questions.json",
  },
};

const subjectKey = document.body.dataset.subject || "physics";
const subjectConfig = SUBJECTS[subjectKey] || SUBJECTS.physics;

const layoutState = {
  pointerId: null,
  startClientX: 0,
  startClientY: 0,
  startSidebarWidth: 0,
  startSidebarHeight: 0,
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function pdfUrl(question) {
  const page = Number(question.page) || 1;
  const y = Number(question.y) || 0;
  return `${encodeURI(question.file)}#page=${page}&zoom=125,0,${y}`;
}

function answerUrl(question) {
  if (!question.answerFile) return "";
  const page = Number(question.answerPage) || 1;
  const y = Number(question.answerY) || 0;
  return `${encodeURI(question.answerFile)}#page=${page}&zoom=125,0,${y}`;
}

function populateFilters() {
  for (const topic of state.syllabus) {
    const option = document.createElement("option");
    option.value = String(topic.number);
    option.textContent = `${topic.number}. ${topic.title}`;
    topicFilter.append(option);
  }
  populateLearningOutcomes();
  populateSourceFilters();
}

function populateLearningOutcomes() {
  const selectedTopic = topicFilter.value;
  loFilter.innerHTML = '<option value="">All learning outcomes</option>';

  const topics = selectedTopic
    ? state.syllabus.filter((topic) => String(topic.number) === selectedTopic)
    : state.syllabus;

  for (const topic of topics) {
    for (const outcome of topic.learningOutcomes) {
      const option = document.createElement("option");
      option.value = outcome.code;
      option.textContent = `${outcome.code}: ${outcome.statement}`;
      loFilter.append(option);
    }
  }
}

function populateSelect(select, values, allLabel) {
  select.innerHTML = `<option value="">${allLabel}</option>`;
  for (const value of values) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    select.append(option);
  }
}

function populateSourceFilters() {
  const schools = [...new Set(state.questions.map((question) => question.schoolName).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b));
  const papers = [...new Set(state.questions.map((question) => question.paperKind).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b));
  const years = [...new Set(state.questions.map((question) => question.year).filter(Boolean))]
    .sort((a, b) => b.localeCompare(a));

  populateSelect(schoolFilter, schools, "All schools");
  populateSelect(paperFilter, papers, "All papers");
  populateSelect(yearFilter, years, "All years");
}

function matchesSearch(question, needle) {
  if (!needle) return true;
  const haystack = [
    question.schoolName,
    question.fileName,
    question.paperKind,
    question.topicTitle,
    question.learningOutcome,
    question.preview,
    question.year,
  ].join(" ").toLowerCase();
  return haystack.includes(needle);
}

function applyFilters() {
  const topic = topicFilter.value;
  const lo = loFilter.value;
  const school = schoolFilter.value;
  const paper = paperFilter.value;
  const year = yearFilter.value;
  const needle = searchInput.value.trim().toLowerCase();

  state.filtered = state.questions.filter((question) => {
    if (topic && String(question.topicNumber) !== topic) return false;
    if (lo && question.learningOutcomeCode !== lo) return false;
    if (school && question.schoolName !== school) return false;
    if (paper && question.paperKind !== paper) return false;
    if (year && question.year !== year) return false;
    return matchesSearch(question, needle);
  });

  renderList();
}

function renderList() {
  resultCount.textContent = `${state.filtered.length.toLocaleString()} question${state.filtered.length === 1 ? "" : "s"}`;
  questionList.innerHTML = "";

  if (!state.filtered.length) {
    questionList.innerHTML = '<p class="empty">No questions match the current filters.</p>';
    return;
  }

  const fragment = document.createDocumentFragment();
  for (const question of state.filtered.slice(0, 500)) {
    const card = document.createElement("article");
    card.className = `question-card${question.id === state.selectedId ? " active" : ""}`;
    card.innerHTML = `
      <button class="question-preview" type="button" data-id="${escapeHtml(question.id)}">
        <div class="card-topline">
          <span>Q${escapeHtml(question.questionNumber)} · p.${escapeHtml(question.page)}</span>
          <span class="tag">${escapeHtml(question.learningOutcomeCode || "Review")}</span>
        </div>
        <div class="source-meta">
          ${escapeHtml(question.schoolName || question.fileName)} · ${escapeHtml(question.paperKind || "Question paper")} · ${escapeHtml(question.year || "Year unknown")}
        </div>
        <p class="preview">${escapeHtml(question.preview)}</p>
        <div class="classification">
          ${escapeHtml(question.topicTitle)}
        </div>
      </button>
      <button class="answer-link${question.answerFile ? "" : " disabled"}" type="button" data-id="${escapeHtml(question.id)}" ${question.answerFile ? "" : "disabled"} aria-disabled="${question.answerFile ? "false" : "true"}">
        ${question.answerFile ? "Answer" : "No answer linked"}
      </button>
    `;
    fragment.append(card);
  }

  if (state.filtered.length > 500) {
    const note = document.createElement("p");
    note.className = "empty";
    note.textContent = "Showing the first 500 matches. Add a topic, learning outcome, or search term to narrow the list.";
    fragment.append(note);
  }

  questionList.append(fragment);
}

function selectQuestion(question) {
  state.selectedId = question.id;
  state.selectedQuestion = question;
  const url = pdfUrl(question);
  showPdf(url);
  answerPdf.disabled = !question.answerFile;
  answerPdf.setAttribute("aria-disabled", question.answerFile ? "false" : "true");
  viewerTitle.textContent = `${question.fileName} · Q${question.questionNumber}`;
  viewerSubtitle.textContent = `Question page ${question.page}, ${question.topicTitle}, LO ${question.learningOutcomeCode || "review"}`;
  activeClass.textContent = `${question.topicTitle} · LO ${question.learningOutcomeCode || "review"}`;
  renderList();
}

function showPdf(url) {
  state.currentPdfUrl = url;
  pdfFrame.src = url;
  openPdf.href = url;
  openPdf.setAttribute("aria-disabled", "false");
}

function showAnswer(question) {
  const url = answerUrl(question);
  if (!url) return;
  state.selectedId = question.id;
  state.selectedQuestion = question;
  showPdf(url);
  answerPdf.disabled = false;
  answerPdf.setAttribute("aria-disabled", "false");
  viewerTitle.textContent = `${question.answerFileName || "Answer paper"} · Q${question.questionNumber}`;
  viewerSubtitle.textContent = `Answer page ${question.answerPage || 1} for ${question.schoolName || question.fileName}`;
  activeClass.textContent = `${question.topicTitle} · LO ${question.learningOutcomeCode || "review"}`;
  renderList();
}

function isStackedLayout() {
  return window.matchMedia("(max-width: 920px)").matches;
}

function setDesktopSidebarWidth(width) {
  const minWidth = 300;
  const maxWidth = Math.max(minWidth, window.innerWidth - 380);
  const nextWidth = Math.min(Math.max(width, minWidth), maxWidth);
  appShell.style.setProperty("--sidebar-width", `${Math.round(nextWidth)}px`);
  layoutResizer.setAttribute("aria-valuenow", String(Math.round(nextWidth)));
}

function setMobileSidebarHeight(height) {
  const minHeight = 260;
  const maxHeight = Math.max(minHeight, window.innerHeight - 300);
  const nextHeight = Math.min(Math.max(height, minHeight), maxHeight);
  appShell.style.gridTemplateRows = `${Math.round(nextHeight)}px 8px minmax(320px, 1fr)`;
  layoutResizer.setAttribute("aria-valuenow", String(Math.round(nextHeight)));
}

function beginResize(event) {
  layoutState.pointerId = event.pointerId;
  layoutState.startClientX = event.clientX;
  layoutState.startClientY = event.clientY;
  layoutState.startSidebarWidth = document.querySelector(".sidebar").getBoundingClientRect().width;
  layoutState.startSidebarHeight = document.querySelector(".sidebar").getBoundingClientRect().height;
  appShell.classList.add("resizing");
  layoutResizer.setPointerCapture(event.pointerId);
}

function updateResize(event) {
  if (layoutState.pointerId !== event.pointerId) return;

  if (isStackedLayout()) {
    setMobileSidebarHeight(layoutState.startSidebarHeight + event.clientY - layoutState.startClientY);
    return;
  }

  setDesktopSidebarWidth(layoutState.startSidebarWidth + event.clientX - layoutState.startClientX);
}

function endResize(event) {
  if (layoutState.pointerId !== event.pointerId) return;
  layoutState.pointerId = null;
  appShell.classList.remove("resizing");
  layoutResizer.releasePointerCapture(event.pointerId);
}

questionList.addEventListener("click", (event) => {
  const answer = event.target.closest(".answer-link");
  if (answer) {
    const question = state.questions.find((item) => item.id === answer.dataset.id);
    if (question) showAnswer(question);
    return;
  }

  const preview = event.target.closest(".question-preview");
  if (!preview) return;
  const question = state.questions.find((item) => item.id === preview.dataset.id);
  if (question) selectQuestion(question);
});

answerPdf.addEventListener("click", () => {
  if (state.selectedQuestion) showAnswer(state.selectedQuestion);
});

topicFilter.addEventListener("change", () => {
  populateLearningOutcomes();
  applyFilters();
});
loFilter.addEventListener("change", applyFilters);
schoolFilter.addEventListener("change", applyFilters);
paperFilter.addEventListener("change", applyFilters);
yearFilter.addEventListener("change", applyFilters);
searchInput.addEventListener("input", applyFilters);
layoutResizer.addEventListener("pointerdown", beginResize);
layoutResizer.addEventListener("pointermove", updateResize);
layoutResizer.addEventListener("pointerup", endResize);
layoutResizer.addEventListener("pointercancel", endResize);
layoutResizer.addEventListener("keydown", (event) => {
  const step = event.shiftKey ? 80 : 24;
  const sidebar = document.querySelector(".sidebar").getBoundingClientRect();

  if (isStackedLayout()) {
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setMobileSidebarHeight(sidebar.height - step);
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setMobileSidebarHeight(sidebar.height + step);
    }
    return;
  }

  if (event.key === "ArrowLeft") {
    event.preventDefault();
    setDesktopSidebarWidth(sidebar.width - step);
  }
  if (event.key === "ArrowRight") {
    event.preventDefault();
    setDesktopSidebarWidth(sidebar.width + step);
  }
});

async function init() {
  const [syllabusResponse, questionResponse] = await Promise.all([
    fetch(subjectConfig.syllabusUrl),
    fetch(subjectConfig.questionsUrl),
  ]);

  state.syllabus = await syllabusResponse.json();
  const questionData = await questionResponse.json();
  state.questions = questionData.questions;

  stats.textContent = `${subjectConfig.label} question bank`;
  populateFilters();
  applyFilters();
}

init().catch((error) => {
  stats.textContent = "Could not load the question index. Run scripts/build_index.py first.";
  questionList.innerHTML = `<p class="empty">${escapeHtml(error.message)}</p>`;
});
