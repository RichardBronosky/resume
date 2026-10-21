// Injected only by review-server.py; never part of the published resume.
(() => {
  const session = crypto.randomUUID();
  let reports = 0;
  const rect = e => {
    const r = e.getBoundingClientRect(), s = getComputedStyle(e);
    return {tag: e.tagName, id: e.id, class: e.getAttribute('class'),
      left: r.left, right: r.right, width: r.width, scrollWidth: e.scrollWidth,
      clientWidth: e.clientWidth, overflowX: s.overflowX, position: s.position,
      paddingLeft: s.paddingLeft, paddingRight: s.paddingRight,
      marginLeft: s.marginLeft, marginRight: s.marginRight, transform: s.transform,
      fontSize: s.fontSize, whiteSpace: s.whiteSpace, overflowWrap: s.overflowWrap};
  };
  async function report(reason, extra = {}) {
    if (++reports > 80) return;
    const width = document.documentElement.getBoundingClientRect().width;
    const nodes = [...document.querySelectorAll('body *')]
      .filter(e => !e.closest('#review-diagnostics'));
    const payload = {session, reason, time: new Date().toISOString(),
      userAgent: navigator.userAgent, url: location.pathname,
      innerWidth, innerHeight, screenWidth: screen.width, dpr: devicePixelRatio,
      scrollX, scrollY, root: rect(document.documentElement), body: rect(document.body),
      scrollingElement: document.scrollingElement && rect(document.scrollingElement),
      viewport: document.querySelector('meta[name="viewport"]')?.content,
      visualViewport: visualViewport && {width: visualViewport.width,
        height: visualViewport.height, scale: visualViewport.scale,
        offsetLeft: visualViewport.offsetLeft, pageLeft: visualViewport.pageLeft},
      mobileQuery: matchMedia('(max-width: 767px)').matches,
      containers: [...document.querySelectorAll('.container')].map(rect),
      details: [...document.querySelectorAll('.details')].map(rect),
      overflow: nodes.filter(e => {
        const r = e.getBoundingClientRect();
        return r.width && (r.left < -0.5 || r.right > width + 0.5 || e.scrollWidth > e.clientWidth + 1);
      }).map(rect).sort((a, b) =>
        Math.max(b.right - width, -b.left, b.scrollWidth - b.clientWidth) -
        Math.max(a.right - width, -a.left, a.scrollWidth - a.clientWidth)).slice(0, 100),
      stylesheets: [...document.styleSheets].map(s => ({href: s.href, disabled: s.disabled})),
      ...extra};
    try {
      const response = await fetch('/__review/report', {method: 'POST',
        headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
      if (!response.ok) throw new Error('HTTP ' + response.status);
      status.textContent = 'Report sent (' + reason + ')';
    } catch (error) { status.textContent = 'Report failed: ' + error.message; }
  }
  const panel = document.createElement('div');
  panel.id = 'review-diagnostics';
  panel.style.cssText = 'position:fixed;bottom:8px;left:8px;max-width:calc(100vw - 16px);z-index:2147483647;background:#fff;color:#111;border:1px solid #555;padding:5px;font:12px sans-serif;';
  const button = document.createElement('button');
  button.textContent = 'Report layout';
  button.style.cssText = 'color:#111;background:#eee;border:1px solid #555;padding:6px;';
  const status = document.createElement('span');
  status.textContent = ' Review diagnostics';
  button.onclick = () => report('manual');
  panel.append(button, status);
  document.body.append(panel);
  let timer;
  const later = reason => { clearTimeout(timer); timer = setTimeout(() => report(reason), 500); };
  addEventListener('resize', () => later('resize'));
  addEventListener('orientationchange', () => later('orientation'));
  visualViewport?.addEventListener('resize', () => later('visual-resize'));
  visualViewport?.addEventListener('scroll', () => later('visual-scroll'));
  addEventListener('scroll', () => { if (scrollX) later('horizontal-scroll'); }, {passive: true});
  addEventListener('scroll', e => {
    if (e.target instanceof Element && e.target.scrollLeft)
      report('nested-horizontal-scroll', {target: rect(e.target), scrollLeft: e.target.scrollLeft});
  }, {passive: true, capture: true});
  let touch;
  addEventListener('touchstart', e => {
    const t = e.touches[0]; touch = t && {x: t.clientX, y: t.clientY};
  }, {passive: true});
  addEventListener('touchend', e => {
    const t = e.changedTouches[0];
    if (touch && t && Math.abs(t.clientX - touch.x) > 25)
      report('horizontal-gesture', {gesture: {dx: t.clientX - touch.x, dy: t.clientY - touch.y}});
  }, {passive: true});
  addEventListener('error', e => {
    if (e.target?.src || e.target?.href)
      later('resource-error');
  }, true);
  report('loaded');
  setTimeout(() => report('settled'), 3000);
})();
