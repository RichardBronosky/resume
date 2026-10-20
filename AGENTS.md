# Rules for agents working in this repo

Bruno's resume. One source of truth: `src/bruno.bronosky.resume.yaml`.
Everything else is built from it. Read this whole file before changing anything.

## Where things go

| You are doing | Branch | You may change |
| --- | --- | --- |
| Fixing or adding resume facts, tools, theme | `main` (or a `preview/<name>` branch for review) | anything except `oneoffs/` |
| Making or updating a one-off resume for one job | `oneoffs` | only `oneoffs/<your-folder>/` |

- `main` never contains `oneoffs/`. The `oneoffs` branch is main plus the
  `oneoffs/` folder and nothing else. `tools/oneoff.py check` enforces both.
- `oneoffs` merges *from* main (`git merge main`), never into it.
- **`oneoffs` is local only. Never push it anywhere**, under any name. The
  GitHub repo is public, and one-offs name the companies Bruno applies to. A
  `pre-push` hook in `.git/hooks/` refuses it; never bypass it with `--no-verify`.

## Making a one-off

```bash
git switch oneoffs && git merge main
tools/oneoff.py new 2026-10-21-acme-sre-lead --company Acme --role "SRE Lead" --url https://...
# save the job posting VERBATIM as oneoffs/<folder>/jd.txt, then edit oneoff.yaml
tools/oneoff.py build 2026-10-21-acme-sre-lead
git add oneoffs/2026-10-21-acme-sre-lead && git commit
```

`oneoffs/2026-09-22-mysql-dba-contractor/` is a finished example.

Get the posting with the shared browser (the `collaborative-chromium` skill),
not a fetch tool: fetchers get blocked by Cloudflare or return summaries.
Track applications with `tools/oneoff.py status <folder> sent` and
`tools/oneoff.py list`.

## The facts rule

A one-off may **select, reorder, and reword** what the main YAML says. It may
**not add facts**: no new numbers, tools, employers, titles, dates, or duties.
- Bullets are changed only through `jobs.<id>.top / drop / reword` in
  `oneoff.yaml`, quoting main's bullets word for word. The build fails otherwise.
- A reword keeps the meaning of its `based_on` bullet. Adding detail that
  isn't in main is adding a fact.
- `basics.summary` and `basics.label` are free text: every claim in them must
  already be in the main YAML.
- If the job needs a fact that isn't in main, stop and ask Bruno. Once he
  confirms it, add it on `main` (with `variants: [None]` if it should stay off
  the public resume), merge main into `oneoffs`, then use it with `top`.
- Never claim the degree. He didn't finish it.

## Never

- Edit `src/`, `tools/`, `themes/`, `Makefile` or `build/` on the `oneoffs` branch.
- Copy the main YAML to make a variant. Forks drift; that's what `oneoff.yaml` replaces.
- Run `resume-docx` from PATH. Use `make` or `tools/oneoff.py`; they run this
  checkout's generator.
- Hand-edit a generated PDF/DOCX/JSON. Rebuild instead.

## Building main's outputs

`make pdf` (paper), `make ats`, `make json`; web HTML via
`tools/jsonresume.sh html` (see USAGE.md). Variants: `src/variants/README.md`.
