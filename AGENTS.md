# Rules for agents working in this repo

Bruno's resume. One source of truth: `src/bruno.bronosky.resume.yaml`.
Everything else is built from it. Read this whole file before changing anything.

Current development work and acceptance criteria: [PLAN.md](PLAN.md).

## Command entrypoint

Use this checkout's executable `tools.sh` for builds and tool operations. Run
`./tools.sh help` for commands; see [USAGE.md](USAGE.md#unified-tools-entrypoint).
For persistent agent permissions, invoke the absolute path directly:
`/home/bruno/Work/resume/tools.sh <command>` (no shell wrapper or compound command).
Use `tools.sh make <target>`, `tools.sh html`, `tools.sh oneoff ...`, and
`tools.sh review ...` instead of separately invoking their implementations.
A blanket executable permission covers the exposed destructive/publishing
commands too; conversation authorization still governs their use.


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
./tools.sh oneoff new 2026-10-21-acme-sre-lead --company Acme --role "SRE Lead" --url https://...
# save the job posting VERBATIM as oneoffs/<folder>/jd.txt, then edit oneoff.yaml
./tools.sh oneoff build 2026-10-21-acme-sre-lead
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

`./tools.sh make pdf` (paper), `./tools.sh make ats`, `./tools.sh make json`;
web HTML via `./tools.sh html` (see USAGE.md). Variants: `src/variants/README.md`.

## Human development review loop

Use `./tools.sh review demo` and `./tools.sh review notify` for the standard loop.
For every UI review: develop, rebuild, verify, demo to Bruno, incorporate his
feedback, and repeat until approved. Then commit/publish as authorized and
verify the deployed result. See [USAGE.md](USAGE.md#human-development-review)
for the server and browser commands.

- Serve only generated public artifacts from `build/`, never the repo root.
  Make the review server reachable privately over the tailnet with Tailscale
  Serve; give Bruno the HTTPS tailnet URL, not just localhost. Preserve any
  existing Serve routes and do not use public Funnel for reviews.
- Open a dedicated tab in shared collaborative Chrome ("chrollab") for every
  review loop, using `--cdp 9222 --pin-tab --session <task>`. Read the
  `collaborative-chromium` skill for session/tab ownership. Bruno explicitly
  wants this shared browser for local demos too.
- Resize that tab to the viewport under review before handing it over. For
  responsive changes, check 390px and 412px widths and leave it at a phone
  size for Bruno. State the dimensions and tell him Super+0 opens chrollab.
- Provide screenshot links with `file://` URLs, as requested by Bruno.
  Screenshots supplement the interactive demo; they do not replace it.
- Record checks and review status in PLAN.md. Wait for Bruno's review before
  publishing; feedback is another iteration, not implicit approval.
