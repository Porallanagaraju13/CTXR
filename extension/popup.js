// CTXR Browser Popup Controller — V3 Upload & In-View Markdown preview
const LIVE_API_URL = "https://contextforge.onrender.com";
const LOCAL_API_URL = "http://127.0.0.1:8000";
let API_URL = LIVE_API_URL;  // Active backend URL (resolved at startup)

let isBackendOnline = false;
let forgedMarkdown = "";
let rawTextLength = 0;
let isActiveTabLLM = false;
let activeLLMName = "";

document.addEventListener("DOMContentLoaded", async () => {
  await checkBackendStatus();
  await checkActiveTabType();
  
  setupDragAndDrop();
  setupTabSwitcher();
  
  document.getElementById("btn-forge").addEventListener("click", forgeActiveTab);
  document.getElementById("btn-reset").addEventListener("click", resetView);
  document.getElementById("btn-copy-preview").addEventListener("click", copyPreviewToClipboard);
  document.getElementById("btn-optimize-prompt").addEventListener("click", optimizePrompt);
});

async function checkBackendStatus() {
  const statusBadge = document.getElementById("backend-status");
  
  // Try live deployed backend first, then fall back to localhost
  for (const url of [LIVE_API_URL, LOCAL_API_URL]) {
    try {
      const response = await fetch(`${url}/health`, { signal: AbortSignal.timeout(8000) });
      if (response.ok) {
        isBackendOnline = true;
        API_URL = url;
        statusBadge.textContent = url === LIVE_API_URL ? "CLOUD" : "LOCAL";
        statusBadge.className = "badge online";
        return;
      }
    } catch (err) {
      // Try next URL
    }
  }
  
  // Neither backend reachable
  isBackendOnline = false;
  statusBadge.textContent = "STANDALONE";
  statusBadge.className = "badge offline";
}

async function checkActiveTabType() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.url) return;

  const url = tab.url.toLowerCase();
  if (url.includes("chatgpt.com")) {
    isActiveTabLLM = true;
    activeLLMName = "ChatGPT";
  } else if (url.includes("claude.ai")) {
    isActiveTabLLM = true;
    activeLLMName = "Claude";
  } else if (url.includes("gemini.google.com")) {
    isActiveTabLLM = true;
    activeLLMName = "Gemini";
  } else {
    isActiveTabLLM = false;
    activeLLMName = "";
  }
}

function setupDragAndDrop() {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-upload");
  
  // Click drop zone triggers file selector
  dropZone.addEventListener("click", () => fileInput.click());
  
  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      processIngestedFile(e.target.files[0]);
    }
  });

  // Drag over states
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  ["dragleave", "drop"].forEach(event => {
    dropZone.addEventListener(event, () => {
      dropZone.classList.remove("dragover");
    });
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    if (e.dataTransfer.files.length > 0) {
      processIngestedFile(e.dataTransfer.files[0]);
    }
  });
}

function setupTabSwitcher() {
  const tabBtns = document.querySelectorAll(".tab-btn");
  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      // Remove active from all tabs and tab contents
      tabBtns.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      
      // Activate clicked tab and its content
      btn.classList.add("active");
      const targetId = btn.getAttribute("data-tab");
      document.getElementById(targetId).classList.add("active");
    });
  });
}

async function processIngestedFile(file) {
  showView("loading-view");
  updateLoadingStatus("Normalizing uploaded document...");
  
  const suffix = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
  
  if (isBackendOnline) {
    await uploadFileToBackend(file);
  } else {
    // Standalone fallback: can parse simple text files locally
    if (suffix === ".txt" || suffix === ".md") {
      const reader = new FileReader();
      reader.onload = (e) => {
        processTextLocally(e.target.result, file.name);
      };
      reader.readAsText(file);
    } else {
      showError(
        "PDF/Word parsing requires CTXR backend. " +
        "Please start the backend (python main.py web) or upload a .txt/.md file."
      );
    }
  }
}

async function uploadFileToBackend(file) {
  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("use_ai", "false");
    
    const response = await fetch(`${API_URL}/normalize`, {
      method: "POST",
      body: formData
    });
    
    if (!response.ok) {
      throw new Error("API Normalization parsing failed.");
    }
    
    const data = await response.json();
    forgedMarkdown = data.full_markdown;
    
    renderResultsView(data.metrics.savings_percentage, data.metrics.tokens_saved);
  } catch (err) {
    showError(`Upload failed: ${err.message}`);
  }
}

