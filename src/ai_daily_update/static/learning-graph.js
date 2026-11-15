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
    if (x > width - 250) link.classList.add('graph-label-left');
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
  let zoom = 1;
  let pathIds = new Set();

  function centerOn(x, y) {
    const rect = stage.getBoundingClientRect();
    const view = viewport.getBoundingClientRect();
    viewport.scrollBy(rect.left + x * zoom - view.left - viewport.clientWidth / 2,
                      rect.top + y * zoom - view.top - viewport.clientHeight / 2);
  }

  function setZoom(value, center = true) {
    const rect = stage.getBoundingClientRect();
    const view = viewport.getBoundingClientRect();
    const x = (view.left + viewport.clientWidth / 2 - rect.left) / zoom;
    const y = (view.top + viewport.clientHeight / 2 - rect.top) / zoom;
    zoom = Math.max(.15, Math.min(2, value));
    stage.style.zoom = zoom;
    stage.style.setProperty('--graph-label-size', `${Math.max(15, 9 / zoom)}px`);
    stage.classList.toggle('graph-compact', zoom < .4);
    if (center) centerOn(x, y);
    status.textContent = `缩放 ${Math.round(zoom * 100)}%`;
  }

  function fit() {
    setZoom(Math.min(viewport.clientWidth / width, viewport.clientHeight / height, 1), false);
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
                     viewport.clientHeight / (bottom - top + 120), 1.2), false);
    centerOn((left + right) / 2, (top + bottom) / 2);
    viewport.scrollIntoView({block: 'nearest', inline: 'nearest'});
  }

  function drawEdges() {
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, width, height);
    const active = pathIds.size > 0;
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
      [ctx.strokeStyle, ctx.lineWidth] = highlight ? ['#ffd580', 4] : styles[edge.kind];
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
    if (zoom < .75) setZoom(1, false);
    const {x, y} = positions.get(id);
    centerOn(x, y);
    viewport.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    link.focus({ preventScroll: true });
  }

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
  let drag = null;
  viewport.addEventListener('pointerdown', event => {
    if (event.pointerType !== 'mouse' || event.button !== 0 || event.target.closest('a')) return;
    drag = { x: event.clientX, y: event.clientY, left: viewport.scrollLeft, top: viewport.scrollTop };
    viewport.setPointerCapture(event.pointerId);
    viewport.classList.add('dragging');
  });
  viewport.addEventListener('pointermove', event => {
    if (drag) viewport.scrollTo(drag.left + drag.x - event.clientX, drag.top + drag.y - event.clientY);
  });
  viewport.addEventListener('lostpointercapture', () => { drag = null; viewport.classList.remove('dragging'); });

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
  if (zoom < .4 && viewport.clientWidth < 540) {
    setZoom(.4, false);
    centerOn(width / 2, height / 2);
  }
  drawEdges();
  locate(new URLSearchParams(location.search).get('node'));
})();
