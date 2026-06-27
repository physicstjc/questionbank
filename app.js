const state = {
  syllabus: [],
  questions: [],
  filtered: [],
  selectedId: null,
};

const topicFilter = document.querySelector("#topicFilter");
const loFilter = document.querySelector("#loFilter");
const searchInput = document.querySelector("#searchInput");
const questionList = document.querySelector("#questionList");
const resultCount = document.querySelector("#resultCount");
const activeClass = document.querySelector("#activeClass");
const stats = document.querySelector("#stats");
const pdfFrame = document.querySelector("#pdfFrame");
const viewerTitle = document.querySelector("#viewerTitle");
const viewerSubtitle = document.querySelector("#viewerSubtitle");
const openPdf = document.querySelector("#openPdf");
const appShell = document.querySelector(".app-shell");
const layoutResizer = document.querySelector("#layoutResizer");

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

function populateFilters() {
  for (const topic of state.syllabus) {
    const option = document.createElement("option");
    option.value = String(topic.number);
    option.textContent = `${topic.number}. ${topic.title}`;
    topicFilter.append(option);
  }
  populateLearningOutcomes();
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

function matchesSearch(question, needle) {
  if (!needle) return true;
  const haystack = [
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
  const needle = searchInput.value.trim().toLowerCase();

  state.filtered = state.questions.filter((question) => {
    if (topic && String(question.topicNumber) !== topic) return false;
    if (lo && question.learningOutcomeCode !== lo) return false;
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
    const button = document.createElement("button");
    button.type = "button";
    button.className = `question-card${question.id === state.selectedId ? " active" : ""}`;
    button.dataset.id = question.id;
    button.innerHTML = `
      <div class="card-topline">
        <span>${escapeHtml(question.year)} · ${escapeHtml(question.paperKind)} · Q${escapeHtml(question.questionNumber)} · p.${escapeHtml(question.page)}</span>
        <span class="tag">${escapeHtml(question.learningOutcomeCode || "Review")}</span>
      </div>
      <p class="preview">${escapeHtml(question.preview)}</p>
      <div class="classification">
        ${escapeHtml(question.topicTitle)}<br>
        ${escapeHtml(question.learningOutcome)}
      </div>
    `;
    fragment.append(button);
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
  const url = pdfUrl(question);
  pdfFrame.src = url;
  openPdf.href = url;
  openPdf.setAttribute("aria-disabled", "false");
  viewerTitle.textContent = `${question.fileName} · Q${question.questionNumber}`;
  viewerSubtitle.textContent = `Page ${question.page}, ${question.topicTitle}, LO ${question.learningOutcomeCode || "review"}`;
  activeClass.textContent = `${question.topicTitle} · ${question.learningOutcome}`;
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
  const card = event.target.closest(".question-card");
  if (!card) return;
  const question = state.questions.find((item) => item.id === card.dataset.id);
  if (question) selectQuestion(question);
});

topicFilter.addEventListener("change", () => {
  populateLearningOutcomes();
  applyFilters();
});
loFilter.addEventListener("change", applyFilters);
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
    fetch("data/syllabus.json"),
    fetch("data/questions.json"),
  ]);

  state.syllabus = await syllabusResponse.json();
  const questionData = await questionResponse.json();
  state.questions = questionData.questions;

  stats.textContent = `${questionData.metadata.questionCount.toLocaleString()} questions classified from ${questionData.metadata.pdfCount.toLocaleString()} PDFs.`;
  populateFilters();
  applyFilters();
}

init().catch((error) => {
  stats.textContent = "Could not load the question index. Run scripts/build_index.py first.";
  questionList.innerHTML = `<p class="empty">${escapeHtml(error.message)}</p>`;
});
