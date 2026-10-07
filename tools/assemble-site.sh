#!/usr/bin/env bash
# Assemble the GitHub Pages site into ./dist from committed build/ artifacts.
#   /resume/                  <- origin/main
#   /resume/preview/<branch>/ <- every origin/preview/<branch> (the "preview/" prefix is the opt-in)
# Reads git refs, not the working tree, so it gives the same result whichever branch triggered it.
set -euo pipefail

OUT=${1:-dist}
BASE=bruno.bronosky.resume

redirect() { # redirect <dir> <target>
  mkdir -p "$OUT/$1"
  printf '<!DOCTYPE html>\n<meta charset="utf-8">\n<title>Resume of Bruno Bronosky</title>\n<meta http-equiv="refresh" content="0; url=%s">\n<a href="%s">Continue</a>\n' "$2" "$2" > "$OUT/$1/index.html"
}

# site <ref> <dest-dir>: lay out one version of the site
site() {
  local ref=$1 dest=$2 f
  mkdir -p "$dest/html" "$dest/pdf"
  git show "$ref:build/$BASE.html" > "$dest/index.html"
  cp "$dest/index.html" "$dest/html/$BASE.html"
  cp "$dest/index.html" "$dest/html/index.html"
  git show "$ref:build/$BASE.pdf"  > "$dest/pdf/$BASE.pdf"
  for f in "$BASE.docx" "$BASE.json" bruno.bronosky.community.pdf; do
    git show "$ref:build/$f" > "$dest/$f" 2>/dev/null || rm -f "$dest/$f"
  done
  # /community/: a real HTML page (a github.com link would open the GitHub app on Android);
  # fall back to the PDF if no HTML was built.
  mkdir -p "$dest/community"
  if git cat-file -e "$ref:build/bruno.bronosky.community.html" 2>/dev/null; then
    git show "$ref:build/bruno.bronosky.community.html" > "$dest/community/index.html"
  elif [ -f "$dest/bruno.bronosky.community.pdf" ]; then
    printf '<!DOCTYPE html>\n<meta charset="utf-8">\n<meta http-equiv="refresh" content="0; url=../bruno.bronosky.community.pdf">\n' > "$dest/community/index.html"
  else
    rmdir "$dest/community"
  fi
}

rm -rf "$OUT"
site origin/main "$OUT"
redirect "pdf" "$BASE.pdf"

rows=""
while read -r ref; do
  [ -n "$ref" ] || continue
  name=${ref#origin/preview/}
  dest="$OUT/preview/$name"
  if ! git cat-file -e "$ref:build/$BASE.html" 2>/dev/null; then
    echo "skip $ref: no build/$BASE.html"; continue
  fi
  site "$ref" "$dest"
  redirect "preview/$name/pdf" "$BASE.pdf"
  sha=$(git rev-parse --short "$ref")
  # Mark as non-public-facing: keep out of search engines, banner on the HTML pages.
  for page in "$dest/index.html" "$dest/html/$BASE.html" "$dest/html/index.html" "$dest/community/index.html"; do
    [ -f "$page" ] || continue
    sed -i "0,/<\/head>/s||<meta name=\"robots\" content=\"noindex,nofollow\"></head>|" "$page"
    sed -i "0,/<body[^>]*>/s||&<div style=\"position:fixed;bottom:0;left:0;z-index:9999;background:#b00020;color:#fff;font:12px sans-serif;padding:3px 8px\">PREVIEW preview/$name @ $sha</div>|" "$page"
  done
  rows+="<li><a href=\"$name/\">preview/$name</a> <small>($sha)</small></li>"
  echo "preview: $ref -> /preview/$name/"
done < <(git for-each-ref --format='%(refname:short)' 'refs/remotes/origin/preview/')

mkdir -p "$OUT/preview"
printf '<!DOCTYPE html>\n<meta charset="utf-8">\n<meta name="robots" content="noindex,nofollow">\n<title>Resume previews</title>\n<h1>Resume previews</h1>\n<ul>%s</ul>\n<p><a href="../">Production resume</a></p>\n' "${rows:-<li>none</li>}" > "$OUT/preview/index.html"
find "$OUT" -type f | sort
