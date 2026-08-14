---
version: 1
slug: "index-html"
primary_target: "site/index.html"
related_targets: ["site/styles.css","site/app.js"]
---

# Portfolio homepage brief

## Scope and mode

- Surface: `site/index.html`
- Mode: Experience with a Read-oriented evidence path
- Default language: English
- Alternate language: Traditional Chinese, switched in page without navigation

## Audience, job, and action

- Primary audience: Uber Taiwan Mobility hiring manager or interviewer.
- Job: understand the recommendation quickly, judge the candidate's operations reasoning, and verify the evidence.
- Primary action: inspect the SQL evidence and complete work-analysis report.
- Secondary actions: open the English summary, dashboard, tests, and GitHub repository.

## Proof and constraints

- Lead with the verified decision: the campaign creates demand but the current reward design should not be fully scaled.
- Use only verified metrics from project outputs.
- Label all operational data as synthetic and state that the project is not affiliated with Uber.
- Static HTML, CSS, and JavaScript suitable for GitHub Pages.
- Keyboard accessible, responsive, reduced-motion aware, and readable without JavaScript except for language switching enhancements.

## Chosen direction

Operations evidence dossier: a left evidence index, a central case file, and a right decision rail. The memorable moment is the data-cleaning flow where 52,222 raw orders narrow into 48,347 trusted trips before the decision is allowed to appear.

- Approved comp: `.impeccable/mocks/comp-b.png`
- Direction seed: `6ee356c8`
- The comp's invented labels and values are compositional placeholders only; implementation uses repository truth.

## Design-system inventory

| Ingredient | Commitment | Medium |
|---|---|---|
| Desktop shell | 17rem evidence index, fluid central dossier, 18rem decision rail | Semantic HTML and CSS grid |
| Mobile shell | Compact top bar, horizontal evidence navigation, single-column exhibits | Semantic HTML and CSS |
| Typography | Condensed display face for decisions; workhorse sans for prose; monospace only for SQL and measurements | Self-hosted or web font with safe fallbacks |
| Surface | Cool gray paper with deep navy ink; no decorative texture substitution | CSS color surfaces |
| Rules and tabs | 1px navy rules, squared exhibit tabs, restrained 10–14px corners | CSS and pseudo-elements |
| Status language | Safety orange for breach/decision; verification green for passed evidence | CSS tokens and inline SVG icons |
| Data-cleaning flow | Dense lines narrowing from raw orders to trusted trips, with quarantine branch | Authored responsive SVG |
| Experiment evidence | Comparison table plus proportional bars for airport conversion and D7 repeat | Semantic table and CSS bars |
| Marketplace evidence | Four-zone guardrail ledger with pass/breach states | Semantic table/list |
| Budget evidence | 139.3% execution line with planned threshold and overage | Semantic HTML and CSS |
| SQL evidence | Real snippets, step index, copy control, and links to complete SQL | Semantic code blocks and JavaScript copy action |
| Primary action | Open SQL evidence; styled as a dossier tab, not a generic pill button | Anchor plus authored SVG arrow |
| Motion | One opening chain-of-evidence trace; active exhibit marker while scrolling | CSS and IntersectionObserver |

## Unresolved decisions

- GitHub Pages will be enabled after the implementation branch is pushed and the deployment route is confirmed.
