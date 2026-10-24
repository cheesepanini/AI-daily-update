(() => {
  const key = "ai-daily-favorites-v1";
  const list = document.getElementById("favorites-list");

  function read() {
    try {
      const value = JSON.parse(localStorage.getItem(key) || "[]");
      return Array.isArray(value) ? [...new Set(value.filter(id => typeof id === "string" && id))] : [];
    } catch {
      return null;
    }
  }

  let favorites = read();

  function updateButtons() {
    document.querySelectorAll("[data-favorite-id]").forEach(button => {
      const selected = favorites?.includes(button.dataset.favoriteId) || false;
      button.disabled = favorites === null;
      button.setAttribute("aria-pressed", String(selected));
      button.textContent = favorites === null ? "收藏不可用" : selected ? "取消收藏" : "收藏";
    });
  }

  async function renderList() {
    if (!list) return;
    if (favorites === null) {
      list.textContent = "此浏览器无法读取本地收藏。";
      return;
    }
    if (!favorites.length) {
      list.innerHTML = '<p class="muted">还没有收藏的卡片。可以从精选或全部动态开始浏览。</p>';
      return;
    }
    const ids = [...favorites];
    list.textContent = "正在核对收藏…";
    const results = await Promise.all(ids.map(async id => {
      try {
        const response = await fetch(`/api/v1/cards/${encodeURIComponent(id)}`);
        return response.ok ? { id, card: await response.json() } : { id, missing: response.status === 404 };
      } catch {
        return { id, missing: false };
      }
    }));
    if (ids.join("\0") !== favorites.join("\0")) return;
    list.replaceChildren();
    for (const { id, card, missing } of results) {
      const article = document.createElement("article");
      article.className = "favorite-item";
      const heading = document.createElement("h2");
      if (card) {
        const link = document.createElement("a");
        link.href = `/public/cards/${encodeURIComponent(id)}`;
        link.textContent = card.title;
        heading.append(link);
        const detail = document.createElement("p");
        detail.className = "muted";
        const summary = card.conclusion?.length > 180 ? `${card.conclusion.slice(0, 180)}…` : card.conclusion;
        detail.textContent = [card.event_date, card.source_label, summary].filter(Boolean).join(" · ");
        article.append(heading, detail);
      } else {
        heading.textContent = missing ? "这张卡片已无法公开查看" : "暂时无法加载这张卡片，请稍后刷新";
        article.append(heading);
      }
      const button = document.createElement("button");
      button.type = "button";
      button.className = "favorite-button";
      button.dataset.favoriteId = id;
      button.setAttribute("aria-label", card ? `取消收藏：${card.title}` : "移除这条收藏");
      article.append(button);
      list.append(article);
    }
    updateButtons();
  }

  document.addEventListener("click", event => {
    const button = event.target.closest("[data-favorite-id]");
    if (!button || favorites === null) return;
    const id = button.dataset.favoriteId;
    const next = favorites.includes(id) ? favorites.filter(value => value !== id) : [id, ...favorites];
    try {
      localStorage.setItem(key, JSON.stringify(next));
    } catch {
      button.textContent = "保存失败";
      return;
    }
    favorites = next;
    updateButtons();
    renderList();
  });

  window.addEventListener("storage", event => {
    if (event.key !== key) return;
    favorites = read();
    updateButtons();
    renderList();
  });

  updateButtons();
  renderList();
})();
