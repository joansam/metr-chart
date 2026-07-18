#!/usr/bin/env node
// Screenshot harness for index.html in sandboxed environments where
// cdnjs.cloudflare.com is blocked: the pinned UMD libs are fetched from the
// npm registry (usually allowlisted) on first run, then served to the page by
// intercepting the CDN requests. Serves the repo root itself — no separate
// web server needed.
//
// Usage: NODE_PATH=$(npm root -g) node tools/shot.js [width] [height] [out.png] [hoverText]
//   e.g. node tools/shot.js 1600 1000 desktop.png "2026 slowdown"
// Requires a global playwright install and a chromium at /opt/pw-browsers/chromium
// (or set PW_CHROMIUM to the executable path).
const { chromium } = require('playwright');
const { execSync } = require('child_process');
const fs = require('fs'), path = require('path'), http = require('http');

const ROOT = path.join(__dirname, '..');
const LIBS = path.join(__dirname, '.libs');
// package@version -> file inside the package matching the cdnjs basename
const DEPS = {
  'react@18.2.0': 'umd/react.production.min.js',
  'react-dom@18.2.0': 'umd/react-dom.production.min.js',
  'prop-types@15.8.1': 'prop-types.min.js',
  'recharts@2.15.3': ['umd/Recharts.js', 'Recharts.min.js'],
  '@babel/standalone@7.23.9': 'babel.min.js',
};

function ensureLibs() {
  if (fs.existsSync(LIBS) && fs.readdirSync(LIBS).length >= 5) return;
  fs.mkdirSync(LIBS, { recursive: true });
  const tmp = fs.mkdtempSync(path.join(require('os').tmpdir(), 'shot-libs-'));
  execSync(`npm install --prefix ${tmp} --no-audit --no-fund ${Object.keys(DEPS).join(' ')}`, { stdio: 'inherit' });
  for (const [pkg, spec] of Object.entries(DEPS)) {
    const name = pkg.slice(0, pkg.lastIndexOf('@'));
    const [src, dst] = Array.isArray(spec) ? spec : [spec, path.basename(spec)];
    fs.copyFileSync(path.join(tmp, 'node_modules', name, src), path.join(LIBS, dst));
  }
}

(async () => {
  const [w, h, out, hover] = [+(process.argv[2] || 1600), +(process.argv[3] || 1000),
    process.argv[4] || 'shot.png', process.argv[5]];
  ensureLibs();
  const srv = http.createServer((req, res) => {
    const f = path.join(ROOT, req.url === '/' ? 'index.html' : req.url.split('?')[0]);
    fs.existsSync(f) ? res.end(fs.readFileSync(f)) : (res.statusCode = 404, res.end());
  }).listen(0);
  const port = srv.address().port;
  const b = await chromium.launch({ executablePath: process.env.PW_CHROMIUM || '/opt/pw-browsers/chromium' });
  const pg = await b.newPage({ viewport: { width: w, height: h } });
  const errs = [];
  pg.on('pageerror', e => errs.push(e.message));
  await pg.route('https://cdnjs.cloudflare.com/**', route => {
    const f = path.join(LIBS, path.basename(new URL(route.request().url()).pathname));
    fs.existsSync(f)
      ? route.fulfill({ contentType: 'application/javascript', body: fs.readFileSync(f) })
      : route.abort();
  });
  await pg.goto(`http://localhost:${port}/index.html`);
  await pg.waitForTimeout(3000); // babel-standalone compile + render
  if (hover) {
    const t = pg.locator('.tt', { hasText: hover }).first();
    if (await t.count()) { await t.hover(); await pg.waitForTimeout(400); }
  }
  await pg.screenshot({ path: out, fullPage: false });
  console.log(`wrote ${out} (${w}x${h}); page errors:`, errs.length ? errs.slice(0, 5) : 'none');
  await b.close();
  srv.close();
})();
