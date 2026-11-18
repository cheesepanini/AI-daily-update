// Run against a local test site (with reviewed textbook content) or production:
// PLAYWRIGHT_MODULE=/path/to/playwright node scripts/check_graph_interactions.cjs [base URL]
const assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.argv[2] || 'http://localhost:8765';
const errors = [];

async function camera(page) {
  return page.locator('#graph-stage').evaluate(element => {
    const {a, e, f} = new DOMMatrix(getComputedStyle(element).transform);
    return {zoom: a, x: e, y: f};
  });
}
async function settle(page) {
  await page.evaluate(async () => {
    const stage = document.getElementById('graph-stage');
    let previous = '', stable = 0;
    for (let frame = 0; frame < 180; frame++) {
      await new Promise(requestAnimationFrame);
      const transform = stage.style.transform;
      stable = transform === previous ? stable + 1 : 0;
      previous = transform;
      if (stable >= 3) return;
    }
    throw new Error('Graph camera did not settle');
  });
}

async function checkNodeSpacing(page) {
  const result = await page.evaluate(() => {
    const nodes = [...document.querySelectorAll('.graph-node')];
    const points = nodes.map(node => ({x: parseFloat(node.style.left), y: parseFloat(node.style.top),
                                      radius: parseFloat(node.style.getPropertyValue('--node-size')) / 2}));
    let deficit = 0;
    for (let i = 0; i < points.length; i++) for (let j = i + 1; j < points.length; j++) {
      const a = points[i], b = points[j];
      deficit = Math.max(deficit, Math.max(42, a.radius + b.radius + 18) - Math.hypot(a.x - b.x, a.y - b.y));
    }
    const blocked = nodes.filter(node => {
      const rect = node.getBoundingClientRect();
      return document.elementFromPoint(rect.x + rect.width / 2, rect.y + rect.height / 2)?.closest('.graph-node') !== node;
    }).map(node => node.dataset.graphId);
    return {deficit, blocked};
  });
  assert(result.deficit < .5, `Crowded graph nodes: ${JSON.stringify(result)}`);
  assert.deepEqual(result.blocked, [], 'Every node center must be independently clickable in overview');
}

async function checkGraphVisible(page) {
  assert(await page.locator('#graph-viewport').evaluate(view => {
    const rect = view.getBoundingClientRect();
    const inset = Math.min(72, view.clientWidth / 4, view.clientHeight / 4);
    return [...view.querySelectorAll('.graph-node')].some(node => {
      const point = node.getBoundingClientRect();
      const x = point.x + point.width / 2 - rect.left - view.clientLeft;
      const y = point.y + point.height / 2 - rect.top - view.clientTop;
      return x >= inset - .1 && x <= view.clientWidth - inset + .1 && y >= inset - .1 && y <= view.clientHeight - inset + .1;
    });
  }), 'The graph must retain a node within the usable viewport after navigation');
}

