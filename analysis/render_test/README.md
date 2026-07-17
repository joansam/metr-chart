# Render smoke test

`npm install && npm test` renders `index.html` in headless Chromium with the
CDN scripts routed to local npm copies (works in sandboxes that block
cdnjs.cloudflare.com). It walks the p50/p80 toggle, the ECI/AECI y-axis modes,
tooltips, wheel zoom, the prediction-basis selector, and the tested-only
toggle, writing a screenshot per state and printing any console errors.

Set `CHROMIUM_PATH` if Chromium isn't at `/opt/pw-browsers/chromium`.
Keep the pinned versions in sync with the `<script>` tags in `index.html`.
