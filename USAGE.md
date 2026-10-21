# Usage

This repo generates DOCX and PDF resumes from `src/bruno.bronosky.resume.yaml`
using `nix-shell` (Python and LibreOffice are provisioned automatically — no
system Python or Docker required).

## Prerequisites

- [Nix](https://nixos.org/download) package manager. If you don't have it:
  ```bash
  sh <(curl -L https://nixos.org/nix/install) --daemon
  ```

## Generate a resume

```bash
# 1. Drop into the development shell (auto-installs the generator CLI)
nix-shell

# 2. Build the DOCX version
make docx

# 3. Build the DOCX and PDF versions
make pdf
```

Outputs are saved to `build/`.

## Publish to bronosky.com/resume/

Commit the regenerated `build/` files and push `main`; the
[Pages workflow](.github/workflows/pages.yml) deploys them. There is no
`gh-pages` branch any more. See the Publishing section of the
[README](README.md#publishing-bronoskycomresume).

The HTML theme is vendored at
[`themes/jsonresume-theme-kendall-markdown/`](themes/jsonresume-theme-kendall-markdown/)
(edit it there; `style.css` holds the responsive overrides). `tools/jsonresume.sh`
always renders with that copy, never the npm package, so it is never published
or fetched. The old standalone clone of the theme repo is no longer used.

The community page (`/resume/community/`) is a themed web page (same CSS and
header as the resume, no PDF involved) rendered from
`src/bruno.bronosky.community.md` with `node tools/community-html.cjs` and
committed as `build/bruno.bronosky.community.html`. The resume links to it
instead of a github.com URL because on Android a github.com link opens the
GitHub app.

Each output is a *variant* of the one YAML file (web, paper, ATS, one-offs);
see [`src/variants/README.md`](src/variants/README.md). `make json` writes the
JSON for each; `make ats` builds the ATS DOCX. One-off resumes for a single
job live on the `oneoffs` branch: see [AGENTS.md](AGENTS.md). The HTML is not produced by `make`. With `tools/` on `PATH` run:

```bash
PATH=$PWD/tools:$PATH ./tools/jsonresume.sh yaml_file_to_json_file
PATH=$PWD/tools:$PATH ./tools/jsonresume.sh html
```

## Unified tools entrypoint

Use `./tools.sh help` to discover the supported commands. The executable resolves
this checkout from its own location, so it also works from other directories:

```bash
/home/bruno/Work/resume/tools.sh make pdf
/home/bruno/Work/resume/tools.sh html
/home/bruno/Work/resume/tools.sh oneoff list
/home/bruno/Work/resume/tools.sh variant web
/home/bruno/Work/resume/tools.sh community
/home/bruno/Work/resume/tools.sh doctor
/home/bruno/Work/resume/tools.sh test
```

Existing Make/Python/Bash tools remain the implementations. `tools.sh make`
accepts the documented targets and an optional `VERSION=...`, rather than
arbitrary Make options or variable overrides. Other adapters include `assemble`,
`application`, and the maintained `jsonresume` HTML/serve/watch actions.

For agents, approve the absolute `tools.sh` executable path persistently and
invoke it directly, outside the sandbox when browser/network access is needed.
Do not wrap it in `bash -lc`, `python`, or compound commands. Each coding-agent
harness manages its own permission settings; a grant in one does not configure
another. The implementation is in `tools/commands.py`; approving this mutable
checkout means trusting future changes to the entrypoint and its helpers too.

A blanket entrypoint grant covers every exposed subcommand. In particular,
`make clean` deletes generated files and the virtual environment, and
`make release` publishes a GitHub release. Run them only when authorized in the
conversation. The entrypoint does not commit, push, or bypass the one-off rules.

## Human development review

```bash
/home/bruno/Work/resume/tools.sh review demo
/home/bruno/Work/resume/tools.sh review notify
```

`demo` rebuilds web JSON/HTML, rejects diagnostic code in public HTML, starts a
loopback review server, verifies its tailnet response, and opens independent
wide (1280 × 900) and mobile (390 × 844) chrollab tabs. It checks layout at
320, 376, 390, 412, 768, 1024, and 1280px, checks both themes, and prints screenshot
`file://` links and the private HTTPS demo URL. Failed checks produce a nonzero
exit status but still leave the demo ready for review. It does not send ntfy
notifications automatically; `review notify` explicitly sends the current URL
using `NTFY_SERVER`/`NTFY_TOPIC` (defaulting to the existing phone setup) and
optional `NTFY_TOKEN` or `~/.config/ntfy/token`.

The HTTP server binds to `127.0.0.1:8765` and serves only `build/`. Tailscale
Serve adds HTTPS port 8765 without replacing unrelated routes; Funnel is
refused. A matching pre-existing private route may be reused, but cleanup will
not remove it. A busy port belonging to another process is an error, not a
reason to kill that process. The shared Chromium must already be running;
read the machine's `collaborative-chromium` skill for setup and session rules.

Use the plain demo URL with `Cache-Control: no-store`; no `?review=...` query
is needed. Press Super+0 to view chrollab. Each tab has a separate owned session;
refresh recovers closed tabs without taking over unrelated tabs. Useful commands:

```bash
./tools.sh review refresh
./tools.sh review open wide
./tools.sh review resize mobile 412 915
./tools.sh review inspect mobile
./tools.sh review screenshot mobile
./tools.sh check layout
./tools.sh check themes
./tools.sh check pdf
./tools.sh check public
./tools.sh review status
```

`check pdf` reports page count and whether the artifact matches HEAD. It does
not rebuild it. `review screenshot` foregrounds the owned tab before capture.
Viewport checks restore the mobile tab's prior size, and theme checks restore
the prior choice. Report and screenshot paths are local, not public artifacts.

For a phone-only problem:

```bash
./tools.sh review diagnostics on
./tools.sh review notify
./tools.sh review reports 5
./tools.sh review diagnostics off
```

Diagnostics are **off by default**. When enabled, only private server responses
include the report button and `tools/review-diagnostics.js`. Generated files are
never instrumented. Geometry/zoom/gesture reports go to this server, not a
third-party analytics service. Reports do not include resume text. Turning
reporting off refreshes owned tabs and disables its endpoints.

PID ownership, stable browser target IDs, endpoint ownership, logs, reports,
and screenshots live in a private checkout-specific `/tmp/resume-tools-*`
directory. `review status` prints its location. Do not commit those artifacts.

Wait for Bruno's review, incorporate feedback, and repeat before publishing.
After review, clean up only managed resources:

```bash
./tools.sh review stop
```

This closes owned tabs, stops the owned server, and removes a Tailscale endpoint
only if this tool created it and it still matches. Pre-existing routes and
unrelated tabs/services remain intact. No new deployment is triggered.

## Rebuilding from scratch

If the local `.venv` gets stale (e.g. after moving to a different machine or
a Nix package upgrade), delete it and let `nix-shell` recreate it:

```bash
rm -rf .venv
nix-shell
```

## Troubleshooting

- `resume-docx: command not found` inside `nix-shell` — delete `.venv` and
  re-enter the shell (see above); the shell hook reinstalls the CLI
  automatically.
- PDF conversion errors — LibreOffice is provisioned by `nix-shell`; make
  sure you're running `make pdf` (or `make docx`) from inside the shell.