(async () => {
  const browser = await chromium.launch({
    ...(process.env.CHROME_PATH ? {executablePath: process.env.CHROME_PATH} : {}),
    headless: true,
  });
  try {
    const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(`${base}/learn`);
    const node = page.locator('.graph-node[data-kind="concept"]').first();
    await node.waitFor();
    await settle(page);
    const total = await page.locator('.graph-node').count();
    assert(total > 0);
    await checkNodeSpacing(page);
    const overviewZoom = (await camera(page)).zoom;

    await node.hover();
    assert(await page.locator('#graph-preview').isVisible());
    assert((await page.locator('#graph-preview-summary').innerText()).length > 0);
    assert(await page.locator('.graph-neighbor').count() > 1);
    await page.locator('#graph-preview-read').hover();
    await page.waitForTimeout(220); // Cross the delayed hover-dismiss window.
    assert(await page.locator('#graph-preview').isVisible());
    await page.mouse.move(30, 125);
    await page.waitForFunction(() => document.getElementById('graph-preview').hidden);

    await node.click();
    await page.mouse.move(30, 125);
    await page.waitForTimeout(220);
    assert((await page.locator('#graph-preview-kind').innerText()).includes('已固定'));
    assert((await page.locator('#graph-preview-read').getAttribute('href')).includes('/learn/concepts/'));
    await page.keyboard.press('Escape');
    assert(await page.locator('#graph-preview').isHidden());

    const view = await page.locator('#graph-viewport').boundingBox();
    const anchor = {x: view.width * .35, y: view.height * .35};
    const before = await camera(page);
    await page.mouse.move(view.x + anchor.x + 1, view.y + anchor.y + 1);
    await page.mouse.wheel(0, -120);
    await settle(page);
    const after = await camera(page);
    assert(after.zoom > before.zoom);
    assert(Math.abs((anchor.x - before.x) / before.zoom - (anchor.x - after.x) / after.zoom) < 1);
    assert(Math.abs((anchor.y - before.y) / before.zoom - (anchor.y - after.y) / after.zoom) < 1);
    for (let i = 0; i < 8; i++) await page.mouse.wheel(0, -80);
    await settle(page);
    assert((await camera(page)).zoom <= 3.001);
    assert(await page.locator('#graph-zoom-in').isDisabled());
    await page.locator('#graph-viewport').focus();
    for (const key of ['ArrowLeft', 'ArrowUp', 'ArrowRight', 'ArrowDown']) {
      await page.locator('#graph-viewport').evaluate((view, key) => {
        for (let n = 0; n < 100; n++) view.dispatchEvent(new KeyboardEvent('keydown', {key, bubbles: true}));
      }, key);
      await settle(page);
      await checkGraphVisible(page);
    }
    for (const direction of [1, -1]) {
      const x = view.x + view.width / 2, y = view.y + view.height / 2;
      await page.mouse.move(x, y);
      await page.mouse.down();
      await page.mouse.move(x + 12, y + 12);
      await page.mouse.move(x + direction * 8000, y + direction * 5000);
      await page.mouse.up();
      await settle(page);
      await checkGraphVisible(page);
    }
    await page.mouse.move(view.x + view.width / 2, view.y + view.height / 2);
    for (let n = 0; n < 12; n++) await page.mouse.wheel(0, 1000);
    await settle(page);
    assert(Math.abs((await camera(page)).zoom - overviewZoom) < .001, 'Zooming out must stop at overview');
    assert(await page.locator('#graph-zoom-out').isDisabled());
    await checkGraphVisible(page);
    await page.locator('#graph-fit').click();
    await settle(page);
    await checkNodeSpacing(page);

    const point = await node.boundingBox();
    const start = await camera(page);
    await page.mouse.move(point.x + point.width / 2, point.y + point.height / 2);
    await page.mouse.down();
    await page.mouse.move(point.x + point.width / 2 + 80, point.y + point.height / 2 + 45, {steps: 8});
    await page.mouse.up();
    await settle(page);
    assert(Math.abs((await camera(page)).x - start.x - 80) < 1);
    assert(new URL(page.url()).pathname === '/learn');
    assert(await page.locator('#graph-preview').isHidden());

    await page.locator('#graph-viewport').focus();
    const keyStart = await camera(page);
    await page.keyboard.press('+');
    await settle(page);
    assert((await camera(page)).zoom > keyStart.zoom);
    await page.keyboard.press('0');
    await settle(page);
    const title = await node.getAttribute('aria-label');
    await page.locator('#graph-search').fill(title);
    await page.locator('#graph-search').press('Enter');
    await settle(page);
    assert(await node.evaluate(element => element.classList.contains('graph-located')));

    const id = await node.getAttribute('data-graph-id');
    await page.evaluate(id => document.getElementById('learning-plan-result').dispatchEvent(new CustomEvent('textbook-plan', {
      detail: {title: '交互验证路径', target_ids: [id], steps: [{id}]},
    })), id);
    await settle(page);
    assert(await node.evaluate(element => element.classList.contains('graph-target')));
    assert(await page.locator('#graph-path-legend').isVisible());
    await page.locator('#graph-preview-read').click();
    await page.waitForURL('**/learn/concepts/**');
    assert((await page.locator('main').innerText()).includes(title));

    const mobile = await browser.newPage({viewport: {width: 390, height: 844}, isMobile: true, hasTouch: true});
    mobile.on('pageerror', error => errors.push(error.message));
    await mobile.goto(`${base}/learn`);
    await mobile.locator('.graph-node').first().waitFor();
    await settle(mobile);
    await checkNodeSpacing(mobile);
    await mobile.locator('.graph-node[data-kind="chapter"]').first().tap();
    assert(await mobile.locator('#graph-preview').isVisible());
    const card = await mobile.locator('#graph-preview').boundingBox();
    assert(card.x >= 0 && card.x + card.width <= 390);
    await mobile.locator('#graph-preview-close').tap();
    const bounds = await mobile.locator('#graph-viewport').boundingBox();
    const touch = await mobile.context().newCDPSession(mobile);
    const center = {x: bounds.x + bounds.width / 2, y: bounds.y + bounds.height / 2};
    const touchPoints = distance => [{x: center.x - distance, y: center.y, id: 1}, {x: center.x + distance, y: center.y, id: 2}];
    const pinchStart = await camera(mobile);
    await touch.send('Input.dispatchTouchEvent', {type: 'touchStart', touchPoints: touchPoints(35)});
    await touch.send('Input.dispatchTouchEvent', {type: 'touchMove', touchPoints: touchPoints(70)});
    await touch.send('Input.dispatchTouchEvent', {type: 'touchEnd', touchPoints: []});
    await settle(mobile);
    assert((await camera(mobile)).zoom > pinchStart.zoom * 1.5);
    await touch.send('Input.dispatchTouchEvent', {type: 'touchStart', touchPoints: [{...center, id: 1}]});
    await touch.send('Input.dispatchTouchEvent', {type: 'touchMove', touchPoints: [{x: center.x + 16, y: center.y + 16, id: 1}]});
    await touch.send('Input.dispatchTouchEvent', {type: 'touchMove', touchPoints: [{x: center.x + 3000, y: center.y - 3000, id: 1}]});
    await touch.send('Input.dispatchTouchEvent', {type: 'touchEnd', touchPoints: []});
    await settle(mobile);
    await checkGraphVisible(mobile);
    await mobile.setViewportSize({width: 844, height: 390});
    await settle(mobile);
    await checkGraphVisible(mobile);
    assert(await mobile.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await mobile.emulateMedia({reducedMotion: 'reduce'});
    await mobile.locator('#graph-zoom-in').tap();
    await settle(mobile);
    assert.deepEqual(errors, []);
    console.log(`Graph checks passed: ${total} separated clickable nodes, bounded pan/zoom, hover/pin, keyboard, search, path, touch pinch, resize, reduced motion.`);
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
