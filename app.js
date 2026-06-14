const state = {
  book: null,
  searchIndex: null,
  selectedPage: 1,
  query: "",
  sidebarMode: "results",
  viewMode: "split",
  zoom: 1,
  normalizedPages: []
};

const els = {
  bookMeta: document.querySelector("#bookMeta"),
  searchInput: document.querySelector("#searchInput"),
  searchStatus: document.querySelector("#searchStatus"),
  resultsList: document.querySelector("#resultsList"),
  resultsTab: document.querySelector("#resultsTab"),
  indexTab: document.querySelector("#indexTab"),
  prevPage: document.querySelector("#prevPage"),
  nextPage: document.querySelector("#nextPage"),
  pageInput: document.querySelector("#pageInput"),
  pageTotal: document.querySelector("#pageTotal"),
  splitView: document.querySelector("#splitView"),
  imageView: document.querySelector("#imageView"),
  textView: document.querySelector("#textView"),
  zoomOut: document.querySelector("#zoomOut"),
  zoomIn: document.querySelector("#zoomIn"),
  zoomLabel: document.querySelector("#zoomLabel"),
  copyText: document.querySelector("#copyText"),
  pageKicker: document.querySelector("#pageKicker"),
  pageTitle: document.querySelector("#pageTitle"),
  contentGrid: document.querySelector("#contentGrid"),
  pageImage: document.querySelector("#pageImage"),
  ocrText: document.querySelector("#ocrText"),
  toast: document.querySelector("#toast")
};

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, char => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#039;"
  }[char]));
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function normalizeForSearch(text) {
  return text
    .normalize("NFC")
    .toLocaleLowerCase("ta-IN")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokenize(text) {
  return normalizeForSearch(text)
    .split(" ")
    .filter(token => token.length > 1);
}

function pageByNumber(pageNumber) {
  return state.book.pages[pageNumber - 1];
}

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("is-visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    els.toast.classList.remove("is-visible");
  }, 1800);
}

function markMatches(text, query) {
  const terms = Array.from(new Set([query.trim(), ...tokenize(query)]))
    .filter(term => term.length > 1)
    .sort((a, b) => b.length - a.length);

  if (!terms.length) {
    return escapeHtml(text);
  }

  const regex = new RegExp(terms.map(escapeRegExp).join("|"), "giu");
  let output = "";
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    output += escapeHtml(text.slice(lastIndex, match.index));
    output += `<mark>${escapeHtml(match[0])}</mark>`;
    lastIndex = match.index + match[0].length;
  }

  output += escapeHtml(text.slice(lastIndex));
  return output;
}

function snippetFor(page, query) {
  const collapsed = page.text.replace(/\s+/g, " ").trim();
  if (!collapsed) {
    return "No OCR text was found on this page.";
  }

  const normalizedCollapsed = normalizeForSearch(collapsed);
  const normalizedQuery = normalizeForSearch(query);
  const terms = tokenize(query);
  let position = normalizedQuery ? normalizedCollapsed.indexOf(normalizedQuery) : -1;

  if (position < 0) {
    for (const term of terms) {
      position = normalizedCollapsed.indexOf(term);
      if (position >= 0) break;
    }
  }

  const approxPosition = position < 0 ? 0 : Math.min(position, collapsed.length);
  const start = Math.max(0, approxPosition - 70);
  const end = Math.min(collapsed.length, approxPosition + 170);
  const prefix = start > 0 ? "..." : "";
  const suffix = end < collapsed.length ? "..." : "";

  return `${prefix}${collapsed.slice(start, end)}${suffix}`;
}

function scorePage(page, normalizedText, query, terms) {
  if (!query) return page.number === state.selectedPage ? 2 : 1;

  const normalizedQuery = normalizeForSearch(query);
  let score = 0;

  if (normalizedText.includes(normalizedQuery)) {
    score += 120;
  }

  for (const term of terms) {
    const re = new RegExp(`(^| )${escapeRegExp(term)}(?= |$)`, "gu");
    const matches = normalizedText.match(re);
    if (matches) {
      score += matches.length * 8;
    } else if (normalizedText.includes(term)) {
      score += 2;
    }
  }

  if (normalizeForSearch(page.title).includes(normalizedQuery)) {
    score += 60;
  }

  return score;
}

