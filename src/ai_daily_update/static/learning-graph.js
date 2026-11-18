(() => {
  const byId = id => document.getElementById(id);
  const chapters = JSON.parse(byId('textbook-graph-data').textContent);
  const viewport = byId('graph-viewport');
  const stage = byId('graph-stage');
  const canvas = byId('graph-edges');
  const status = byId('graph-status');
  const links = new Map([...stage.querySelectorAll('[data-graph-id]')].map(link => [link.dataset.graphId, link]));
  const chapterByNumber = new Map(chapters.map(chapter => [chapter.number, chapter]));
  const nodes = new Map(chapters.flatMap(chapter => [
    ...(chapter.id ? [chapter] : []), ...chapter.nodes,
  ]).map(node => [node.id, node]));
  const width = 1400;
  const height = 940;
  const positions = new Map();
  const edges = [...nodes.values()].flatMap(node => ['required', 'helpful'].flatMap(kind =>
    (node[kind] || []).map(source => ({ source, target: node.id, kind }))));
  const degree = new Map();
  for (const {source, target} of edges) {
    degree.set(source, (degree.get(source) || 0) + 1);
    degree.set(target, (degree.get(target) || 0) + 1);
  }
  const goldenAngle = Math.PI * (3 - Math.sqrt(5));
  function place(id, x, y, radius) {
    positions.set(id, {x, y, radius});
    const link = links.get(id);
    link.style.left = `${x}px`;
    link.style.top = `${y}px`;
    link.style.setProperty('--node-size', `${radius * 2}px`);
    link.classList.toggle('graph-label-left', x > width - 250);
  }
  for (const [index, chapter] of chapters.entries()) {
    const angle = index * (2 * Math.PI / chapters.length) - Math.PI / 2;
    const x = width / 2 + Math.cos(angle) * 400;
    const y = height / 2 + Math.sin(angle) * 265;
    if (chapter.id) place(chapter.id, x, y, 15 + Math.min(chapter.nodes.length / 9, 7));
    const members = chapter.nodes.slice().sort((a, b) =>
      Number(b.type === 'concept') - Number(a.type === 'concept') ||
      (degree.get(b.id) || 0) - (degree.get(a.id) || 0));
    for (const [position, node] of members.entries()) {
      const spread = 22 + 18 * Math.sqrt(position + 1);
      const theta = angle + Math.PI + position * goldenAngle;
      const concept = node.type === 'concept';
      const connections = degree.get(node.id) || 0;
      const radius = concept ? 8 + Math.min(connections / 2, 5) : 5;
      const inward = concept ? Math.min(150, connections * 15) : 0;
      place(node.id, x + spread * Math.cos(theta) - inward * Math.cos(angle),
                     y + spread * Math.sin(theta) - inward * Math.sin(angle), radius);
      if (concept && position < 3) links.get(node.id).classList.add('graph-major');
      // A section reference can put the same knowledge point in more than one chapter.
      const groups = new Set([chapter.number, ...node.sections.map(section => section.split('.')[0])]);
      for (const group of groups) {
        const hub = chapterByNumber.get(group)?.id;
        if (hub) edges.push({source: hub, target: node.id, kind: 'membership'});
      }
    }
  }
  const particles = [...positions].map(([id, point]) => ({id, point, fixed: links.get(id).dataset.kind === 'chapter'}));
  // ponytail: bounded O(n²) layout at load; spatial bins if the catalog grows.
  for (let pass = 0; pass < 160; pass++) {
    let overlap = 0;
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const a = particles[i], b = particles[j];
        if (a.fixed && b.fixed) continue;
        let dx = b.point.x - a.point.x, dy = b.point.y - a.point.y;
        const minimum = Math.max(42, a.point.radius + b.point.radius + 18);
        const squaredDistance = dx * dx + dy * dy;
        if (squaredDistance >= minimum * minimum) continue;
        let distance = Math.sqrt(squaredDistance);
        if (!distance) { dx = Math.cos(j * goldenAngle); dy = Math.sin(j * goldenAngle); distance = 1; }
        const push = (minimum - distance) / distance / (a.fixed || b.fixed ? 1 : 2);
        if (!a.fixed) { a.point.x -= dx * push; a.point.y -= dy * push; }
        if (!b.fixed) { b.point.x += dx * push; b.point.y += dy * push; }
        overlap = Math.max(overlap, minimum - distance);
      }
    }
    for (const {point, fixed} of particles) {
      if (fixed) continue;
      point.x = Math.max(point.radius + 32, Math.min(width - point.radius - 32, point.x));
      point.y = Math.max(point.radius + 32, Math.min(height - point.radius - 32, point.y));
    }
    if (overlap < .1) break;
  }
  for (const {id, point} of particles) place(id, point.x, point.y, point.radius);
  const contentBounds = {
    left: Math.min(...[...positions.values()].map(point => point.x - point.radius)),
    right: Math.max(...[...positions.values()].map(point => point.x + point.radius)),
    top: Math.min(...[...positions.values()].map(point => point.y - point.radius)),
    bottom: Math.max(...[...positions.values()].map(point => point.y + point.radius)),
  };
  let zoom = 1;
  let pathIds = new Set();
  let camera = {x: 0, y: 0, zoom: 1};
  let target = {...camera};
  let animation;
  let lastFrame = 0;
  let renderedZoom;
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');

  function renderCamera(time) {
    const blend = reducedMotion.matches ? 1 : 1 - Math.exp(-Math.min(time - lastFrame, 64) / 45);
    lastFrame = time;
    let moving = false;
    for (const key of ['x', 'y', 'zoom']) {
      camera[key] += (target[key] - camera[key]) * blend;
      if (Math.abs(target[key] - camera[key]) < (key === 'zoom' ? .0001 : .05)) camera[key] = target[key];
      else moving = true;
    }
    stage.style.transform = `translate(${camera.x}px, ${camera.y}px) scale(${camera.zoom})`;
    if (renderedZoom !== camera.zoom) {
      renderedZoom = camera.zoom;
      stage.style.setProperty('--graph-label-size', `${Math.max(15, 10 / camera.zoom)}px`);
      stage.style.setProperty('--graph-hit-size', `${Math.min(36, 24 / camera.zoom)}px`);
      stage.classList.toggle('graph-compact', camera.zoom < .95);
    }
    positionPreview();
    animation = moving ? requestAnimationFrame(renderCamera) : null;
  }

  function fitZoom() {
    return Math.min((viewport.clientWidth - 48) / width, (viewport.clientHeight - 80) / height, 1);
  }

  function moveCamera(next, immediate = false) {
    const inset = Math.min(72, viewport.clientWidth / 4, viewport.clientHeight / 4);
    next = {...next, zoom: Math.max(fitZoom(), Math.min(3, next.zoom))};
    function bound(value, start, end, size) {
      const overlap = .8 * Math.min(size, (end - start) * next.zoom);
      return Math.max(overlap - end * next.zoom, Math.min(size - overlap - start * next.zoom, value));
    }
    next.x = bound(next.x, contentBounds.left, contentBounds.right, viewport.clientWidth);
    next.y = bound(next.y, contentBounds.top, contentBounds.bottom, viewport.clientHeight);
    const points = [...positions.values()].map(point => ({x: next.x + point.x * next.zoom, y: next.y + point.y * next.zoom}));
    const inside = point => point.x >= inset && point.x <= viewport.clientWidth - inset &&
                            point.y >= inset && point.y <= viewport.clientHeight - inset;
    if (!points.some(inside)) {
      const offset = point => ({x: Math.max(inset, Math.min(viewport.clientWidth - inset, point.x)) - point.x,
                               y: Math.max(inset, Math.min(viewport.clientHeight - inset, point.y)) - point.y});
      const closest = points.map(offset).reduce((best, point) => Math.hypot(point.x, point.y) < Math.hypot(best.x, best.y) ? point : best);
      next.x += closest.x;
      next.y += closest.y;
    }
    target = next;
    zoom = target.zoom;
    if (immediate || reducedMotion.matches) camera = {...target};
    byId('graph-zoom-out').disabled = zoom <= fitZoom() + .0001;
    byId('graph-zoom-in').disabled = zoom >= 3;
    byId('graph-zoom-value').value = `${Math.round(zoom * 100)}%`;
    status.textContent = `缩放 ${Math.round(zoom * 100)}%`;
    if (!animation) {
      lastFrame = performance.now();
      animation = requestAnimationFrame(renderCamera);
    }
  }

  function centerOn(x, y) {
    moveCamera({x: viewport.clientWidth / 2 - x * zoom, y: viewport.clientHeight / 2 - y * zoom, zoom});
  }

  function setZoom(value, anchor = {x: viewport.clientWidth / 2, y: viewport.clientHeight / 2}) {
    const nextZoom = Math.max(fitZoom(), Math.min(3, value));
    const ratio = nextZoom / zoom;
    moveCamera({x: anchor.x - (anchor.x - target.x) * ratio,
                y: anchor.y - (anchor.y - target.y) * ratio, zoom: nextZoom});
  }

  function fit() {
    hidePreview();
    setZoom(fitZoom());
    centerOn(width / 2, height / 2);
  }

  function fitPath() {
    const points = [...pathIds].map(id => positions.get(id)).filter(Boolean);
    if (!points.length) return;
    const xs = points.map(point => point.x);
    const ys = points.map(point => point.y);
    const left = Math.min(...xs), right = Math.max(...xs);
    const top = Math.min(...ys), bottom = Math.max(...ys);
    setZoom(Math.min(viewport.clientWidth / (right - left + 180),
                     viewport.clientHeight / (bottom - top + 120), 1.2));
    centerOn((left + right) / 2, (top + bottom) / 2);
    viewport.scrollIntoView({block: 'nearest', inline: 'nearest'});
  }

  function drawEdges() {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, width, height);
    const active = pathIds.size > 0 || activeId;
    const styles = {
      membership: [active ? '#51618135' : '#8499ba70', 1.4],
      helpful: [active ? '#7f99c542' : '#98afd096', 1.7],
      required: [active ? '#87e6d050' : '#87e6d0b3', 2.1],
    };
    const selected = edge => edge.kind === 'required' && pathIds.has(edge.source) && pathIds.has(edge.target);
    for (const edge of [...edges.filter(edge => !selected(edge)), ...edges.filter(selected)]) {
      const from = positions.get(edge.source);
      const to = positions.get(edge.target);
      if (!from || !to) continue;
      const highlight = selected(edge);
      const connected = edge.source === activeId || edge.target === activeId;
      [ctx.strokeStyle, ctx.lineWidth] = highlight ? ['#ffd580', 4] :
        connected ? [edge.kind === 'required' ? '#87e6d0' : '#c4b5fd', 2.8] : styles[edge.kind];
      ctx.setLineDash(edge.kind === 'helpful' ? [6, 5] : []);
      const angle = Math.atan2(to.y - from.y, to.x - from.x);
      const tipX = to.x - (to.radius + 3) * Math.cos(angle);
      const tipY = to.y - (to.radius + 3) * Math.sin(angle);
      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      ctx.lineTo(tipX, tipY);
      if (highlight) {
        ctx.moveTo(tipX - 12 * Math.cos(angle - .5), tipY - 12 * Math.sin(angle - .5));
        ctx.lineTo(tipX, tipY);
        ctx.lineTo(tipX - 12 * Math.cos(angle + .5), tipY - 12 * Math.sin(angle + .5));
      }
      ctx.stroke();
    }
  }

  function locate(id) {
    const link = links.get(id);
    if (!link) return;
    stage.querySelector('.graph-located')?.classList.remove('graph-located');
    link.classList.add('graph-located');
    hidePreview();
    if (zoom < .75) setZoom(1);
    const {x, y} = positions.get(id);
    centerOn(x, y);
    viewport.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    link.focus({ preventScroll: true });
  }

  const preview = byId('graph-preview');
  let activeId = null;
  let pinned = false;
  let previewTimer;
  const neighbors = new Map([...nodes.keys()].map(id => [id, new Set([id])]));
  for (const {source, target} of edges) {
    neighbors.get(source)?.add(target);
    neighbors.get(target)?.add(source);
  }

  function positionPreview() {
    if (!activeId || preview.hidden) return;
    const point = positions.get(activeId);
    const x = camera.x + point.x * camera.zoom;
    const y = camera.y + point.y * camera.zoom;
    const gap = point.radius * camera.zoom + 18;
    const maxX = viewport.clientWidth - preview.offsetWidth - 12;
    const left = x + gap <= maxX ? x + gap : x - gap - preview.offsetWidth;
    preview.style.left = `${Math.max(12, Math.min(maxX, left))}px`;
    preview.style.top = `${Math.max(12, Math.min(viewport.clientHeight - preview.offsetHeight - 72, y - 28))}px`;
  }

  function hidePreview() {
    clearTimeout(previewTimer);
    if (!activeId) return;
    links.get(activeId)?.removeAttribute('aria-describedby');
    activeId = null;
    pinned = false;
    preview.hidden = true;
    stage.classList.remove('graph-has-hover');
    for (const link of links.values()) link.classList.remove('graph-hovered', 'graph-neighbor');
    drawEdges();
  }

  function showPreview(id, pin = false) {
    clearTimeout(previewTimer);
    if (pinned && !pin) return;
    if (activeId) links.get(activeId)?.removeAttribute('aria-describedby');
    activeId = id;
    pinned = pin;
    const node = nodes.get(id);
    const kind = node.type === 'concept' ? '概念' : node.type === 'microtopic' ? '细知识点' : '章节导读';
    byId('graph-preview-kind').textContent = `${kind} · 教材 ${(node.sections || []).join('、')}${pin ? ' · 已固定' : ''}`;
    byId('graph-preview-title').textContent = node.title;
    byId('graph-preview-summary').textContent = node.summary || '查看完整内容，了解本知识点的解释与示例。';
    const required = (node.required || []).map(id => nodes.get(id)?.title).filter(Boolean);
    byId('graph-preview-relations').textContent = required.length ? `先修：${required.join('、')}` :
      `直接关联 ${neighbors.get(id).size - 1} 个节点`;
    byId('graph-preview-read').href = links.get(id).href;
    links.get(id).setAttribute('aria-describedby', 'graph-preview-title graph-preview-summary');
    for (const [nodeId, link] of links) {
      link.classList.toggle('graph-hovered', nodeId === id);
      link.classList.toggle('graph-neighbor', neighbors.get(id).has(nodeId));
    }
    stage.classList.add('graph-has-hover');
    preview.hidden = false;
    positionPreview();
    drawEdges();
  }

  function scheduleHide() {
    clearTimeout(previewTimer);
    if (!pinned) previewTimer = setTimeout(() => {
      if (!preview.contains(document.activeElement) && !stage.contains(document.activeElement)) hidePreview();
    }, 180);
  }
  for (const [id, link] of links) {
    link.addEventListener('pointerenter', event => {
      if (event.pointerType !== 'touch' && !pointers.size && performance.now() >= suppressClickUntil) showPreview(id);
    });
    link.addEventListener('pointerleave', scheduleHide);
    link.addEventListener('focus', () => showPreview(id, pinned));
    link.addEventListener('blur', scheduleHide);
    link.addEventListener('click', event => {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      showPreview(id, true);
    });
    link.draggable = false;
  }
  preview.addEventListener('pointerenter', () => clearTimeout(previewTimer));
  preview.addEventListener('pointerleave', scheduleHide);
  preview.addEventListener('focusin', () => clearTimeout(previewTimer));
  preview.addEventListener('focusout', scheduleHide);
  byId('graph-preview-close').addEventListener('click', () => {
    viewport.focus({preventScroll: true});
    hidePreview();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !preview.hidden) {
      const restoreFocus = preview.contains(document.activeElement);
      hidePreview();
      if (restoreFocus) viewport.focus({preventScroll: true});
    }
  });

  function text(parent, tag, value) {
    const element = document.createElement(tag);
    element.textContent = value;
    parent.append(element);
    return element;
  }
  function readLink(parent, node, label = node.title) {
    const link = text(parent, 'a', label);
    link.href = links.get(node.id).href;
  }
  function locateButton(parent, node, label = '定位') {
    const button = text(parent, 'button', label);
    button.type = 'button';
    button.addEventListener('click', () => locate(node.id));
  }

  byId('graph-zoom-in').addEventListener('click', () => setZoom(zoom * 1.25));
  byId('graph-zoom-out').addEventListener('click', () => setZoom(zoom / 1.25));
  byId('graph-fit').addEventListener('click', fit);
  const pointers = new Map();
  let gesture = null;
  let suppressClickUntil = 0;
  function pointerGeometry() {
    const points = [...pointers.values()];
    const first = points[0], second = points[1] || first;
    const rect = viewport.getBoundingClientRect();
    return {x: (first.x + second.x) / 2 - rect.left - viewport.clientLeft,
            y: (first.y + second.y) / 2 - rect.top - viewport.clientTop,
            distance: Math.hypot(second.x - first.x, second.y - first.y)};
  }
  viewport.addEventListener('pointerdown', event => {
    if (event.button !== 0) return;
    pointers.set(event.pointerId, {x: event.clientX, y: event.clientY});
    gesture = {...pointerGeometry(), camera: {...camera}};
  });
  viewport.addEventListener('pointermove', event => {
    if (!pointers.has(event.pointerId)) return;
    pointers.set(event.pointerId, {x: event.clientX, y: event.clientY});
    const point = pointerGeometry();
    if (pointers.size === 1 && Math.hypot(point.x - gesture.x, point.y - gesture.y) < 5 && !viewport.classList.contains('dragging')) return;
    hidePreview();
    viewport.classList.add('dragging');
    viewport.setPointerCapture(event.pointerId);
    suppressClickUntil = performance.now() + 400;
    const scale = gesture.distance > 0 ? point.distance / gesture.distance : 1;
    const nextZoom = Math.max(fitZoom(), Math.min(3, gesture.camera.zoom * scale));
    const ratio = nextZoom / gesture.camera.zoom;
    moveCamera({x: point.x - (gesture.x - gesture.camera.x) * ratio,
                y: point.y - (gesture.y - gesture.camera.y) * ratio, zoom: nextZoom}, true);
  });
  function endPointer(event) {
    pointers.delete(event.pointerId);
    if (pointers.size) gesture = {...pointerGeometry(), camera: {...camera}};
    else { gesture = null; viewport.classList.remove('dragging'); }
  }
  viewport.addEventListener('pointerup', endPointer);
  viewport.addEventListener('pointercancel', endPointer);
  viewport.addEventListener('lostpointercapture', endPointer);
  window.addEventListener('pointerup', endPointer);
  viewport.addEventListener('click', event => {
    if (performance.now() < suppressClickUntil) { event.preventDefault(); event.stopPropagation(); }
    else if (!event.target.closest('a')) hidePreview();
  }, true);
  viewport.addEventListener('wheel', event => {
    event.preventDefault();
    hidePreview();
    const rect = viewport.getBoundingClientRect();
    const delta = event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? viewport.clientHeight : 1);
    setZoom(zoom * Math.exp(-Math.max(-160, Math.min(160, delta)) * .0025),
      {x: event.clientX - rect.left - viewport.clientLeft, y: event.clientY - rect.top - viewport.clientTop});
  }, {passive: false});
  viewport.addEventListener('keydown', event => {
    const pan = {ArrowLeft: [60, 0], ArrowRight: [-60, 0], ArrowUp: [0, 60], ArrowDown: [0, -60]}[event.key];
    if (pan) moveCamera({...target, x: target.x + pan[0], y: target.y + pan[1]});
    else if (event.key === '+' || event.key === '=') setZoom(zoom * 1.25);
    else if (event.key === '-') setZoom(zoom / 1.25);
    else if (event.key === '0') fit();
    else return;
    event.preventDefault();
  });

  const search = byId('graph-search');
  const results = byId('graph-search-results');
  let firstMatch;
  search.addEventListener('input', () => {
    const query = search.value.trim().toLowerCase();
    results.replaceChildren();
    results.hidden = !query;
    firstMatch = null;
    if (!query) return;
    const matches = [...nodes.values()].filter(node =>
      [node.title, ...(node.aliases || []), ...(node.sections || [])].some(value => value.toLowerCase().includes(query)));
    firstMatch = matches[0];
    text(results, 'p', matches.length ? `找到 ${matches.length} 项${matches.length > 10 ? '，显示前 10 项' : ''}` : '未找到匹配的知识点。');
    for (const node of matches.slice(0, 10)) {
      const row = text(results, 'div', '');
      locateButton(row, node, node.title);
      readLink(row, node, '阅读');
    }
  });
  search.addEventListener('keydown', event => {
    if (event.key === 'Enter' && firstMatch) locate(firstMatch.id);
  });

  byId('graph-plan-toggle').addEventListener('click', () => byId('graph-plan').showModal());
  const result = byId('learning-plan-result');
  result.addEventListener('textbook-plan', event => {
    const data = event.detail;
    const targets = new Set(data.target_ids || []);
    const stepsById = new Map(data.steps.map((step, index) => [step.id, index + 1]));
    pathIds = new Set(stepsById.keys());
    const sections = new Set([...targets].flatMap(id => nodes.get(id)?.sections || []));
    const relatedChapters = new Set([...sections].map(section => section.split('.')[0]));
    for (const [id, link] of links) {
      link.classList.toggle('graph-target', targets.has(id));
      link.classList.toggle('graph-prereq', pathIds.has(id) && !targets.has(id));
      if (stepsById.has(id)) link.dataset.step = stepsById.get(id);
      else delete link.dataset.step;
    }
    for (const chapter of chapters) {
      links.get(chapter.id)?.classList.toggle('graph-related', relatedChapters.has(chapter.number));
    }
    stage.classList.toggle('graph-has-path', pathIds.size > 0);
    byId('graph-path-legend').hidden = !pathIds.size;
    drawEdges();
    result.replaceChildren();
    text(result, 'h3', data.title);
    byId('graph-path-details').hidden = false;
    const showPath = text(result, 'button', '在图中定位整条路径');
    showPath.type = 'button';
    showPath.addEventListener('click', fitPath);
    text(result, 'h4', '直接相关章节');
    const chapterList = text(result, 'ul', '');
    for (const number of [...relatedChapters].sort((a, b) => Number(a) - Number(b))) {
      const chapter = chapterByNumber.get(number);
      const row = text(chapterList, 'li', `第 ${number} 章 · ${[...sections].filter(section => section.split('.')[0] === number).join('、')} `);
      if (chapter?.id) { locateButton(row, chapter); readLink(row, chapter, '读章节导读'); }
    }
    text(result, 'h4', '建议学习顺序');
    if (data.starting_note) text(result, 'p', data.starting_note);
    const steps = text(result, 'ol', '');
    for (const step of data.steps) {
      const node = nodes.get(step.id);
      if (!node) continue;
      const row = text(steps, 'li', `${targets.has(step.id) ? '直接相关' : '必修先修'} · `);
      readLink(row, node);
      row.append(` · 教材 ${node.sections.join('、')} `);
      const prerequisites = node.required.filter(id => pathIds.has(id)).map(id => nodes.get(id).title);
      if (prerequisites.length) row.append(` · 先学 ${prerequisites.join('、')} `);
      locateButton(row, node);
    }
    fitPath();
    status.textContent += ` · 已高亮 ${pathIds.size} 个知识点`;
  });
  canvas.width = width;
  canvas.height = height;
  fit();
  moveCamera(target, true);
  let viewSize = {width: viewport.clientWidth, height: viewport.clientHeight};
  new ResizeObserver(() => {
    const next = {width: viewport.clientWidth, height: viewport.clientHeight};
    moveCamera({...target, x: target.x + (next.width - viewSize.width) / 2,
                y: target.y + (next.height - viewSize.height) / 2}, true);
    viewSize = next;
  }).observe(viewport);
  drawEdges();
  locate(new URLSearchParams(location.search).get('node'));
})();
