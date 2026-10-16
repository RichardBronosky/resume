# Resume variants

`src/bruno.bronosky.resume.yaml` is the only source of truth. Each file here
defines one output, and `tools/resume-variant.py <name>` turns the YAML into
plain JSON Resume for it. The HTML theme and the DOCX generator only ever see
that JSON, so they cannot disagree about what is shown.

| variant     | output                                  | what it is                                 |
| ----------- | --------------------------------------- | ------------------------------------------ |
| `web`       | `build/…resume.json`, `.html`           | exhaustive: every entry and every bullet    |
| `paper`     | `build/…resume.docx`, `.pdf`            | aggregates on, top-N bullets per job        |
| `ats`       | `build/…resume.ats.docx`                | `paper` + ATS-only aggregates               |
| `mysql-dba` | `build/…resume.mysql-dba.docx`, `.pdf`  | one-off, `make oneoff VARIANT=mysql-dba`    |

## In the YAML

Any entry (job, education, skill group, profile), any bullet in
`highlights`, and any skill keyword can carry `variants:`.

| `variants:`            | appears in                                        |
| ---------------------- | ------------------------------------------------- |
| omitted                | every variant                                     |
| `[paper, ats]`         | only those (and one-offs that `extend` them)      |
| `["!mysql-dba"]`       | every variant except that one                     |
| `[None]`               | nowhere; kept only as the source of truth         |

A bullet that needs `variants:` is written as `{text: "...", variants: [...]}`.

**Aggregates.** An entry with `replaces: [id, id, …]` stands in for those
entries: whenever it is shown, they are not. "Various" is `[paper, ats]` and
replaces the early-career jobs, so paper shows "Various" and the web shows the
individual jobs. Every work entry has an `id` for this.

**Bullet order is priority order.** Put a job's strongest bullet first.
`paper` keeps the top 8 for jobs that ended in the last 6 years, 5 for the
last 15, and 3 before that (`highlights.max_by_age` in `paper.yaml`).

## One-off resumes

Copy `mysql-dba.yaml`. A one-off `extends` a base variant and can override
`basics` (label, summary), replace `skills`, and change the bullet caps. Write
tailored bullets in the main YAML with `variants: [<one-off>]`; with
`promote_own_bullets: true` they go to the top of their job. When a tailored
bullet rewrites a generic one, mark the generic one `["!<one-off>"]`.
