#!/usr/bin/env node
// Render src/bruno.bronosky.community.md to a standalone, responsive HTML page.
// Usage: node tools/community-html.cjs [in.md] [out.html]
const fs = require('fs');
const showdown = require('showdown');
const [inp = 'src/bruno.bronosky.community.md', out = 'build/bruno.bronosky.community.html'] = process.argv.slice(2);
const md = fs.readFileSync(inp, 'utf8').replace(/^---\n[\s\S]*?\n---\n/, '');
const conv = new showdown.Converter({ simplifiedAutoLink: true, ghCompatibleHeaderId: true, openLinksInNewWindow: false });
const body = conv.makeHtml(md);
const title = (md.match(/^#\s+(.+)$/m) || [, 'Community Involvement'])[1];
fs.writeFileSync(out, `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title} - Bruno Bronosky</title>
<style>
:root { color-scheme: light dark; }
body { font: 16px/1.55 system-ui, sans-serif; max-width: 46rem; margin: 0 auto; padding: 1rem; overflow-wrap: break-word; }
img { max-width: 100%; height: auto; }
pre, code { white-space: pre-wrap; }
h1, h2 { line-height: 1.2; }
footer { margin-top: 2rem; font-size: .9em; }
</style>
</head>
<body>
${body}
<footer><a href="../">Resume</a> · <a href="../pdf/">PDF</a></footer>
</body>
</html>
`);
console.log(out);
