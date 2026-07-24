// Render index.html in headless Chromium, routing cdnjs URLs to local UMD
// builds (the sandbox can't reach the CDN). Screenshots p50 and p80 views.
const { chromium } = require('playwright-core');
const fs = require('fs');
const path = require('path');

const NM = path.join(__dirname, 'node_modules');
const LOCAL = {
  'react/18.2.0/umd/react.production.min.js': 'react/umd/react.production.min.js',
  'react-dom/18.2.0/umd/react-dom.production.min.js': 'react-dom/umd/react-dom.production.min.js',
  'prop-types/15.8.1/prop-types.min.js': 'prop-types/prop-types.min.js',
  'recharts/2.15.3/Recharts.min.js': 'recharts/umd/Recharts.js',
  'babel-standalone/7.23.9/babel.min.js': '@babel/standalone/babel.min.js',
};

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium' });
  const page = await browser.newPage({ viewport: { width: 1100, height: 900 } });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });

  await page.route('**cdnjs.cloudflare.com/**', route => {
    const url = route.request().url();
    const hit = Object.keys(LOCAL).find(k => url.includes(k));
    if (hit) route.fulfill({ body: fs.readFileSync(path.join(NM, LOCAL[hit])),
                             contentType: 'application/javascript' });
    else route.abort();
  });

  await page.goto('file://' + path.resolve(__dirname, '../../index.html'));
  await page.waitForTimeout(4000); // babel transform + render
  await page.screenshot({ path: 'chart_p50.png' });

  // DOM assertions (cheaper than eyeballing screenshots)
  const failures = [];
  const labelsPresent = names => page.evaluate(ns => {
    const have = new Set([...document.querySelectorAll('text')].map(t => t.textContent));
    return ns.filter(n => !have.has(n));
  }, names);
  const OPEN_MODELS = ['DeepSeek-R1', 'GLM-5.2', 'Kimi K3'];
  // open-weights reference diamonds render in the TH view
  for (const n of await labelsPresent(OPEN_MODELS))
    failures.push(`TH view: missing ${n}`);
  // "ECI lab-adj" basis: labs without an ANCOVA intercept must fall back to
  // the pooled fit, not vanish with NaN coordinates
  await page.getByRole('button', { name: 'ECI lab-adj' }).click();
  await page.waitForTimeout(600);
  for (const n of await labelsPresent(OPEN_MODELS))
    failures.push(`lab-adj basis: missing ${n}`);
  await page.getByRole('button', { name: 'per-lab default' }).click();
  await page.waitForTimeout(300);

  // toggle p80 view
  await page.getByText('Show p80 (harder tasks)').click();
  await page.waitForTimeout(800);
  await page.screenshot({ path: 'chart_p80.png' });
  await page.getByText('Show p80 (harder tasks)').click(); // back to p50

  // score modes
  await page.getByRole('button', { name: 'ECI', exact: true }).click();
  await page.waitForTimeout(800);
  await page.screenshot({ path: 'chart_eci.png' });
  // open-weights models carry a public ECI, so they appear in score mode too
  for (const n of await labelsPresent(OPEN_MODELS))
    failures.push(`ECI view: missing ${n}`);
  // hover Opus 4.6 in ECI mode: tooltip should show the METR horizons line
  const o46 = await page.evaluate(() => {
    const t = [...document.querySelectorAll('text')].find(el => el.textContent === 'Opus 4.6');
    if (!t) return null;
    const r = t.getBoundingClientRect();
    return { x: r.right + 8, y: r.top + r.height / 2 + 12 };
  });
  if (o46) {
    await page.mouse.move(o46.x, o46.y);
    await page.waitForTimeout(600);
    await page.screenshot({ path: 'chart_eci_tooltip.png' });
    await page.mouse.move(60, 60);
    await page.waitForTimeout(300);
  }
  // wheel-zoom into the 2025-26 frontier region
  await page.mouse.move(600, 400);
  await page.mouse.wheel(0, -300);
  await page.mouse.wheel(0, -300);
  await page.waitForTimeout(600);
  await page.screenshot({ path: 'chart_eci_zoom.png' });
  await page.getByText('Reset zoom').click();
  await page.waitForTimeout(400);
  await page.getByRole('button', { name: 'AECI', exact: true }).click();
  await page.waitForTimeout(800);
  await page.screenshot({ path: 'chart_aeci.png' });
  await page.getByRole('button', { name: 'Time horizon' }).click();
  await page.waitForTimeout(800);

  // hover a measured dot in TH mode to check the new index line (Opus 4.6:
  // label is end-anchored at (cx-8, cy-12), so the dot sits right+below it)
  const opus = await page.evaluate(() => {
    const t = [...document.querySelectorAll('text')].find(el => el.textContent === 'Opus 4.6');
    if (!t) return null;
    const r = t.getBoundingClientRect();
    return { x: r.right + 8, y: r.top + r.height / 2 + 12 };
  });
  if (opus) {
    await page.mouse.move(opus.x, opus.y);
    await page.waitForTimeout(600);
    await page.screenshot({ path: 'chart_tooltip_th.png' });
  }

  // hover the Mythos/Fable 5 prediction: find its registered dot position
  const pos = await page.evaluate(() => {
    const svg = document.querySelector('svg');
    if (!svg) return null;
    const texts = [...document.querySelectorAll('text')];
    const t = texts.find(el => el.textContent === 'Mythos 5');
    if (!t) return null;
    const r = t.getBoundingClientRect();
    return { x: r.left - 14, y: r.top + r.height / 2 + 8 };
  });
  if (pos) {
    await page.mouse.move(pos.x, pos.y);
    await page.waitForTimeout(600);
    await page.screenshot({ path: 'chart_tooltip.png' });
    await page.mouse.move(60, 60);
    await page.waitForTimeout(300);
  }

  // switch prediction basis to pooled ECI and re-hover Mythos 5
  await page.getByRole('button', { name: 'ECI pooled' }).click();
  await page.waitForTimeout(600);
  if (pos) {
    const p2 = await page.evaluate(() => {
      const t = [...document.querySelectorAll('text')].find(el => el.textContent === 'Mythos 5');
      if (!t) return null;
      const r = t.getBoundingClientRect();
      return { x: r.left - 14, y: r.top + r.height / 2 + 8 };
    });
    if (p2) { await page.mouse.move(p2.x, p2.y); await page.waitForTimeout(600); }
  }
  await page.screenshot({ path: 'chart_basis_eci.png' });
  await page.getByRole('button', { name: 'per-lab default' }).click();
  await page.waitForTimeout(300);

  // Slowdown scenario is off by default, so opt in to keep the decel curve
  // covered. Its toggle is labelled with the start year, which defaults to one
  // year out, hence the regex rather than a fixed string.
  await page.getByRole('button', { name: 'Time horizon' }).click();
  await page.waitForTimeout(600);
  const decelToggle = page.getByText(/^\d{4} slowdown$/).first();
  await decelToggle.click();
  await page.waitForTimeout(800);
  // Assert on the drawn curve, not the legend: the legend entry renders
  // unconditionally, while the decel <Line>'s data is null until it is enabled,
  // leaving an empty path. COL.decel is the purple used only by that series.
  const decelDrawn = () => page.evaluate(() =>
    [...document.querySelectorAll('path')].some(p =>
      (p.getAttribute('stroke') || '').toLowerCase() === '#c084fc' &&
      (p.getAttribute('d') || '').length > 10));
  if (!await decelDrawn()) failures.push('slowdown enabled: decel curve not drawn');
  await page.screenshot({ path: 'chart_decel.png' });
  await decelToggle.click(); // back to default (off)
  await page.waitForTimeout(800);
  if (await decelDrawn()) failures.push('slowdown off: decel curve still drawn');

  // tested-only toggle: TH view hides diamonds; ECI view refits to measured
  await page.getByText('Show tested models only').click();
  await page.waitForTimeout(600);
  await page.screenshot({ path: 'chart_th_tested.png' });
  await page.getByRole('button', { name: 'ECI', exact: true }).click();
  await page.waitForTimeout(800);
  await page.screenshot({ path: 'chart_eci_tested.png' });

  console.log('pageerrors:', errors.length ? errors : 'none');
  console.log('assertions:', failures.length ? failures : 'all passed');
  if (errors.length || failures.length) process.exitCode = 1;
  await browser.close();
})();
