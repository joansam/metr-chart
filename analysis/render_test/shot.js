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

  // ── Finance section (Epoch AI-companies data) ──
  await page.getByText('AI Lab Finance Trends').scrollIntoViewIfNeeded();
  await page.waitForTimeout(600);
  // Finance trend lines are the only paths of a given color with dasharray
  // "8 4" (prediction diamonds use "3 2"), so the checks stay unambiguous even
  // for colors the top chart also draws.
  const trendDrawn = hex => page.evaluate(h =>
    [...document.querySelectorAll('path')].some(p =>
      (p.getAttribute('stroke') || '').toLowerCase() === h &&
      (p.getAttribute('stroke-dasharray') || '') === '8 4' &&
      (p.getAttribute('d') || '').length > 10), hex);
  if (!await trendDrawn('#2fbcd3')) failures.push('finance rev: xAI trend line not drawn');
  if (!await trendDrawn('#e069a8')) failures.push('finance rev: Z.ai (pink) trend line not drawn');
  // hover an xAI revenue dot → tooltip with the dollar figure
  const finDot = await page.evaluate(() => {
    const c = [...document.querySelectorAll('circle')].find(el =>
      el.getAttribute('fill') === '#2fbcd3' && el.getAttribute('r') === '4.5');
    if (!c) return null;
    c.scrollIntoView({ block: 'center' }); // taller chart: dots can sit below the fold
    const r = c.getBoundingClientRect();
    return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
  });
  if (!finDot) failures.push('finance rev: no xAI dots rendered');
  else {
    await page.mouse.move(finDot.x, finDot.y);
    await page.waitForTimeout(600);
    if (!await page.evaluate(() => document.body.innerText.includes('Annualized revenue:')))
      failures.push('finance rev: dot tooltip missing');
    await page.mouse.move(finDot.x + 200, finDot.y - 100);
    await page.waitForTimeout(300);
  }
  // hover the xAI trend LINE itself, 75% along its path (past the last xAI
  // dot, so the dots-win-over-lines priority can't intercept the hit)
  const xaiLinePt = () => page.evaluate(() => {
    const p = [...document.querySelectorAll('path')].find(el =>
      (el.getAttribute('stroke') || '').toLowerCase() === '#2fbcd3' &&
      (el.getAttribute('d') || '').length > 10);
    if (!p) return null;
    p.scrollIntoView({ block: 'center' });
    const pt = p.getPointAtLength(p.getTotalLength() * 0.75);
    const m = p.getScreenCTM();
    return { x: m.a*pt.x + m.c*pt.y + m.e, y: m.b*pt.x + m.d*pt.y + m.f };
  });
  const linePt = await xaiLinePt();
  if (!linePt) failures.push('finance rev: xAI trend path not found for line hover');
  else {
    await page.mouse.move(linePt.x, linePt.y);
    await page.waitForTimeout(600);
    if (!await page.evaluate(() => document.body.innerText.includes('xAI trend')))
      failures.push('finance rev: trend-line hover tooltip missing');
    if (!await page.evaluate(() => document.body.innerText.includes('Trend from last report')))
      failures.push('finance rev: anchored-trend reading missing from tooltip');
    await page.screenshot({ path: 'chart_fin_line_tip.png' });
    // 40px above the line is outside the 5px hit band: the tooltip should fade
    // (it stays in the DOM at opacity 0, like the main chart's, so test the
    // computed opacity rather than innerText)
    await page.mouse.move(linePt.x, linePt.y - 40);
    await page.waitForTimeout(1400);
    const tipVisible = await page.evaluate(() => {
      const d = [...document.querySelectorAll('div')].find(el =>
        el.textContent.startsWith('xAI trend') && el.style.position !== 'absolute');
      const box = d && d.closest('div[style*="absolute"]');
      return box ? parseFloat(getComputedStyle(box).opacity) > 0.05 : false;
    });
    if (tipVisible) failures.push('finance rev: trend tooltip did not fade off-line');
  }
  await page.screenshot({ path: 'chart_fin_rev.png' });
  // Valuations view: Mistral is fitted here (n=5) but not in revenue (n=2)
  await page.getByRole('button', { name: 'Valuations' }).click();
  await page.waitForTimeout(800);
  if (!await trendDrawn('#d4b24e')) failures.push('finance val: Mistral (gold) trend line not drawn');
  if (await trendDrawn('#e069a8')) failures.push('finance val: unexpected Z.ai trend (n=2, dots-only)');
  if (!await page.evaluate(() => document.body.innerText.includes('closed funding round')))
    failures.push('finance val: caption did not switch');
  await page.screenshot({ path: 'chart_fin_val.png' });
  await page.getByRole('button', { name: 'Revenue' }).click();
  await page.waitForTimeout(400);

  // wheel-zoom the finance chart (shared useZoomPan hook): Reset zoom appears,
  // and it must be the only one on the page (the main chart is not zoomed here)
  const zoomPt = await xaiLinePt(); // re-measure: view toggles may have scrolled
  if (zoomPt) {
    await page.mouse.move(zoomPt.x, zoomPt.y);
    await page.mouse.wheel(0, -300);
    await page.mouse.wheel(0, -300);
    await page.waitForTimeout(600);
    await page.screenshot({ path: 'chart_fin_zoom.png' });
    const resetBtns = page.getByText('Reset zoom');
    if (await resetBtns.count() !== 1)
      failures.push('finance zoom: expected exactly one Reset zoom button');
    else {
      await resetBtns.click();
      await page.waitForTimeout(400);
      if (await page.getByText('Reset zoom').count() !== 0)
        failures.push('finance zoom: Reset zoom did not clear');
    }
  }

  // legend chip toggle: hiding Anthropic removes exactly its trend path (the
  // top chart draws no #d97757 <path> strokes except prediction diamonds,
  // which stay — hence count-based assertions, not zero-checks)
  const anthPaths = () => page.evaluate(() =>
    [...document.querySelectorAll('path')].filter(p =>
      (p.getAttribute('stroke') || '').toLowerCase() === '#d97757' &&
      (p.getAttribute('d') || '').length > 10).length);
  const anthChip = page.getByText('Anthropic', { exact: true }).last(); // finance legend
  const nBefore = await anthPaths();
  await anthChip.click();
  await page.waitForTimeout(600);
  const nHidden = await anthPaths();
  if (nHidden !== nBefore - 1)
    failures.push(`finance toggle: expected ${nBefore - 1} anthropic paths, got ${nHidden}`);
  await page.screenshot({ path: 'chart_fin_toggle.png' });
  await anthChip.click();
  await page.waitForTimeout(600);
  if (await anthPaths() !== nBefore)
    failures.push('finance toggle: Anthropic did not restore');

  // "Trend from <last frontier point>" on the main chart's trend tooltips.
  // Re-enable derived points first: the anchor may be predicted/imputed (the
  // deliberate special case), so with everything shown TH anchors on Mythos
  // 5.1's predicted horizon and ECI on Mythos 5.1's imputed score.
  await page.getByText('Show tested models only').click();
  await page.waitForTimeout(600);
  await page.getByText('METR Time Horizon Trends').scrollIntoViewIfNeeded();
  await page.getByRole('button', { name: 'Time horizon' }).click();
  await page.waitForTimeout(800);
  await page.mouse.move(750, 300); // extrapolation region, right of every dot
  await page.waitForTimeout(600);
  if (!await page.evaluate(() => document.body.innerText.includes('Trend from Mythos 5.1')))
    failures.push('TH tooltip: anchored-trend reading missing (want predicted Mythos 5.1 anchor)');
  await page.screenshot({ path: 'chart_th_anchored.png' });
  await page.getByRole('button', { name: 'ECI', exact: true }).click();
  await page.waitForTimeout(800);
  await page.mouse.move(750, 300);
  await page.waitForTimeout(600);
  if (!await page.evaluate(() => document.body.innerText.includes('Trend from Mythos 5.1')))
    failures.push('ECI tooltip: anchored-trend reading missing (want imputed Mythos 5.1 anchor)');

  // ── Mobile: pinch zoom must stay continuous across a multi-step gesture ──
  // (regression test for the one-step-pinch bug: gesture state used to reset
  // on every zoom-induced re-render, so only the first touchmove applied)
  const mob = await browser.newPage({ viewport: { width: 390, height: 844 }, hasTouch: true });
  mob.on('pageerror', e => errors.push('mobile: ' + String(e)));
  await mob.route('**cdnjs.cloudflare.com/**', route => {
    const url = route.request().url();
    const hit = Object.keys(LOCAL).find(k => url.includes(k));
    if (hit) route.fulfill({ body: fs.readFileSync(path.join(NM, LOCAL[hit])),
                             contentType: 'application/javascript' });
    else route.abort();
  });
  await mob.goto('file://' + path.resolve(__dirname, '../../index.html'));
  await mob.waitForTimeout(4000);
  const mobCdp = await mob.context().newCDPSession(mob);
  const chartMid = await mob.evaluate(() => {
    const el = document.querySelector('.recharts-wrapper');
    el.scrollIntoView({ block: 'center' });
    const r = el.getBoundingClientRect();
    return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
  });
  // Compare the rendered x-tick label SEQUENCE, not the count — Recharts
  // hides overlapping labels, so the count is not monotonic in zoom level.
  const tickSig = () => mob.evaluate(() => {
    const svg = document.querySelector('svg');
    return [...svg.querySelectorAll('text')]
      .filter(t => /^(20\d\d|Jul '\d\d)$/.test(t.textContent))
      .map(t => t.textContent).join(',');
  });
  const sigFull = await tickSig();
  const pts = d => [{ x: chartMid.x - d, y: chartMid.y, id: 0 },
                    { x: chartMid.x + d, y: chartMid.y, id: 1 }];
  await mobCdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: pts(40) });
  let sigAfterOne = null;
  for (let d = 60; d <= 160; d += 20) {
    await mobCdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: pts(d) });
    await mob.waitForTimeout(120);
    if (sigAfterOne === null) sigAfterOne = await tickSig();
  }
  await mobCdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await mob.waitForTimeout(400);
  const sigAfterAll = await tickSig();
  // continuous pinch keeps shrinking the domain after the first step
  if (sigAfterOne === sigFull)
    failures.push('mobile pinch: first step did not zoom');
  if (sigAfterAll === sigAfterOne)
    failures.push(`mobile pinch: gesture died after one step (ticks stuck at "${sigAfterOne}")`);
  if (await mob.getByText('Reset zoom').count() < 1)
    failures.push('mobile pinch: Reset zoom button missing');
  await mob.screenshot({ path: 'chart_mobile_pinch.png' });
  await mob.close();

  console.log('pageerrors:', errors.length ? errors : 'none');
  console.log('assertions:', failures.length ? failures : 'all passed');
  if (errors.length || failures.length) process.exitCode = 1;
  await browser.close();
})();
