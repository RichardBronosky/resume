#!/usr/bin/env python3
"""Implementation of tools.sh. Run tools.sh help for the supported interface."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parent.parent
IDENTITY = hashlib.sha256(str(ROOT).encode()).hexdigest()[:12]
STATE = Path(f'/tmp/resume-tools-{os.getuid()}-{IDENTITY}')
PORT = 8765
PAGE = '/bruno.bronosky.resume.html'
LOCAL = f'http://127.0.0.1:{PORT}'
PYTHON = str(ROOT / '.venv/bin/python') if (ROOT / '.venv/bin/python').exists() else sys.executable
ENV = {**os.environ, 'PATH': str(ROOT / 'tools') + os.pathsep + os.environ.get('PATH', '')}
HELP = '''Usage: /absolute/path/to/tools.sh <command>

  make [TARGET ...] [VERSION=x]   Run validated Make targets (default: all)
  html                          Rebuild web JSON and HTML
  oneoff ARGS...                One-off CLI (its branch/facts rules still apply)
  variant ARGS...               Variant JSON CLI
  community [INPUT OUTPUT]      Community HTML renderer
  application ARGS...           Interactive application helper
  assemble [DIRECTORY]          Pages assembly (default: dist)
  jsonresume ACTION [ARGS...]   Maintained HTML/serve/watch adapters
  doctor                        Dependency and connection checks
  test                          Run entrypoint/server regression tests
  check public|pdf|layout|themes Public artifact, paper, or browser checks
  review demo                   Build, start, check layout/themes, open both tabs
  review start|stop|status       Manage only owned server/routes/tabs
  review open wide|mobile       Open/recover a dedicated chrollab tab
  review resize TAB WIDTH [HEIGHT]
  review refresh                Reload owned tabs, recovering closed tabs
  review screenshot TAB         Foreground capture; prints file:// link
  review inspect TAB            Viewport, overflow geometry, and browser errors
  review highlight TAB          Scroll to and highlight an overflowing label
  review diagnostics on|off     Toggle private response-only reporting
  review reports [COUNT]        Summarize phone layout reports
  review notify                 Send this demo URL to configured ntfy destination

Review uses loopback port 8765 and a dedicated tailnet HTTPS endpoint.
Diagnostics default off. No arbitrary shell/eval passthrough. No git push/commit.
Make clean is destructive; make release publishes. A blanket tools.sh approval
also permits those actions; use them only when authorized in the conversation.
'''


def run(*args, capture=False, timeout=60):
    result = subprocess.run([str(a) for a in args], cwd=ROOT, env=ENV,
                            text=True, capture_output=capture, timeout=timeout)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or f'{args[0]} failed').strip()
                           if capture else f'{args[0]} exited {result.returncode}')
    return result.stdout.strip() if capture else None


def read(name, default=None):
    path = STATE / name
    return json.loads(path.read_text()) if path.exists() else default


def write(name, value):
    temporary = STATE / (name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(STATE / name)


def request(url, payload=None, headers=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=15) as response:
        return response.read()


def branch():
    return run('git', 'branch', '--show-current', capture=True)


def require_main_work():
    if branch() == 'oneoffs':
        raise RuntimeError('This operation writes main build artifacts; use oneoff build on oneoffs.')


def html():
    require_main_work()
    run(PYTHON, ROOT / 'tools/resume-variant.py', 'web', '-o', 'build/bruno.bronosky.resume.json')
    run(ROOT / 'tools/jsonresume.sh', 'html')


def public_check():
    files = list((ROOT / 'build').rglob('*.html'))
    if not files:
        raise RuntimeError('No generated HTML; run tools.sh html first.')
    for path in files:
        if re.search(r'Report layout|review-diagnostics|/__review/', path.read_text(), re.I):
            raise RuntimeError(f'Private review diagnostics leaked into {path.relative_to(ROOT)}')
    print(f'PASS: {len(files)} public HTML files contain no review diagnostics.')


def pdf_check():
    path = ROOT / 'build/bruno.bronosky.resume.pdf'
    info = run('pdfinfo', path, capture=True)
    pages = re.search(r'^Pages:\s+(\d+)', info, re.M)
    if not pages:
        raise RuntimeError('pdfinfo did not return a page count.')
    old = subprocess.run(['git', 'show', 'HEAD:build/bruno.bronosky.resume.pdf'],
                         cwd=ROOT, capture_output=True, timeout=15)
    print(json.dumps({'pages': int(pages[1]), 'unchanged_from_HEAD':
                      old.returncode == 0 and old.stdout == path.read_bytes()}))


def server_owned(state):
    if not state:
        return False
    try:
        args = Path(f'/proc/{state["pid"]}/cmdline').read_bytes().split(b'\0')
        return (str(ROOT / 'tools/review-server.py').encode() in args
                and state['token'].encode() in args)
    except (OSError, KeyError):
        return False


def serve_config():
    return json.loads(run('tailscale', 'serve', 'status', '--json', capture=True)) or {}


def endpoint(config):
    matches = [(host, web) for host, web in config.get('Web', {}).items()
               if host.endswith(f':{PORT}')]
    if len(matches) > 1:
        raise RuntimeError('Multiple Serve endpoints use the review port; inspect tailscale serve status.')
    return matches[0] if matches else None


def ensure_route():
    config = serve_config()
    existing = endpoint(config)
    route = read('route.json', {})
    if existing:
        host, settings = existing
        if settings.get('Handlers') != {'/': {'Proxy': LOCAL}}:
            raise RuntimeError('Review port has an unrelated Tailscale route; it will not be replaced.')
        if config.get('AllowFunnel', {}).get(host):
            raise RuntimeError('Review endpoint has public Funnel enabled; refusing to use it.')
        # Reuse a matching existing route, but never claim ownership of it.
        if not route or route.get('host') != host:
            write('route.json', {'host': host, 'created': False})
    else:
        hostname = json.loads(run('tailscale', 'status', '--json', capture=True))['Self']['DNSName'].rstrip('.')
        host = f'{hostname}:{PORT}'
        if config.get('AllowFunnel', {}).get(host):
            raise RuntimeError('Public Funnel is enabled on the proposed review endpoint.')
        run('tailscale', 'serve', '--bg', f'--https={PORT}', LOCAL)
        write('route.json', {'host': host, 'created': True})
    return f'https://{host}{PAGE}'


def start():
    state = read('server.json')
    if not server_owned(state):
        token = uuid.uuid4().hex
        write('config.json', {'diagnostics': False})
        with (STATE / 'server.log').open('ab') as log:
            child = subprocess.Popen([sys.executable, '-u', str(ROOT / 'tools/review-server.py'),
                                      '--port', str(PORT), '--reports', str(STATE / 'reports.jsonl'),
                                      '--config', str(STATE / 'config.json'), '--owner-token', token],
                                     cwd=ROOT, env=ENV, stdin=subprocess.DEVNULL,
                                     stdout=log, stderr=log, start_new_session=True)
        state = {'pid': child.pid, 'token': token}
        for _ in range(40):
            if child.poll() is not None:
                raise RuntimeError('Review server failed to start (port may be in use). See ' + str(STATE / 'server.log'))
            try:
                health = json.loads(request(LOCAL + '/__review/health'))
                if health.get('owner') == token:
                    break
            except (OSError, ValueError):
                pass
            time.sleep(.1)
        else:
            if server_owned(state):
                os.kill(child.pid, signal.SIGTERM)
            raise RuntimeError('Review server did not become ready.')
        write('server.json', state)
    url = ensure_route()
    body = request(url).decode()
    expected = (ROOT / 'build/bruno.bronosky.resume.html').read_text()
    if not read('config.json', {}).get('diagnostics') and body != expected:
        raise RuntimeError('Tailnet response does not match the generated HTML.')
    print(url)
    return url


def review_url():
    route = read('route.json')
    if not route or not server_owned(read('server.json')):
        raise RuntimeError('Review server is not managed/running; run tools.sh review start.')
    return f'https://{route["host"]}{PAGE}'


def browser(tab, *args, capture=False):
    return run('agent-browser', '--cdp', '9222', '--pin-tab', '--session',
               f'resume-{IDENTITY}-{tab}', *args, capture=capture, timeout=35)


def tab_name(value):
    if value not in ('wide', 'mobile'):
        raise RuntimeError('Tab must be wide or mobile.')
    return value


def browser_tabs(tab):
    return json.loads(browser(tab, 'tab', 'list', '--json', capture=True))['data']['tabs']


def owned_tab(tab, known):
    if not known:
        return None
    return next((item for item in browser_tabs(tab)
                 if item['targetId'] == known.get('target')), None)


def open_tab(tab):
    tab_name(tab)
    tabs = read('tabs.json', {})
    known = tabs.get(tab)
    recovered = False
    if known:
        try:
            item = owned_tab(tab, known)
            if item:
                known['id'] = item['tabId']
                browser(tab, 'tab', item['tabId'])
                browser(tab, 'open', review_url())
                recovered = True
        except RuntimeError:
            pass
    if not recovered:
        label = f'resume-{IDENTITY}-{tab}'
        browser(tab, 'tab', 'new', '--label', label, review_url())
        item = next((item for item in browser_tabs(tab) if item.get('label') == label), None)
        if not item:
            raise RuntimeError('Could not identify the newly created review tab.')
        known = {'id': item['tabId'], 'target': item['targetId']}
    known.setdefault('width', 1280 if tab == 'wide' else 390)
    known.setdefault('height', 900 if tab == 'wide' else 844)
    browser(tab, 'set', 'viewport', str(known['width']), str(known['height']))
    tabs[tab] = known
    write('tabs.json', tabs)


def ensure_tab(tab):
    tab_name(tab)
    if tab not in read('tabs.json', {}):
        open_tab(tab)
    # Verify ownership even if a closed tab id was reused or session state reset.
    known = read('tabs.json')[tab]
    item = owned_tab(tab, known)
    if not item:
        open_tab(tab)
    else:
        browser(tab, 'tab', item['tabId'])


def evaluate(tab, code):
    output = browser(tab, 'eval', 'JSON.stringify(' + code + ')', capture=True)
    result = json.loads(output)
    return json.loads(result) if isinstance(result, str) else result


LAYOUT = '''(() => {
 const root = document.documentElement;
 const badges = [...document.querySelectorAll('.skill.badge,.interest.badge')];
 return {viewport: innerWidth, contentWidth: root.clientWidth, scrollWidth: root.scrollWidth,
   theme: root.dataset.theme,
   badBadges: badges.filter(e => {
     const r = e.getBoundingClientRect(), p = e.parentElement.getBoundingClientRect();
     const s = getComputedStyle(e.parentElement);
     return r.right > p.right - parseFloat(s.paddingRight) + 1 ||
            r.left < p.left + parseFloat(s.paddingLeft) - 1;
   }).map(e => e.textContent.trim())};
})()'''


def layout_check():
    ensure_tab('mobile')
    original = read('tabs.json')['mobile']
    failures = []
    try:
        for width in (320, 376, 390, 412, 768, 1024, 1280):
            browser('mobile', 'set', 'viewport', str(width), '900', capture=True)
            result = evaluate('mobile', LAYOUT)
            print(json.dumps(result))
            if result['scrollWidth'] > result['contentWidth'] + 1 or result['badBadges']:
                failures.append(str(width))
    finally:
        browser('mobile', 'set', 'viewport', str(original['width']), str(original['height']), capture=True)
    if failures:
        raise RuntimeError('Layout overflow at ' + ', '.join(failures) + 'px.')


MEDIA = "[...document.styleSheets].filter(s=>!s.href).flatMap(s=>[...s.cssRules].filter(r=>r.media).map(r=>r.media.mediaText))"


def themes_check():
    for tab in ('wide', 'mobile'):
        ensure_tab(tab)
        initial = evaluate(tab, 'document.documentElement.dataset.theme')
        media = evaluate(tab, MEDIA)
        try:
            for _ in range(2):
                browser(tab, 'click', '#theme-toggle', capture=True)
                result = evaluate(tab, LAYOUT)
                result['button'] = evaluate(tab, 'document.querySelector("#theme-toggle").innerText')
                if evaluate(tab, MEDIA) != media or result['scrollWidth'] > result['contentWidth'] + 1:
                    raise RuntimeError('Theme switching changed layout/media queries.')
                expected = 'light' if result['theme'] == 'dark' else 'dark'
                if expected not in result['button']:
                    raise RuntimeError('Theme button label did not update.')
                browser(tab, 'reload', capture=True)
                if evaluate(tab, 'document.documentElement.dataset.theme') != result['theme']:
                    raise RuntimeError('Theme preference did not survive reload.')
                print(tab + ': ' + json.dumps(result))
        finally:
            if evaluate(tab, 'document.documentElement.dataset.theme') != initial:
                browser(tab, 'click', '#theme-toggle', capture=True)


def screenshot(tab):
    ensure_tab(tab)  # foreground the owned tab before capture
    path = STATE / f'{tab}.png'
    browser(tab, 'screenshot', path)
    print(path.as_uri())


def inspect_tab(tab):
    ensure_tab(tab)
    print(json.dumps(evaluate(tab, LAYOUT), indent=2))
    print(json.dumps(evaluate(tab, '''[...document.querySelectorAll('body *')]
      .filter(e => e.getBoundingClientRect().right > document.documentElement.clientWidth + 1)
      .map(e => ({tag:e.tagName,id:e.id,class:e.getAttribute('class'),
                 right:e.getBoundingClientRect().right,position:getComputedStyle(e).position}))
      .slice(0,50)'''), indent=2))
    browser(tab, 'errors')


def highlight(tab):
    ensure_tab(tab)
    result = evaluate(tab, '''(() => {
      document.querySelectorAll('[data-review-highlight]').forEach(e=>e.remove());
      const edge = document.documentElement.clientWidth;
      const label = [...document.querySelectorAll('.skill-level')]
        .find(e=>e.getBoundingClientRect().right > edge + 1);
      if (!label) {
        document.querySelector('#section_skills')?.scrollIntoView({block:'start'});
        return {found:false};
      }
      label.scrollIntoView({block:'center',inline:'nearest'});
      window.scrollTo(0,window.scrollY);
      label.style.outline='3px solid red';
      label.style.background='#ffeb00'; label.style.color='#000';
      label.parentElement.style.outline='2px dashed orange';
      const line=document.createElement('div'); line.dataset.reviewHighlight='edge';
      line.style.cssText='position:fixed;top:0;bottom:0;width:3px;background:red;z-index:2147483647;pointer-events:none;left:'+(edge-3)+'px';
      const note=document.createElement('div'); note.dataset.reviewHighlight='note';
      note.style.cssText='position:fixed;top:8px;left:8px;max-width:80vw;padding:8px;background:#fff;color:#111;border:2px solid red;z-index:2147483647;pointer-events:none;font:14px sans-serif';
      note.textContent='Red line: viewport edge. Yellow label extends beyond it. Orange: its heading. Temporary review highlights; reload clears them.';
      document.body.append(line,note);
      return {found:true,heading:label.parentElement.textContent.trim(),right:label.getBoundingClientRect().right,edge};
    })()''')
    print(json.dumps(result))


def stop():
    tabs = read('tabs.json', {})
    for tab, settings in tabs.items():
        try:
            item = owned_tab(tab, settings)
            if item:
                browser(tab, 'tab', item['tabId'])
                browser(tab, 'tab', 'close')
        except (RuntimeError, subprocess.TimeoutExpired) as error:
            print('Browser cleanup skipped: ' + str(error), file=sys.stderr)
    write('tabs.json', {})
    route = read('route.json', {})
    if route.get('created'):
        current = endpoint(serve_config())
        if current and current[0] == route['host'] and current[1].get('Handlers') == {'/': {'Proxy': LOCAL}}:
            run('tailscale', 'serve', f'--https={PORT}', 'off')
            write('route.json', {})
        elif current:
            raise RuntimeError('Serve route changed; refusing to remove it.')
    state = read('server.json')
    if server_owned(state):
        os.kill(state['pid'], signal.SIGTERM)
    write('server.json', {})
    print('Stopped owned review resources. Pre-existing routes were preserved.')


def reports(count=5):
    path = STATE / 'reports.jsonl'
    if not path.exists():
        print('No reports yet.'); return
    for line in path.read_text().splitlines()[-count:]:
        row = json.loads(line)
        print(json.dumps({k: row.get(k) for k in
                          ('received', 'reason', 'userAgent', 'innerWidth', 'visualViewport', 'root')}))
        print('Top overflow: ' + json.dumps(row.get('overflow', [])[:5]))


def notify():
    url = review_url()
    server = os.environ.get('NTFY_SERVER', 'https://ntfy.sh').rstrip('/')
    topic = os.environ.get('NTFY_TOPIC', 'BrunoBronosky')
    headers = {'Title': 'Resume review ready', 'Click': url, 'Content-Type': 'application/json'}
    token = os.environ.get('NTFY_TOKEN', '')
    token_path = Path.home() / '.config/ntfy/token'
    if not token and token_path.exists():
        token = token_path.read_text().strip()
    if token:
        headers['Authorization'] = 'Bearer ' + token
    # ntfy JSON publishing uses the server root; the click URL opens the demo.
    result = json.loads(request(server, {'topic': topic, 'title': 'Resume review ready',
                                        'message': url, 'click': url}, headers))
    print('ntfy accepted notification: ' + result['id'])


def doctor():
    for name in ('python3', 'make', 'node', 'agent-browser', 'tailscale', 'pdfinfo', 'libreoffice'):
        print(f'{name}: {shutil.which(name) or "MISSING"}')
    print('checkout: ' + str(ROOT))
    print('state: ' + str(STATE))
    for command in [('tailscale', 'serve', 'status', '--json'),
                    ('agent-browser', '--cdp', '9222', '--session', f'resume-{IDENTITY}-doctor', 'tab', 'list')]:
        try:
            run(*command, capture=True, timeout=15)
            print(command[0] + ': connected')
        except (RuntimeError, subprocess.TimeoutExpired):
            print(command[0] + ': unavailable (check service or run tools.sh outside sandbox)')


def review(args):
    if not args:
        raise RuntimeError('Use review demo/start/stop/status/open/resize/refresh/screenshot/diagnostics/reports/notify.')
    action, *rest = args
    if action in ('start', 'stop', 'status', 'refresh', 'demo', 'notify') and rest:
        raise RuntimeError('Unexpected arguments for review ' + action)
    if action == 'start': start()
    elif action == 'stop': stop()
    elif action == 'status':
        print(json.dumps({'running': server_owned(read('server.json')), 'state': str(STATE),
                          'route': read('route.json'), 'tabs': read('tabs.json'),
                          'config': read('config.json')}, indent=2))
        reports(1)
    elif action == 'open' and len(rest) == 1: open_tab(rest[0])
    elif action == 'refresh':
        for tab in ('wide', 'mobile'): open_tab(tab)
    elif action == 'resize' and len(rest) in (2, 3):
        tab = tab_name(rest[0]); width = int(rest[1]); height = int(rest[2]) if len(rest) == 3 else 900
        if not (240 <= width <= 3840 and 240 <= height <= 3840):
            raise RuntimeError('Viewport dimensions must be 240..3840.')
        ensure_tab(tab)
        browser(tab, 'set', 'viewport', str(width), str(height))
        tabs = read('tabs.json'); tabs[tab].update(width=width, height=height); write('tabs.json', tabs)
    elif action == 'screenshot' and len(rest) == 1: screenshot(rest[0])
    elif action == 'inspect' and len(rest) == 1: inspect_tab(rest[0])
    elif action == 'highlight' and len(rest) == 1: highlight(rest[0])
    elif action == 'diagnostics' and rest in (['on'], ['off']):
        write('config.json', {'diagnostics': rest[0] == 'on'})
        for tab in read('tabs.json', {}): open_tab(tab)
        print('Diagnostics ' + rest[0] + '; only private server responses are affected.')
    elif action == 'reports' and len(rest) <= 1:
        count = int(rest[0]) if rest else 5
        if not 1 <= count <= 100: raise RuntimeError('Report count must be 1..100.')
        reports(count)
    elif action == 'notify': notify()
    elif action == 'demo':
        html(); public_check(); start()
        for tab in ('wide', 'mobile'): open_tab(tab)
        failures = []
        for check in (layout_check, themes_check):
            try: check()
            except (RuntimeError, subprocess.TimeoutExpired) as error:
                failures.append(str(error))
        for tab in ('wide', 'mobile'): screenshot(tab)
        print('Review: ' + review_url() + '\nSuper+0 opens shared Chrome. Await Bruno review before publishing.')
        if failures:
            raise RuntimeError('Demo is ready, but checks failed: ' + '; '.join(failures))
    else: raise RuntimeError('Invalid review command; run tools.sh help.')


def main(args):
    if not args or args[0] in ('help', '--help', '-h'):
        print(HELP); return
    cmd, *rest = args
    if cmd == 'make':
        targets = {'all', 'docx', 'pdf', 'ats', 'json', 'check-docx', 'clean', 'open-docx', 'open-pdf', 'release'}
        if any(a not in targets and not re.fullmatch(r'VERSION=[A-Za-z0-9._-]+', a) for a in rest):
            raise RuntimeError('Unsupported Make target/argument; run tools.sh help.')
        require_main_work(); run('make', *(rest or ['all']), timeout=300)
    elif cmd == 'html' and not rest: html()
    elif cmd in ('oneoff', 'variant', 'application'):
        scripts = {'oneoff': 'oneoff.py', 'variant': 'resume-variant.py', 'application': 'job-application-helper.py'}
        run(PYTHON, ROOT / 'tools' / scripts[cmd], *rest, timeout=3600 if cmd == 'application' else 300)
    elif cmd == 'community' and len(rest) in (0, 2):
        require_main_work(); run('node', ROOT / 'tools/community-html.cjs', *rest)
    elif cmd == 'assemble' and len(rest) <= 1:
        run(ROOT / 'tools/assemble-site.sh', *rest)
    elif cmd == 'jsonresume' and rest and rest[0] in ('html', 'html_preload', 'yaml_file_to_json_file', 'serve', 'watch_yaml_to_json'):
        require_main_work(); run(ROOT / 'tools/jsonresume.sh', *rest, timeout=3600)
    elif cmd == 'doctor' and not rest: doctor()
    elif cmd == 'test' and not rest:
        run(sys.executable, '-m', 'unittest', 'discover', '-s', 'tools/tests', '-v')
    elif cmd == 'review': review(rest)
    elif cmd == 'check' and len(rest) == 1:
        checks = {'public': public_check, 'pdf': pdf_check, 'layout': layout_check, 'themes': themes_check}
        if rest[0] not in checks: raise RuntimeError('Unknown check.')
        checks[rest[0]]()
    else: raise RuntimeError('Unknown command/arguments; run tools.sh help.')


if __name__ == '__main__':
    if not sys.argv[1:] or sys.argv[1] in ('help', '--help', '-h'):
        print(HELP)
        sys.exit(0)
    try:
        STATE.mkdir(mode=0o700, exist_ok=True)
        if STATE.is_symlink() or STATE.stat().st_uid != os.getuid():
            raise RuntimeError('Unsafe review state directory.')
        STATE.chmod(0o700)
        if sys.argv[1:3] in (['review', 'status'], ['review', 'reports']):
            main(sys.argv[1:])
        else:
            with (STATE / 'lock').open('w') as lock:
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise RuntimeError('Another tools.sh command is running; retry when it finishes.')
                main(sys.argv[1:])
    except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired, KeyboardInterrupt) as error:
        print('tools: ' + (str(error) or 'Interrupted'), file=sys.stderr)
        sys.exit(1)