function searchPages() {
  const query = state.query.trim();
  const terms = tokenize(query);

  if (!query) {
    return {
      total: state.book.pages.length,
      items: state.book.pages.slice(0, 40).map(page => ({ page, score: 0 }))
    };
  }

  const candidateNumbers = new Set();
  for (const term of terms) {
    const pages = state.searchIndex.index[term];
    if (pages) {
      pages.forEach(pageNumber => candidateNumbers.add(pageNumber));
    }
  }

  if (!candidateNumbers.size) {
    state.book.pages.forEach(page => candidateNumbers.add(page.number));
  }

  const matches = [...candidateNumbers]
    .map(pageNumber => {
      const page = pageByNumber(pageNumber);
      const normalizedText = state.normalizedPages[pageNumber - 1];
      return {
        page,
        score: scorePage(page, normalizedText, query, terms)
      };
    })
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score || a.page.number - b.page.number);

  return {
    total: matches.length,
    items: matches.slice(0, 80)
  };
}

function resultButton(item) {
  const selected = item.page.number === state.selectedPage ? " is-selected" : "";
  const snippet = snippetFor(item.page, state.query);

  return `
    <button class="result-item${selected}" type="button" data-page="${item.page.number}">
      <span class="result-topline">
        <span>Page ${item.page.number}</span>
        <span>${item.page.wordCount.toLocaleString()} words</span>
      </span>
      <span class="result-title">${markMatches(item.page.title, state.query)}</span>
      <span class="result-snippet">${markMatches(snippet, state.query)}</span>
    </button>
  `;
}

function renderResults() {
  if (!state.book) return;

  const search = searchPages();
  const results = search.items;
  if (state.query.trim()) {
    const shown = results.length;
    const total = search.total;
    els.searchStatus.textContent = shown < total
      ? `Showing ${shown} of ${total} matching pages`
      : `${total} matching page${total === 1 ? "" : "s"}`;
  } else {
    els.searchStatus.textContent = "Showing the first 40 indexed pages";
  }

  if (!results.length) {
    els.resultsList.innerHTML = `<p class="empty-state">No matching pages found. Try a shorter Tamil word, an English transliteration, or browse the page index.</p>`;
    return;
  }

  els.resultsList.innerHTML = results.map(resultButton).join("");
}

function renderIndex() {
  if (!state.book) return;

  els.searchStatus.textContent = `${state.book.pages.length} pages indexed`;
  els.resultsList.innerHTML = state.book.pages.map(page => `
    <button class="result-item${page.number === state.selectedPage ? " is-selected" : ""}" type="button" data-page="${page.number}">
      <span class="result-topline">
        <span>Page ${page.number}</span>
        <span>${page.characterCount.toLocaleString()} chars</span>
      </span>
      <span class="result-title">${escapeHtml(page.title)}</span>
    </button>
  `).join("");
}

function renderSidebar() {
  if (state.sidebarMode === "index") {
    renderIndex();
  } else {
    renderResults();
  }
}

function renderPage() {
  const page = pageByNumber(state.selectedPage);
  if (!page) return;

  els.pageInput.value = String(page.number);
  els.pageKicker.textContent = `Page ${page.number}`;
  els.pageTitle.textContent = page.title;
  els.pageImage.src = page.image;
  els.pageImage.alt = `Scanned page ${page.number}`;
  els.ocrText.innerHTML = markMatches(page.text || "No OCR text was found on this page.", state.query);
  els.prevPage.disabled = page.number <= 1;
  els.nextPage.disabled = page.number >= state.book.pages.length;

  renderSidebar();
}

function setPage(pageNumber) {
  const total = state.book.pages.length;
  const nextPage = Math.min(total, Math.max(1, Number(pageNumber) || 1));
  state.selectedPage = nextPage;
  renderPage();
}

