# Handoff: Rebuild gh-pages with Latest Resume Data

## Objective

Update <https://richardbronosky.github.io/resume/> with the latest resume data
from the `refactor/docx-generator` branch, including a new DOCX-generated PDF.
The gh-pages branch should be rebuilt as an **orphan branch** (clean history, no
source code, just built artifacts).

## Repo

- **Remote:** `ssh://git@github.com/RichardBronosky/resume`
- **Branch with latest data:** `refactor/docx-generator`
- **Source of truth:** `src/bruno.bronosky.resume.yaml`

## Current gh-pages URL Structure (must be preserved)

These URLs are referenced in the YAML itself and possibly linked externally:

| URL Path                                    | Serves                                |
|---------------------------------------------|---------------------------------------|
| `/resume/`                                  | HTML resume (root index.html)         |
| `/resume/html/`                             | HTML resume (redirect to HTML file)   |
| `/resume/html/bruno.bronosky.resume.html`   | HTML resume (direct)                  |
| `/resume/pdf/`                              | PDF resume (redirect to PDF file)     |
| `/resume/pdf/bruno.bronosky.resume.pdf`     | PDF file (direct download)            |

## Step-by-Step Plan

### 1. Set Up the Build Environment

The `refactor/docx-generator` branch should already be checked out. If not:

```bash
cd ~/src/resume  # or wherever the clone is
git checkout refactor/docx-generator
git pull
```

The Python venv is broken (created on a different machine). Recreate it:

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -e src/docx-generator
```

Verify:

```bash
resume-docx --help
```

Node.js deps for HTML generation (if `node_modules/` is stale):

```bash
npm install
```

### 2. Generate the DOCX

```bash
make docx
```

Output: `build/bruno.bronosky.resume.docx`

### 3. Generate the PDF from DOCX

Requires LibreOffice. Either:

```bash
make pdf
```

Or manually:

```bash
libreoffice --headless --convert-to pdf --outdir build/ build/bruno.bronosky.resume.docx
```

Output: `build/bruno.bronosky.resume.pdf`

Verify the PDF looks correct before proceeding.

### 4. Generate the HTML Resume

Uses the Node.js JSON Resume pipeline. First convert YAML to JSON:

```bash
yq -o json src/bruno.bronosky.resume.yaml > build/bruno.bronosky.resume.json
```

Note: The YAML file is multi-document (two `---` sections). The second document
(with `$schema`) is the actual resume data. The `yq` command should handle this,
but verify the JSON output has the `basics`, `work`, `education`, `skills` keys.
If yq outputs only the first document, use:

```bash
yq -o json 'select(documentIndex == 1)' src/bruno.bronosky.resume.yaml > build/bruno.bronosky.resume.json
```

Then render HTML:

```bash
npx resumed render build/bruno.bronosky.resume.json \
  --theme jsonresume-theme-kendall-markdown \
  -o build/bruno.bronosky.resume.html
```

Verify the HTML opens correctly in a browser.

### 5. Create the Orphan gh-pages Branch

```bash
# Start from a clean orphan branch
git checkout --orphan gh-pages-new

# Remove everything from the index
git rm -rf .

# Create the directory structure
mkdir -p html pdf build
```

### 6. Populate the gh-pages Content

```bash
# Copy built artifacts into build/
cp <path-to>/build/bruno.bronosky.resume.html build/
cp <path-to>/build/bruno.bronosky.resume.pdf build/
cp <path-to>/build/bruno.bronosky.resume.json build/

# Root index: symlink to the HTML resume
ln -s build/bruno.bronosky.resume.html index.html

# html/ directory
ln -s ../build/bruno.bronosky.resume.html html/bruno.bronosky.resume.html
```

Create `html/index.html` - a redirect page:

```html
<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="refresh" content="0; url='bruno.bronosky.resume.html'" />
  <title>Resume of Bruno Bronosky</title>
</head>
<body>
  <p>Redirecting to <a href="bruno.bronosky.resume.html">resume</a>...</p>
</body>
</html>
```

```bash
# pdf/ directory
ln -s ../build/bruno.bronosky.resume.pdf pdf/bruno.bronosky.resume.pdf
```

Create `pdf/index.html` - a redirect page:

```html
<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="refresh" content="0; url='bruno.bronosky.resume.pdf'" />
  <title>Resume PDF - Bruno Bronosky</title>
</head>
<body>
  <p>Redirecting to <a href="bruno.bronosky.resume.pdf">PDF resume</a>...</p>
</body>
</html>
```

Add a `.nojekyll` file to prevent GitHub Pages from processing with Jekyll:

```bash
touch .nojekyll
```

### 7. Commit and Force-Push

```bash
git add -A
git commit -m "Rebuild gh-pages with latest resume data from refactor/docx-generator"

# Delete the old gh-pages branch and push the new one
git branch -D gh-pages 2>/dev/null
git branch -m gh-pages
git push origin gh-pages --force
```

### 8. Verify

- Visit <https://richardbronosky.github.io/resume/> and confirm the HTML loads
- Visit <https://richardbronosky.github.io/resume/pdf/> and confirm PDF downloads
- Visit <https://richardbronosky.github.io/resume/html/> and confirm redirect works
- Check that the title/summary reflects the latest "AI-Augmented" branding

### 9. Return to Working Branch

```bash
git checkout refactor/docx-generator
```

## Important Notes

- The old gh-pages had `community/` and `toc/` directories. These are legacy and
  can be dropped from the orphan rebuild unless Bruno wants them preserved.
- The `bruno.bronosky.resume.pdf` symlink in the repo root on gh-pages
  (`/resume/bruno.bronosky.resume.pdf`) was also a legacy path. If external links
  point there, add it: `ln -s build/bruno.bronosky.resume.pdf bruno.bronosky.resume.pdf`
- The YAML file references these URLs in the `basics` section (`url`, `urlPrintable`,
  `urlPdf`). After verifying the site works, consider whether those fields need
  updating.
- If `resumed` rendering fails or the theme is outdated, the HTML can also be
  generated with: `npx resumed render --theme @jsonresume/jsonresume-theme-kendall build/bruno.bronosky.resume.json`
