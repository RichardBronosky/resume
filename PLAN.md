# Development plan

Updated: 2026-10-21. This is the current backlog, not a conversation log.
Operating rules: [AGENTS.md](AGENTS.md). Commands and setup: [USAGE.md](USAGE.md).

## Release: responsive site and unified tooling

Status: complete and publicly deployed. Bruno approved the final implementation;
release checks, push to main, Pages deployment, and live verification passed.

### Completed

- Fixed mobile container padding to match Bootstrap's 15px grid gutters.
- Made skill/interest keyword badges wrap within their columns at all widths;
  removed the conflicting offset on full-width keyword columns.
- Made proficiency labels flow and wrap with headings, and constrained the
  desktop container to account for its horizontal offset and gutters.
- Replaced the theme switch's media-query mutation with explicit theme state,
  persisted preference, and a system-preference default. Restored its original
  plain three-line top-right placement beside the GitHub artwork on desktop
  and mobile. GitHub's original ribbon is visible on mobile.
- Added executable `tools.sh` as the shared entrypoint for Make targets, variant
  and one-off tools, HTML/community rendering, and development review commands.
- Added private tailnet review lifecycle management, independent shared-Chrome
  tabs, viewport/theme checks, screenshots, overflow highlighting, and ntfy.
  Process, browser-target, and endpoint ownership prevent unrelated cleanup.
- Added opt-in layout diagnostics injected only into private server responses.
  Diagnostics default off; generated/public HTML never contains the report UI
  or its script. Reports and screenshots stay in a private local state directory.
- Updated AGENTS.md, USAGE.md, and README with the entrypoint and human review
  loop. A persistent absolute-path permission was saved for this Codex session;
  other agent harnesses still need their own grant.

### Verification

- `./tools.sh test`: 12 regression tests passed, covering route/process/tab
  isolation, diagnostics separation, command validation, and demo handoff.
- `./tools.sh review demo`: passed at 320, 376, 390, 412, 768, 1024, and 1280px.
  At the previously failing tablet widths, document scrollWidth now equals
  available content width: 753px at a 768px desktop viewport and 1009px at 1024px
  (desktop Chrome reserves 15px for its vertical scrollbar).
- Both themes switch correctly, preserve responsive media queries, and survive
  reload. Theme checks passed at the previously failing 768px and 1024px widths.
- Public HTML contains no diagnostic UI/script references. Private diagnostics,
  report delivery, start/stop/recovery, screenshots, and ntfy were exercised.
- Paper PDF remains unchanged from HEAD and is two pages. Resume source YAML
  is unchanged. One-off scope checks and Make's generator dependency check pass.

### Delivery record

- Final release checks: passed (12 regression tests, full viewport/theme demo,
  public artifact isolation, one-off scope check, generator dependencies,
  unchanged two-page PDF, and whitespace checks).
- Application release: `3752f08a9013141beb00b2d4ad89c064b0acc8ad`, pushed to main.
- [GitHub Pages deployment](https://github.com/RichardBronosky/resume/actions/runs/39689512282): succeeded.
- Live verification: fetched https://bronosky.com/resume/ after deployment;
  HTML matches the committed artifact byte for byte. Theme button, 15px mobile
  grid padding, badge wrapping, and tablet fixes are present; diagnostic markers
  are absent.
- Live HTML SHA-256: `01a6ae52b77b30824a0669173d7c4fc0d2d30313ffa161074a2db6ce67d3a934`.
- Public PDF fetched from `/resume/pdf/bruno.bronosky.resume.pdf` matches the
  local unchanged artifact byte for byte and remains two pages.
- This completion-record update changes documentation only; released site
  artifacts remain identical.

## Remaining backlog

### Portable protection for private one-offs

- Track the pre-push hook and provide an installation command for fresh clones.
- Reject private one-off content/history even when pushed through renamed
  branches, tags, or SHA-based refspecs. The current local hook checks names.
- Verify rejection against a local test remote without publishing private data.

### Portable browser setup

- Document where the machine-level `collaborative-chromium` skill comes from
  and how other agents obtain/access it.
- Document the procedure when it is unavailable, preserving the requirement
  to obtain verbatim job descriptions through the shared browser.

### Clean-checkout build environment

- Provision/document Node/npm alongside Python and LibreOffice in Nix.
- Verify setup, builds, and task-specific checks from a clean checkout.
  Entrypoint usage and existing validation commands are now documented.

### Local-file housekeeping

- Fix the root `.gitignore` theme-clone pattern by moving its inline comment
  onto a separate line.
- Choose appropriate shared ignore rules versus `.git/info/exclude` for
  machine-local notes/settings. Do not blanket-stage private local files.
- Review/archive obsolete resume copies and the unused theme clone before
  removing anything. Preserve existing personal/application notes.

### Remaining documentation drift

- Correct README's community route description: the current route serves HTML,
  while the table still describes a PDF.
- Historical local planning/conversation notes are not requirements. Check code
  and get agreement before adopting older proposals such as pinned historical
  rebuilds or a separate one-off worktree. Do not publish those private notes.
