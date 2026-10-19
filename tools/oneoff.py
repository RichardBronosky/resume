#!/usr/bin/env python3
"""Make, build, check and track one-off resumes. Read AGENTS.md first.

    tools/oneoff.py new <slug> --company C --role R [--url U]
    tools/oneoff.py build <slug>       # -> oneoffs/<slug>/Bruno-Bronosky-Resume.{pdf,docx}
    tools/oneoff.py check [<slug>]     # what CI runs; build runs it too
    tools/oneoff.py list               # tracker table
    tools/oneoff.py status <slug> <status>

One-offs live only on the `oneoffs` branch, one folder each under oneoffs/.
That branch is main plus the oneoffs/ folder and nothing else; main never
contains oneoffs/. Content comes from src/bruno.bronosky.resume.yaml; a
one-off only selects, reorders and rewords it (see `jobs:` in oneoff.yaml).
"""

import argparse
import datetime
import os
import re
import subprocess
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = "oneoffs"
BRANCH = "oneoffs"
OUT = "Bruno-Bronosky-Resume"
STATUSES = ("draft", "sent", "interview", "offer", "rejected", "withdrawn")
BASES = ("paper", "ats")
SLUG = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(-[a-z0-9]+)*$")

TEMPLATE = """\
# One-off resume. Only this folder may change on the `oneoffs` branch.
# Content must come from src/bruno.bronosky.resume.yaml: `jobs` ops quote its
# bullets word for word. New facts go into main first, never here.
meta:
  company: {company}
  role: {role}
  url: {url}
  status: draft          # {statuses}
  applied:               # YYYY-MM-DD when sent
  notes: ""
built_from:              # main commit; written by `tools/oneoff.py build`
extends: paper           # or ats

basics:
  label: Principal DevOps Engineer | Team Lead & Trainer
  # summary: |-
  #   Free text, but every claim in it must already be in the main YAML.

# Per job id (see `id:` in the main YAML):
#   top:    bullets to put first; may name `variants: [None]` bullets
#   drop:   bullets to leave out
#   reword: [{{text: ..., based_on: <exact existing bullet>}}]
jobs: {{}}

# skills: [...]          # optional full replacement of the skills list
"""


def die(msg):
    sys.exit(f"oneoff: {msg}")


def git(*args, check=True):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if check and r.returncode:
        die(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def main_ref():
    for ref in ("main", "origin/main"):
        if git("rev-parse", "--verify", "-q", ref, check=False):
            return ref
    die("no main or origin/main ref; fetch first")


def require_branch():
    branch = git("branch", "--show-current") or os.environ.get("GITHUB_REF_NAME", "")
    if branch != BRANCH:
        die(f"one-offs are made only on the '{BRANCH}' branch (you are on '{branch}').\n"
            f"  git switch {BRANCH} && git merge main")


def folder(slug):
    return os.path.join(ROOT, DIR, slug)


def load(slug):
    path = os.path.join(folder(slug), "oneoff.yaml")
    if not os.path.isfile(path):
        die(f"no {os.path.relpath(path, ROOT)}")
    with open(path) as f:
        return path, yaml.safe_load(f) or {}


def slugs():
    d = os.path.join(ROOT, DIR)
    return sorted(s for s in os.listdir(d) if os.path.isdir(os.path.join(d, s))) if os.path.isdir(d) else []


def check_branch_scope():
    """The oneoffs branch may differ from main only inside oneoffs/."""
    base = git("merge-base", "HEAD", main_ref())
    changed = git("diff", "--name-only", base, "HEAD").splitlines()
    changed += git("diff", "--name-only", "HEAD").splitlines()  # uncommitted, tracked
    outside = sorted({p for p in changed if p and not p.startswith(DIR + "/")})
    return [f"changes outside {DIR}/ on the {BRANCH} branch (make them on main instead): {p}" for p in outside]


def check_one(slug):
    errors = []
    if not SLUG.match(slug):
        errors.append(f"{slug}: folder name must be YYYY-MM-DD-company-role, lowercase")
    path, cfg = load(slug)
    meta = cfg.get("meta") or {}
    for k in ("company", "role", "status"):
        if not meta.get(k):
            errors.append(f"{slug}: meta.{k} is required")
    if meta.get("status") and meta["status"] not in STATUSES:
        errors.append(f"{slug}: meta.status must be one of {', '.join(STATUSES)}")
    if cfg.get("extends") not in BASES:
        errors.append(f"{slug}: extends must be one of {', '.join(BASES)}")
    extra = set(os.listdir(folder(slug))) - {
        "oneoff.yaml", "jd.txt", "cover-letter.md", "resume.json", f"{OUT}.pdf", f"{OUT}.docx", "NOTES.md"}
    if extra:
        errors.append(f"{slug}: unexpected files {sorted(extra)}")
    # A dry build validates job ids and that every quoted bullet exists.
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "resume-variant.py"), path],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        errors.append(f"{slug}: {r.stderr.strip() or r.stdout.strip()}")
    return errors


