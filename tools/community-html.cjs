#!/usr/bin/env node
// Render src/bruno.bronosky.community.md as a web page that matches the resume:
// same theme CSS, header (photo, name, title) and section boxes.
// Usage: node tools/community-html.cjs [in.md] [out.html]
const fs = require('fs');
const path = require('path');
const showdown = require('showdown');
const gravatar = require('gravatar');

const [inp = 'src/bruno.bronosky.community.md', out = 'build/bruno.bronosky.community.html'] = process.argv.slice(2);
const theme = path.join(__dirname, '..', 'themes', 'jsonresume-theme-kendall-markdown');
const basics = JSON.parse(fs.readFileSync('build/bruno.bronosky.resume.json', 'utf8')).basics;
const css = fs.readFileSync(path.join(theme, 'style.css'), 'utf8');
const printcss = fs.readFileSync(path.join(theme, 'print.css'), 'utf8');
const photo = basics.image || gravatar.url(basics.email, { s: '200', r: 'pg', d: 'mm' });

const md = fs.readFileSync(inp, 'utf8').replace(/^---\n[\s\S]*?\n---\n/, '');
const heading = (md.match(/^#\s+(.+)$/m) || [, 'Community Involvement'])[1];
// The page header carries the h1; sections below become themed boxes.
const body = new showdown.Converter({ simplifiedAutoLink: true, ghCompatibleHeaderId: true, disableForced4SpacesIndentedSublists: true })
  .makeHtml(md.replace(/^#\s+.+\n/m, ''))
  .split(/(?=<h2)/)
  .filter((s) => s.trim())
  .map((s) => `<div class="box community">${s}</div>`)
  .join('\n');

fs.writeFileSync(out, `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${heading} - ${basics.name}</title>
    <link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css" rel="stylesheet">
    <style type="text/css">
${css}
.community ul { padding-left: 1.4em; }
.community li { margin-bottom: .5em; }
.community h2 { margin-top: 0; }
#back { display: block; text-align: center; margin-bottom: 1.5em; }
    </style>
    <style type="text/css" media="print">
${printcss}
    </style>
  </head>
  <body>
    <div class="container">
      <div class="row">
        <div class="col-xs-12">
          <div id="photo-header" class="text-center">
            <div id="photo"><img src="${photo}" alt="avatar"></div>
            <div id="text-header">
              <h1>${basics.name}<br><span>${heading}</span></h1>
            </div>
          </div>
        </div>
      </div>
      <div class="row">
        <div class="col-xs-12">
${body}
          <a id="back" href="../"><i class="fas fa-arrow-left"></i> Back to the resume</a>
        </div>
      </div>
    </div>
  </body>
</html>
`);
console.log(out);
