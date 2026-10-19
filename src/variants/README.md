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

## In the YAML

Any entry (job, education, skill group, profile), any bullet in
`highlights`, and any skill keyword can carry `variants:`.

| `variants:`            | appears in                                        |
| ---------------------- | ------------------------------------------------- |
| omitted                | every variant                                     |
| `[paper, ats]`         | only those (and one-offs that `extend` them)      |
| `["!ats"]`             | every variant except that one                     |
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

A resume tailored to one job is not a variant here. It is a folder on the
`oneoffs` branch with an `oneoff.yaml` that extends `paper` or `ats`. See
[AGENTS.md](../../AGENTS.md) and `tools/oneoff.py`. Facts it may use but the
public resume shouldn't show stay in the main YAML as `variants: [None]`.