def cmd_check(a):
    on_branch = (git("branch", "--show-current") or os.environ.get("GITHUB_REF_NAME", "")) == BRANCH
    if not on_branch:
        tracked = git("ls-files", DIR)
        if tracked:
            die(f"{DIR}/ is tracked on this branch; one-offs belong only on '{BRANCH}'")
        print(f"ok: no one-offs on this branch")
        return
    errors = check_branch_scope()
    for slug in ([a.slug] if a.slug else slugs()):
        errors += check_one(slug)
    if errors:
        die("check failed:\n  " + "\n  ".join(errors))
    print(f"ok: {len([a.slug] if a.slug else slugs())} one-off(s) checked")


def cmd_new(a):
    require_branch()
    if not SLUG.match(a.slug):
        die("slug must be YYYY-MM-DD-company-role, lowercase, e.g. "
            f"{datetime.date.today()}-acme-sre-lead")
    d = folder(a.slug)
    if os.path.exists(d):
        die(f"{os.path.relpath(d, ROOT)} already exists")
    os.makedirs(d)
    with open(os.path.join(d, "oneoff.yaml"), "w") as f:
        f.write(TEMPLATE.format(company=yaml.safe_dump(a.company).strip().removesuffix("\n..."),
                                role=yaml.safe_dump(a.role).strip().removesuffix("\n..."),
                                url=a.url or "", statuses=" | ".join(STATUSES)))
    print(f"created {os.path.relpath(d, ROOT)}/oneoff.yaml; put the posting in jd.txt beside it")


def cmd_build(a):
    require_branch()
    cmd_check(argparse.Namespace(slug=a.slug))
    path, cfg = load(a.slug)
    d = folder(a.slug)
    py = os.path.join(ROOT, ".venv", "bin", "python")
    py = py if os.path.exists(py) else sys.executable
    run = lambda *c, **kw: subprocess.run(c, cwd=ROOT, check=True, **kw)
    run(sys.executable, "tools/resume-variant.py", path, "-o", os.path.join(d, "resume.json"))
    docx = os.path.join(d, f"{OUT}.docx")
    args = [py, "-m", "docx_generator.cli", os.path.join(d, "resume.json"), "-o", docx, "--pdf"]
    if cfg.get("extends") == "ats":
        args.append("--ats")
        docx = docx.replace(".docx", ".ats.docx")
    env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src", "docx-generator", "src"))
    run(*args, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if docx.endswith(".ats.docx"):  # the generator adds .ats; keep one stable name
        os.replace(docx, os.path.join(d, f"{OUT}.docx"))
        os.replace(docx.replace(".docx", ".pdf"), os.path.join(d, f"{OUT}.pdf"))
    sha = git("rev-parse", "--short", git("merge-base", "HEAD", main_ref()))
    text = open(path).read()
    text = re.sub(r"(?m)^built_from:.*$", f"built_from: {sha}              # main commit; written by `tools/oneoff.py build`", text, count=1)
    open(path, "w").write(text)
    pages = subprocess.run(["qpdf", "--show-npages", os.path.join(d, f"{OUT}.pdf")],
                           capture_output=True, text=True).stdout.strip() or "?"
    print(f"built {os.path.relpath(d, ROOT)}/{OUT}.pdf ({pages} pages) and .docx from main@{sha}")


def cmd_list(a):
    rows = [("folder", "status", "applied", "company", "role")]
    for slug in slugs():
        _, cfg = load(slug)
        m = cfg.get("meta") or {}
        rows.append((slug, str(m.get("status") or ""), str(m.get("applied") or ""),
                     str(m.get("company") or ""), str(m.get("role") or "")))
    widths = [max(len(r[i]) for r in rows) for i in range(len(rows[0]))]
    for r in rows:
        print("  ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip())


def cmd_status(a):
    require_branch()
    if a.status not in STATUSES:
        die(f"status must be one of {', '.join(STATUSES)}")
    path, _ = load(a.slug)
    text = open(path).read()
    text = re.sub(r"(?m)^(  status:)\s*\S+", rf"\1 {a.status}", text, count=1)
    if a.status == "sent":
        text = re.sub(r"(?m)^(  applied:)[ \t]*(#.*)?$", rf"\1 {datetime.date.today()}", text, count=1)
    open(path, "w").write(text)
    print(f"{a.slug}: {a.status}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("new"); n.add_argument("slug"); n.add_argument("--company", required=True)
    n.add_argument("--role", required=True); n.add_argument("--url")
    b = sub.add_parser("build"); b.add_argument("slug")
    c = sub.add_parser("check"); c.add_argument("slug", nargs="?")
    sub.add_parser("list")
    s = sub.add_parser("status"); s.add_argument("slug"); s.add_argument("status")
    a = p.parse_args()
    {"new": cmd_new, "build": cmd_build, "check": cmd_check, "list": cmd_list, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    main()