function processTextLocally(text, filename) {
  const clean = text
    .replace(/[ \t]+/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
    
  forgedMarkdown = `# ${filename}\n\n${clean}`;
  
  const rawTokens = Math.ceil(text.length / 4);
  const cleanTokens = Math.ceil(forgedMarkdown.length / 4);
  const saved = Math.max(0, rawTokens - cleanTokens);
  const savingsPercent = rawTokens > 0 ? Math.round((saved / rawTokens) * 100) : 0;
  
  renderResultsView(savingsPercent, saved);
}

async function forgeActiveTab() {
  showView("loading-view");
  updateLoadingStatus("Scraping and analyzing active webpage...");
  
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab || !tab.url.startsWith("http")) {
    showError("Cannot analyze non-web pages (e.g. settings or new tab page).");
    return;
  }

  try {
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: scrapePageContent
    });

    if (!result || !result.text) {
      throw new Error("No readable text found on this page.");
    }

    rawTextLength = result.text.length;
    
    if (isBackendOnline) {
      await processViaBackend(result.text, result.title, tab.url);
    } else {
      processTextLocally(result.text, result.title);
    }
  } catch (err) {
    showError(`Web scrape failed: ${err.message}`);
  }
}

function scrapePageContent() {
  const title = document.title;
  let text = "";
  
  if (window.location.hostname.includes("youtube.com")) {
    const descriptionElement = document.querySelector("#description-inner");
    const descText = descriptionElement ? descriptionElement.innerText : "";
    text = `YouTube Video Page: ${title}\n\nDescription:\n${descText}`;
  } 
  else if (window.location.hostname.includes("github.com")) {
    const fileArea = document.querySelector("table.files") || document.querySelector("[aria-labelledby='folders-and-files']");
    const files = fileArea ? fileArea.innerText : "";
    text = `GitHub Repository Context: ${title}\n\nFile Listings:\n${files}`;
  } 
  else {
    const paragraphs = Array.from(document.querySelectorAll("h1, h2, h3, p, li, table"));
    text = paragraphs
      .map(p => {
        if (p.tagName.startsWith("H")) {
          const level = p.tagName[1];
          return `${"#".repeat(level)} ${p.innerText.trim()}`;
        }
        return p.innerText.trim();
      })
      .filter(t => t.length > 0)
      .join("\n\n");
  }

  return { title, text };
}

async function processViaBackend(text, title, url) {
  const blob = new Blob([text], { type: "text/plain" });
  const file = new File([blob], `${title.replace(/[^a-z0-9]/gi, '_')}.txt`);
  await uploadFileToBackend(file);
}

function renderResultsView(savingsPercent, savedCount) {
  document.getElementById("metric-savings").textContent = `${savingsPercent}%`;
  document.getElementById("metric-saved-count").textContent = savedCount.toLocaleString();
  
  // Populate the GFM Markdown preview container
  const previewArea = document.getElementById("markdown-preview");
  previewArea.value = forgedMarkdown;
  
  const actionBtn = document.getElementById("btn-paste-inject");
  
  if (isActiveTabLLM) {
    actionBtn.textContent = `Send to ${activeLLMName}`;
    actionBtn.onclick = injectContextIntoActiveLLM;
  } else {
    actionBtn.textContent = "Forge & Copy Context";
    actionBtn.onclick = copyToClipboardOnly;
  }
  
  showView("results-view");
}

// ── Prompt Optimization ─────────────────────────────────────────
let lastOptimizationTechniques = [];

async function optimizePrompt() {
  const promptInput = document.getElementById("prompt-input");
  const promptText = promptInput.value.trim();
  
  if (!promptText) {
    alert("Please paste a prompt to optimize.");
    return;
  }
  
  showView("loading-view");
  updateLoadingStatus("Optimizing prompt for token efficiency...");
  
  if (isBackendOnline) {
    await optimizePromptViaBackend(promptText);
  } else {
    optimizePromptLocally(promptText);
  }
}

async function optimizePromptViaBackend(promptText) {
  try {
    const formData = new FormData();
    formData.append("prompt", promptText);
    formData.append("use_ai", "true");
    
    const response = await fetch(`${API_URL}/optimize-prompt`, {
      method: "POST",
      body: formData
    });
    
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || "Prompt optimization failed.");
    }
    
    const data = await response.json();
    forgedMarkdown = data.optimized_prompt;
    lastOptimizationTechniques = data.optimization_techniques || [];
    
    renderResultsView(data.metrics.savings_percentage, data.metrics.tokens_saved);
    renderTechniquesBadges(lastOptimizationTechniques);
  } catch (err) {
    showError(`Optimization failed: ${err.message}`);
  }
}

