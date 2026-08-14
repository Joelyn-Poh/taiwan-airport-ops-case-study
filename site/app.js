const languageButtons = document.querySelectorAll("[data-set-language]");
const languageNodes = document.querySelectorAll(".lang");
const titleByLanguage = {
  en: "From Dirty Ride Data to Operations Decisions",
  zh: "從叫車髒資料到營運決策"
};

function setLanguage(language, persist = true) {
  const nextLanguage = language === "zh" ? "zh" : "en";

  document.documentElement.lang = nextLanguage === "zh" ? "zh-Hant" : "en";
  document.body.dataset.language = nextLanguage;
  document.title = titleByLanguage[nextLanguage];

  languageNodes.forEach((node) => {
    const shouldShow = node.classList.contains(`lang-${nextLanguage}`);
    node.hidden = !shouldShow;
  });

  languageButtons.forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.setLanguage === nextLanguage));
  });

  if (persist) {
    try {
      localStorage.setItem("portfolio-language", nextLanguage);
    } catch {
      // The website still works when storage is unavailable.
    }
  }
}

languageButtons.forEach((button) => {
  button.addEventListener("click", () => setLanguage(button.dataset.setLanguage));
});

const queryLanguage = new URLSearchParams(window.location.search).get("lang");
let savedLanguage = null;
try {
  savedLanguage = localStorage.getItem("portfolio-language");
} catch {
  savedLanguage = null;
}
setLanguage(queryLanguage || savedLanguage || "en", false);

const sections = [...document.querySelectorAll("main section[id]")];
const navigationLinks = [...document.querySelectorAll(".case-nav a")];

if ("IntersectionObserver" in window) {
  const sectionObserver = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];

    if (!visible) return;

    navigationLinks.forEach((link) => {
      const isActive = link.hash === `#${visible.target.id}`;
      link.classList.toggle("is-active", isActive);
      if (isActive) link.setAttribute("aria-current", "location");
      else link.removeAttribute("aria-current");
    });
  }, {
    rootMargin: "-25% 0px -60% 0px",
    threshold: [0, 0.15, 0.4]
  });

  sections.forEach((section) => sectionObserver.observe(section));
}

const copyButton = document.querySelector(".copy-code");
const copyToast = document.querySelector(".copy-toast");
let toastTimer;

function showCopyStatus(message) {
  window.clearTimeout(toastTimer);
  copyToast.textContent = message;
  copyToast.classList.add("is-visible");
  toastTimer = window.setTimeout(() => copyToast.classList.remove("is-visible"), 1800);
}

async function copyCode(button) {
  const target = document.getElementById(button.dataset.copyTarget);
  const language = document.body.dataset.language;

  if (!target) {
    showCopyStatus(language === "zh" ? "找不到程式碼內容" : "Code block not found");
    return;
  }

  try {
    await navigator.clipboard.writeText(target.innerText);
    showCopyStatus(language === "zh" ? "SQL 已複製" : "SQL copied");
  } catch {
    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(target);
    selection.removeAllRanges();
    selection.addRange(range);
    showCopyStatus(language === "zh" ? "請按 Ctrl+C 複製" : "Press Ctrl+C to copy");
  }
}

copyButton?.addEventListener("click", () => copyCode(copyButton));
