// CTXR Content Script — Inline Prompt Optimizer for LLM Chat Inputs
(function () {
  // ── Configuration ──────────────────────────────────────────────
  const LIVE_API = "https://contextforge.onrender.com";
  const LOCAL_API = "http://127.0.0.1:8000";
  let API_URL = null;

  // Detect which LLM we're on
  const host = window.location.hostname;
  let llmType = null;
  if (host.includes("chatgpt.com")) llmType = "chatgpt";
  else if (host.includes("claude.ai")) llmType = "claude";
  else if (host.includes("gemini.google.com")) llmType = "gemini";
  if (!llmType) return;

  // Per-LLM selectors for the main prompt input element
  const INPUT_SELECTORS = {
    chatgpt: ["#prompt-textarea", "div[contenteditable='true']", "textarea"],
    claude: ["div.ProseMirror[contenteditable='true']", "div[contenteditable='true']"],
    gemini: ["div.ql-editor[contenteditable='true']", "div[contenteditable='true']", "textarea"],
  };

  // ── Backend Resolution ─────────────────────────────────────────
  async function resolveBackend() {
    if (API_URL) return;
    const urls = [LIVE_API, LOCAL_API];
    const checks = urls.map(async (url) => {
      try {
        const r = await fetch(`${url}/health`, { signal: AbortSignal.timeout(4000) });
        if (r.ok) return url;
      } catch (_) {}
      throw new Error();
    });
    try {
      API_URL = await Promise.any(checks);
    } catch (_) {
      // Both failed
    }
  }

  // ── Input Helpers ──────────────────────────────────────────────
  function getInput() {
    const selectors = INPUT_SELECTORS[llmType] || [];
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el) return el;
    }
    return null;
  }

  function getInputText(el) {
    if (el.tagName === "TEXTAREA" || el.tagName === "INPUT") return el.value;
    return el.innerText || el.textContent || "";
  }

  function setInputText(el, text) {
    el.focus();
    // Select all existing content for replacement
    if (el.tagName === "TEXTAREA" || el.tagName === "INPUT") {
      el.select();
    } else {
      const sel = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(el);
      sel.removeAllRanges();
      sel.addRange(range);
    }
    // Use execCommand for framework-compatible insertion (React/Vue/Svelte state sync)
    const ok = document.execCommand("insertText", false, text);
    if (!ok) {
      if (el.tagName === "TEXTAREA" || el.tagName === "INPUT") {
        el.value = text;
      } else {
        el.textContent = text;
      }
    }
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }

  // ── CSS Injection ──────────────────────────────────────────────
  function injectStyles() {
    if (document.getElementById("ctxr-injected-styles")) return;
    const style = document.createElement("style");
    style.id = "ctxr-injected-styles";
    style.textContent = `
      @keyframes ctxr-spin {
        to { transform: rotate(360deg); }
      }
      @keyframes ctxr-fade-in {
        from { opacity: 0; transform: translateY(6px) scale(0.95); }
        to   { opacity: 1; transform: translateY(0) scale(1); }
      }

      #ctxr-opt-btn {
        position: fixed;
        z-index: 2147483647;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 5px 13px;
        border: 1px solid rgba(6, 182, 212, 0.45);
        border-radius: 18px;
        background: rgba(15, 23, 42, 0.92);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        color: #e2e8f0;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.01em;
        cursor: pointer;
        box-shadow: 0 4px 14px rgba(0,0,0,0.35), 0 0 10px rgba(6,182,212,0.1);
        transition: all 0.2s ease;
        white-space: nowrap;
        user-select: none;
        opacity: 0;
        pointer-events: none;
      }
      #ctxr-opt-btn.ctxr-visible {
        animation: ctxr-fade-in 0.3s ease forwards;
        pointer-events: auto;
      }
      #ctxr-opt-btn:hover:not(:disabled) {
        border-color: rgba(6, 182, 212, 0.8);
        box-shadow: 0 4px 18px rgba(0,0,0,0.4), 0 0 18px rgba(6,182,212,0.25);
        background: rgba(15, 23, 42, 0.98);
        transform: translateY(-1px);
      }
      #ctxr-opt-btn:active:not(:disabled) {
        transform: translateY(0);
      }
      #ctxr-opt-btn:disabled {
        cursor: wait;
        opacity: 0.85 !important;
        pointer-events: none;
      }
      #ctxr-opt-btn .ctxr-bolt {
        font-size: 13px;
        line-height: 1;
      }
      #ctxr-opt-btn .ctxr-spinner {
        display: inline-block;
        width: 12px;
        height: 12px;
        border: 2px solid rgba(6, 182, 212, 0.25);
        border-top-color: #06b6d4;
        border-radius: 50%;
        animation: ctxr-spin 0.55s linear infinite;
      }
      #ctxr-opt-btn.ctxr-success {
        border-color: rgba(16, 185, 129, 0.6) !important;
        box-shadow: 0 4px 14px rgba(0,0,0,0.3), 0 0 14px rgba(16,185,129,0.2) !important;
        color: #6ee7b7 !important;
      }
      #ctxr-opt-btn.ctxr-error {
        border-color: rgba(239, 68, 68, 0.5) !important;
        color: #fca5a5 !important;
      }
    `;
    document.head.appendChild(style);
  }

  // ── Button Creation ────────────────────────────────────────────
  const DEFAULT_HTML = '<span class="ctxr-bolt">⚡</span>Optimize';

  function ensureButton() {
    let btn = document.getElementById("ctxr-opt-btn");
    if (btn) return btn;

    btn = document.createElement("button");
    btn.id = "ctxr-opt-btn";
    btn.type = "button";
    btn.innerHTML = DEFAULT_HTML;
    // Prevent mousedown from stealing focus away from the input
    btn.addEventListener("mousedown", (e) => { e.preventDefault(); });
    btn.addEventListener("click", handleOptimize);
    document.body.appendChild(btn);
    return btn;
  }

  // ── Dynamic Positioning ────────────────────────────────────────
  // Positions the button just above the prompt input area, left-aligned
  function repositionButton() {
    const btn = document.getElementById("ctxr-opt-btn");
    if (!btn) return;

    const input = getInput();
    if (!input) {
      btn.classList.remove("ctxr-visible");
      return;
    }

    const rect = input.getBoundingClientRect();
    // Skip if input is hidden or off-screen
    if (rect.width === 0 || rect.height === 0) {
      btn.classList.remove("ctxr-visible");
      return;
    }

    const btnH = btn.offsetHeight || 30;
    let top = rect.top - btnH - 6;
    let left = rect.left;

    // If button would go above viewport, place it below the input instead
    if (top < 4) top = rect.bottom + 6;

    // Clamp to viewport
    top = Math.max(4, Math.min(top, window.innerHeight - btnH - 4));
    left = Math.max(4, left);

    btn.style.top = top + "px";
    btn.style.left = left + "px";

    if (!btn.classList.contains("ctxr-visible") && !btn.disabled) {
      btn.classList.add("ctxr-visible");
    }
  }

  // ── Local Fallback Optimizer ───────────────────────────────────
  function optimizeLocally(text) {
    let r = text;
    r = r.replace(/\bPlease\s+/gi, "");
    r = r.replace(/\bCould you\s+(?:please\s+)?/gi, "");
    r = r.replace(/\bCan you\s+(?:please\s+)?/gi, "");
    r = r.replace(/\bWould you\s+(?:please\s+)?/gi, "");
    r = r.replace(/\bI would like you to\s+/gi, "");
    r = r.replace(/\bI want you to\s+/gi, "");
    r = r.replace(/\bI need you to\s+/gi, "");
    r = r.replace(/\bKindly\s+/gi, "");
    r = r.replace(/\bin order to\b/gi, "To");
    r = r.replace(/\bdue to the fact that\b/gi, "Because");
    r = r.replace(/\bfor the purpose of\b/gi, "To");
    r = r.replace(/\bin the event that\b/gi, "If");
    r = r.replace(/\bit is important to note that\b/gi, "Note:");
    r = r.replace(/\bmake sure (?:that|to)\b/gi, "Ensure");
    r = r.replace(/\ball of the\b/gi, "All");
    r = r.replace(/\ba lot of\b/gi, "Many");
    r = r.replace(/\bis able to\b/gi, "Can");
    r = r.replace(/[ \t]+/g, " ").replace(/\n{3,}/g, "\n\n").trim();
    if (r && /^[a-z]/.test(r)) r = r[0].toUpperCase() + r.slice(1);
    return r;
  }

  // ── Click Handler ──────────────────────────────────────────────
  async function handleOptimize(e) {
    e.preventDefault();
    e.stopPropagation();

    const input = getInput();
    if (!input) return;

    const text = getInputText(input).trim();
    if (!text) return;

    const btn = document.getElementById("ctxr-opt-btn");
    if (!btn || btn.disabled) return;

    // Enter loading state
    btn.innerHTML = '<span class="ctxr-spinner"></span>Optimizing…';
    btn.disabled = true;
    btn.classList.remove("ctxr-success", "ctxr-error");

    try {
      if (!API_URL) await resolveBackend();

      let resultText = "";
      let savingsPct = 0;

      if (API_URL) {
        // ── API-powered optimization ──
        const fd = new FormData();
        fd.append("prompt", text);
        fd.append("use_ai", "true");

        const resp = await fetch(`${API_URL}/optimize-prompt`, {
          method: "POST",
          body: fd,
          signal: AbortSignal.timeout(15000),
        });
        if (!resp.ok) throw new Error("API error");

        const data = await resp.json();
        resultText = data.optimized_prompt;
        savingsPct = Math.round(data.metrics?.savings_percentage || 0);
      } else {
        // ── Offline local fallback ──
        resultText = optimizeLocally(text);
        const rawTok = Math.ceil(text.length / 4);
        const newTok = Math.ceil(resultText.length / 4);
        savingsPct = rawTok > 0 ? Math.round(((rawTok - newTok) / rawTok) * 100) : 0;
      }

      // Replace input text with optimized version
      setInputText(input, resultText);

      // Show success state
      btn.innerHTML = `<span class="ctxr-bolt">✓</span>${savingsPct}% reduced`;
      btn.classList.add("ctxr-success");

      setTimeout(() => {
        btn.innerHTML = DEFAULT_HTML;
        btn.classList.remove("ctxr-success");
        btn.classList.add("ctxr-visible");
      }, 2500);
    } catch (err) {
      // Show error state
      btn.innerHTML = '<span class="ctxr-bolt">⚠</span>Failed';
      btn.classList.add("ctxr-error");
      setTimeout(() => {
        btn.innerHTML = DEFAULT_HTML;
        btn.classList.remove("ctxr-error");
        btn.classList.add("ctxr-visible");
      }, 2000);
    } finally {
      btn.disabled = false;
    }
  }

  // ── Initialization ─────────────────────────────────────────────
  function init() {
    injectStyles();
    ensureButton();
    repositionButton();

    // Throttled MutationObserver — repositions button when DOM changes
    // (handles SPA navigation, input appearing/disappearing, layout shifts)
    let repoTimer = null;
    const observer = new MutationObserver(() => {
      ensureButton();
      if (!repoTimer) {
        repoTimer = setTimeout(() => {
          repositionButton();
          repoTimer = null;
        }, 150);
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });

    // Reposition on window resize and scroll
    window.addEventListener("resize", repositionButton);
    window.addEventListener("scroll", repositionButton, true);

    // Periodic fallback — catches SPA navigation that doesn't trigger mutations
    setInterval(() => {
      ensureButton();
      repositionButton();
    }, 3000);
  }

  // ── Boot ───────────────────────────────────────────────────────
  resolveBackend();
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => setTimeout(init, 1500));
  } else {
    setTimeout(init, 1500);
  }
})();
