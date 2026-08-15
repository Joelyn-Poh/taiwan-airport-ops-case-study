const progressBar = document.querySelector(".reading-progress span");
const sections = [...document.querySelectorAll("main section[id]")];
const navLinks = [...document.querySelectorAll(".chapter-nav a")];
const rail = document.querySelector(".chapter-rail");
const contentsToggle = document.querySelector(".contents-toggle");

function updateReadingProgress() {
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const progress = scrollable > 0 ? Math.min(window.scrollY / scrollable, 1) : 0;
  progressBar.style.width = `${progress * 100}%`;
}

function setActiveChapter(id) {
  navLinks.forEach((link) => {
    const active = link.getAttribute("href") === `#${id}`;
    link.classList.toggle("is-active", active);
    if (active) link.setAttribute("aria-current", "location");
    else link.removeAttribute("aria-current");
  });
}

const chapterObserver = new IntersectionObserver(
  (entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (visible) setActiveChapter(visible.target.id);
  },
  { rootMargin: "-18% 0px -68%", threshold: [0.05, 0.2, 0.5] }
);

sections.forEach((section) => chapterObserver.observe(section));

contentsToggle?.addEventListener("click", () => {
  const open = rail.classList.toggle("is-open");
  contentsToggle.setAttribute("aria-expanded", String(open));
});

navLinks.forEach((link) => {
  link.addEventListener("click", () => {
    rail.classList.remove("is-open");
    contentsToggle?.setAttribute("aria-expanded", "false");
  });
});

window.addEventListener("scroll", updateReadingProgress, { passive: true });
window.addEventListener("resize", updateReadingProgress);
updateReadingProgress();