function optimizePromptLocally(promptText) {
  // Standalone fallback: basic rule-based compression
  let result = promptText;
  const techniques = [];
  
  // Filler word removal
  const fillerPatterns = [
    [/\b[Pp]lease\s+/g, ""],
    [/\b[Cc]ould you\s+(?:please\s+)?/g, ""],
    [/\b[Cc]an you\s+(?:please\s+)?/g, ""],
    [/\b[Ww]ould you\s+(?:please\s+)?/g, ""],
    [/\bI would like you to\s+/gi, ""],
    [/\bI want you to\s+/gi, ""],
    [/\bI need you to\s+/gi, ""],
    [/\b[Kk]indly\s+/g, ""],
    [/\bjust\s+/gi, ""],
    [/\bbasically\s+/gi, ""],
    [/\bactually\s+/gi, ""],
  ];
  const beforeFiller = result;
  fillerPatterns.forEach(([pattern, replacement]) => {
    result = result.replace(pattern, replacement);
  });
  if (result !== beforeFiller) techniques.push("Filler word removal");
  
  // Redundant phrase compression
  const redundantPhrases = [
    [/\bin order to\b/gi, "To"],
    [/\bdue to the fact that\b/gi, "Because"],
    [/\bfor the purpose of\b/gi, "To"],
    [/\bin the event that\b/gi, "If"],
    [/\bit is important to note that\b/gi, "Note:"],
    [/\bit should be noted that\b/gi, "Note:"],
    [/\bmake sure (?:that|to)\b/gi, "Ensure"],
    [/\ball of the\b/gi, "All"],
    [/\ba lot of\b/gi, "Many"],
    [/\bis able to\b/gi, "Can"],
    [/\bhas the ability to\b/gi, "Can"],
  ];
  const beforeRedundant = result;
  redundantPhrases.forEach(([pattern, replacement]) => {
    result = result.replace(pattern, replacement);
  });
  if (result !== beforeRedundant) techniques.push("Redundant phrase compression");
  
  // Markdown structuring
  const beforeMarkdown = result;
  const mdLines = result.split("\n");
  const mdResult = [];
  for (let i = 0; i < mdLines.length; i++) {
    const stripped = mdLines[i].trim();
    // Skip already-formatted markdown headings
    if (stripped.startsWith("#")) { mdResult.push(mdLines[i]); continue; }
    // Detect section labels: "Section Name:" on its own line
    const colonMatch = stripped.match(/^([A-Z][A-Za-z0-9 /&,]{2,50}):\s*$/);
    if (colonMatch) { mdResult.push(`## ${colonMatch[1].trim()}`); continue; }
    // Detect numbered instructions: "1. Do X" or "1) Do X"
    const numMatch = stripped.match(/^(\d+)[.)]\s+(.+)$/);
    if (numMatch) { mdResult.push(`${numMatch[1]}. ${numMatch[2]}`); continue; }
    // Keep everything else as-is
    mdResult.push(mdLines[i]);
  }
  result = mdResult.join("\n");
  if (result !== beforeMarkdown) techniques.push("Markdown structuring");
  
  // Whitespace normalization
  result = result.replace(/[ \t]+/g, " ").replace(/\n{3,}/g, "\n\n").trim();
  techniques.push("Whitespace normalization");
  
  // Capitalize first character if needed
  if (result && result[0] === result[0].toLowerCase() && result[0].match(/[a-z]/)) {
    result = result[0].toUpperCase() + result.slice(1);
  }
  
  forgedMarkdown = result;
  lastOptimizationTechniques = techniques;
  
  const rawTokens = Math.ceil(promptText.length / 4);
  const cleanTokens = Math.ceil(result.length / 4);
  const saved = Math.max(0, rawTokens - cleanTokens);
  const savingsPercent = rawTokens > 0 ? Math.round((saved / rawTokens) * 100) : 0;
  
  renderResultsView(savingsPercent, saved);
  renderTechniquesBadges(techniques);
}

function renderTechniquesBadges(techniques) {
  const container = document.getElementById("techniques-container");
  const badgesDiv = document.getElementById("techniques-badges");
  
  if (techniques && techniques.length > 0) {
    badgesDiv.innerHTML = techniques
      .map(t => `<span class="technique-badge">${t}</span>`)
      .join("");
    container.classList.remove("hidden");
  } else {
    container.classList.add("hidden");
    badgesDiv.innerHTML = "";
  }
}

async function injectContextIntoActiveLLM() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab) return;
  
  const packet = forgedMarkdown;

  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: injectTextIntoLLMInput,
      args: [packet, activeLLMName]
    });
    
    const actionBtn = document.getElementById("btn-paste-inject");
    actionBtn.textContent = "✓ Sent successfully!";
    actionBtn.style.background = "#10b981";
    setTimeout(() => {
      actionBtn.textContent = `Send to ${activeLLMName}`;
      actionBtn.style.background = "linear-gradient(135deg, #06b6d4, #0891b2)";
    }, 1500);
  } catch (err) {
    copyToClipboardOnly();
  }
}

