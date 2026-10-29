(() => {
  const prefsKey = "ai-daily-follows-v1";
  const readKey = "ai-daily-follow-read-v1";
  const empty = () => ({ topics: [], keywords: [], sources: [] });
  const tags = document.getElementById("follow-tags");
  const list = document.getElementById("follow-list");
  const more = document.getElementById("follow-more");
  const count = document.getElementById("follow-count");
  let prefs, read, page = 1, shown = 0, requestVersion = 0;
  try {
    const saved = JSON.parse(localStorage.getItem(prefsKey) || "{}");
    prefs = Object.fromEntries(Object.keys(empty()).map(key => [key, Array.isArray(saved[key]) ? saved[key].filter(value => typeof value === "string" && value.length <= 80).slice(0, 20) : []]));
    read = JSON.parse(localStorage.getItem(readKey) || "{}");
    if (!read || typeof read !== "object" || Array.isArray(read)) read = {};
  } catch { prefs = null; read = {}; }
  const save = () => { localStorage.setItem(prefsKey, JSON.stringify(prefs)); };
  const label = (key, value) => key === "topics" ? document.querySelector(`[data-follow-form="topics"] option[value="${CSS.escape(value)}"]`)?.textContent || value : value;
  function renderTags() {
    tags.replaceChildren();
    if (!prefs) { tags.textContent = "此浏览器无法读取本地关注。"; return; }
    for (const key of Object.keys(prefs)) for (const value of prefs[key]) {
      const button = document.createElement("button");
      button.type = "button"; button.className = "concept-chip";
      button.textContent = `${{ topics: "主题", keywords: "关键词", sources: "来源" }[key]}：${label(key, value)} ×`;
      button.addEventListener("click", () => { prefs[key] = prefs[key].filter(item => item !== value); save(); renderTags(); load(true); });
      tags.append(button);
    }
    if (!tags.childElementCount) tags.textContent = "尚未设置关注条件。";
  }
  async function load(reset = false) {
    const version = ++requestVersion;
    if (!prefs) { list.textContent = "此浏览器无法读取本地关注。"; return; }
    if (reset) { page = 1; shown = 0; list.replaceChildren(); more.hidden = true; }
    if (!Object.values(prefs).some(values => values.length)) { list.innerHTML = '<p class="muted">添加关注条件后，这里会显示匹配内容。</p>'; count.textContent = ""; return; }
    const params = new URLSearchParams({ page: String(page) });
    for (const value of prefs.topics) params.append("topic", value);
    for (const value of prefs.keywords) params.append("keyword", value);
    for (const value of prefs.sources) params.append("source", value);
    more.disabled = true;
    try {
      const response = await fetch(`/public/follow-items?${params}`);
      if (!response.ok) throw Error("load failed");
      const data = await response.json();
      if (version !== requestVersion) return;
      for (const card of data.items) {
        const article = document.createElement("article"); article.className = "favorite-item";
        const heading = document.createElement("h3"); const link = document.createElement("a");
        link.href = `/public/cards/${encodeURIComponent(card.id)}`; link.textContent = card.title;
        link.addEventListener("click", () => mark(card, button)); heading.append(link);
        const detail = document.createElement("p"); detail.className = "muted";
        detail.textContent = [card.event_date, card.source_label, card.conclusion?.slice(0, 180)].filter(Boolean).join(" · ");
        const button = document.createElement("button"); button.type = "button";
        button.addEventListener("click", () => mark(card, button, true));
        const refresh = () => { const unread = read[card.id] !== card.version; article.classList.toggle("unread", unread); button.textContent = unread ? "标记已读" : "标记未读"; button.setAttribute("aria-pressed", String(!unread)); };
        function mark(card, target, toggle = false) {
          if (toggle && read[card.id] === card.version) delete read[card.id]; else read[card.id] = card.version;
          try { localStorage.setItem(readKey, JSON.stringify(Object.fromEntries(Object.entries(read).slice(-500)))); } catch { target.textContent = "保存失败"; return; }
          refresh();
        }
        article.append(heading, detail, button); list.append(article); refresh();
      }
      shown += data.items.length; count.textContent = `已显示 ${shown} 条`;
      more.hidden = !data.has_next; page += 1;
      if (!shown) list.innerHTML = '<p class="muted">当前没有匹配的已审核卡片。</p>';
    } catch { if (!shown) list.textContent = "加载失败，请刷新后重试。"; }
    more.disabled = false;
  }
  document.querySelectorAll("[data-follow-form]").forEach(form => form.addEventListener("submit", event => {
    event.preventDefault(); if (!prefs) return;
    const key = form.dataset.followForm, input = form.elements.value, value = input.value.trim();
    if (!value || prefs[key].includes(value) || prefs[key].length >= 20) return;
    prefs[key].push(value); try { save(); } catch { list.textContent = "保存失败，本地存储不可用。"; return; }
    if (key !== "topics") input.value = "";
    renderTags(); load(true);
  }));
  more.addEventListener("click", () => load());
  window.addEventListener("storage", event => { if (event.key === prefsKey || event.key === readKey) location.reload(); });
  renderTags(); load(true);
})();