function setSidebarMode(mode) {
  state.sidebarMode = mode;
  els.resultsTab.classList.toggle("is-active", mode === "results");
  els.indexTab.classList.toggle("is-active", mode === "index");
  els.resultsTab.setAttribute("aria-selected", String(mode === "results"));
  els.indexTab.setAttribute("aria-selected", String(mode === "index"));
  renderSidebar();
}

function setViewMode(mode) {
  state.viewMode = mode;
  els.contentGrid.className = `content-grid ${mode === "split" ? "split" : mode === "image" ? "image-only" : "text-only"}`;
  els.splitView.classList.toggle("is-active", mode === "split");
  els.imageView.classList.toggle("is-active", mode === "image");
  els.textView.classList.toggle("is-active", mode === "text");
}

function setZoom(value) {
  state.zoom = Math.min(1.65, Math.max(0.75, value));
  els.contentGrid.style.setProperty("--zoom", state.zoom.toFixed(2));
  els.zoomLabel.textContent = `${Math.round(state.zoom * 100)}%`;
}

function bindEvents() {
  els.searchInput.addEventListener("input", event => {
    state.query = event.target.value;
    if (state.sidebarMode !== "results") {
      setSidebarMode("results");
    }
    renderPage();
  });

  els.resultsList.addEventListener("click", event => {
    const item = event.target.closest("[data-page]");
    if (!item) return;
    setPage(Number(item.dataset.page));
    document.querySelector(".reader").scrollIntoView({ block: "start", behavior: "smooth" });
  });

  els.resultsTab.addEventListener("click", () => setSidebarMode("results"));
  els.indexTab.addEventListener("click", () => setSidebarMode("index"));
  els.prevPage.addEventListener("click", () => setPage(state.selectedPage - 1));
  els.nextPage.addEventListener("click", () => setPage(state.selectedPage + 1));
  els.pageInput.addEventListener("change", () => setPage(els.pageInput.value));
  els.splitView.addEventListener("click", () => setViewMode("split"));
  els.imageView.addEventListener("click", () => setViewMode("image"));
  els.textView.addEventListener("click", () => setViewMode("text"));
  els.zoomOut.addEventListener("click", () => setZoom(state.zoom - 0.1));
  els.zoomIn.addEventListener("click", () => setZoom(state.zoom + 0.1));

  els.copyText.addEventListener("click", async () => {
    const page = pageByNumber(state.selectedPage);
    await navigator.clipboard.writeText(page.text || "");
    showToast(`Copied OCR text for page ${page.number}`);
  });

  window.addEventListener("keydown", event => {
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
      return;
    }

    if (event.key === "ArrowLeft") {
      setPage(state.selectedPage - 1);
    }

    if (event.key === "ArrowRight") {
      setPage(state.selectedPage + 1);
    }
  });
}

async function loadBook() {
  const [bookResponse, indexResponse] = await Promise.all([
    fetch("data/book.json", { cache: "no-store" }),
    fetch("data/search-index.json", { cache: "no-store" })
  ]);

  if (!bookResponse.ok || !indexResponse.ok) {
    throw new Error("Digitized book data is missing. Run `npm run extract` first.");
  }

  state.book = await bookResponse.json();
  state.searchIndex = await indexResponse.json();
  state.normalizedPages = state.book.pages.map(page => normalizeForSearch(`${page.title}\n${page.text}`));
}

async function init() {
  bindEvents();
  setZoom(1);

  try {
    await loadBook();
    const { metadata } = state.book;
    els.bookMeta.textContent = `${metadata.pageCount.toLocaleString()} pages · ${metadata.language} OCR`;
    els.pageTotal.textContent = `/ ${metadata.pageCount}`;
    els.pageInput.max = String(metadata.pageCount);
    setPage(1);
  } catch (error) {
    els.searchStatus.textContent = "Book data not found";
    els.resultsList.innerHTML = `<p class="empty-state">${escapeHtml(error.message)}</p>`;
    els.pageTitle.textContent = "Run OCR extraction first";
    els.ocrText.textContent = error.message;
  }
}

init();