function injectTextIntoLLMInput(text, llmName) {
  let selectors = [];
  
  if (llmName === "ChatGPT") {
    selectors = ["#prompt-textarea", "textarea", "div[contenteditable='true']"];
  } else if (llmName === "Claude") {
    selectors = ["div[contenteditable='true']", ".ProseMirror", "[placeholder*='Message Claude']"];
  } else if (llmName === "Gemini") {
    selectors = ["div[contenteditable='true']", "[placeholder*='Ask Gemini']", "textarea"];
  } else {
    selectors = ["div[contenteditable='true']", "textarea"];
  }
  
  let targetInput = null;
  for (const selector of selectors) {
    targetInput = document.querySelector(selector);
    if (targetInput) break;
  }
  
  if (!targetInput) {
    throw new Error("Could not locate LLM input box.");
  }
  
  targetInput.focus();
  
  try {
    const isInserted = document.execCommand("insertText", false, text);
    if (!isInserted) {
      throw new Error("execCommand insert failed");
    }
  } catch (e) {
    if (targetInput.tagName === "TEXTAREA" || targetInput.tagName === "INPUT") {
      targetInput.value = text;
    } else {
      targetInput.innerText = text;
    }
    targetInput.dispatchEvent(new Event("input", { bubbles: true }));
    targetInput.dispatchEvent(new Event("change", { bubbles: true }));
  }

  // Auto-submit: click the send button after a brief delay for framework state to update
  setTimeout(() => {
    let sendBtn = null;
    let sendSelectors = [];

    if (llmName === "ChatGPT") {
      sendSelectors = [
        "button[data-testid='send-button']",
        "button[aria-label='Send prompt']",
        "button[aria-label='Send']",
        "form button[type='submit']",
        "button.btn-send"
      ];
    } else if (llmName === "Claude") {
      sendSelectors = [
        "button[aria-label='Send Message']",
        "button[aria-label='Send']",
        "button[type='submit']",
        "button.send-button",
        "fieldset button:last-of-type"
      ];
    } else if (llmName === "Gemini") {
      sendSelectors = [
        "button[aria-label='Send message']",
        "button.send-button",
        "button[mat-icon-button]",
        "button[aria-label='Send']"
      ];
    } else {
      sendSelectors = [
        "button[aria-label='Send']",
        "button[type='submit']",
        "button.send-button"
      ];
    }

    for (const sel of sendSelectors) {
      sendBtn = document.querySelector(sel);
      if (sendBtn && !sendBtn.disabled) break;
      sendBtn = null;
    }

    if (sendBtn) {
      sendBtn.click();
    } else {
      // Fallback: simulate Enter keypress on the input element
      const enterEvent = new KeyboardEvent("keydown", {
        key: "Enter",
        code: "Enter",
        keyCode: 13,
        which: 13,
        bubbles: true,
        cancelable: true
      });
      targetInput.dispatchEvent(enterEvent);
    }
  }, 300);
}

function copyPreviewToClipboard() {
  navigator.clipboard.writeText(forgedMarkdown).then(() => {
    const copyIndicator = document.getElementById("btn-copy-preview");
    copyIndicator.textContent = "Copied!";
    setTimeout(() => {
      copyIndicator.textContent = "Copy";
    }, 1500);
  });
}

function copyToClipboardOnly() {
  const packet = forgedMarkdown;

  navigator.clipboard.writeText(packet).then(() => {
    const actionBtn = document.getElementById("btn-paste-inject");
    const originalText = actionBtn.textContent;
    actionBtn.textContent = "✓ Copied to Clipboard!";
    actionBtn.style.background = "#10b981";
    setTimeout(() => {
      actionBtn.textContent = originalText;
      actionBtn.style.background = "linear-gradient(135deg, #06b6d4, #0891b2)";
    }, 1500);
  });
}

function updateLoadingStatus(text) {
  document.getElementById("loading-status").textContent = text;
}

function showView(viewId) {
  ["intro-view", "loading-view", "results-view"].forEach(id => {
    document.getElementById(id).classList.add("hidden");
  });
  document.getElementById(viewId).classList.remove("hidden");
}

function resetView() {
  checkBackendStatus();
  checkActiveTabType();
  const fileInput = document.getElementById("file-upload");
  fileInput.value = ""; // clear selected files
  document.getElementById("prompt-input").value = ""; // clear prompt input
  lastOptimizationTechniques = [];
  // Hide techniques badges on reset
  document.getElementById("techniques-container").classList.add("hidden");
  document.getElementById("techniques-badges").innerHTML = "";
  showView("intro-view");
}

function showError(msg) {
  showView("intro-view");
  alert(msg);
}
