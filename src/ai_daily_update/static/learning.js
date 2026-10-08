(() => {
  const key = "ai-learning-v1";
  const initial = { goal_id: "", goal_text: "", background: "beginner", read: [], verified: [], history: [] };
  let state;
  try { state = { ...initial, ...JSON.parse(localStorage.getItem(key) || "{}") }; }
  catch { state = { ...initial }; }
  const save = () => { try { localStorage.setItem(key, JSON.stringify(state)); } catch {} };
  const $ = (id) => document.getElementById(id);
  const note = (parent, text) => { const p = document.createElement("p"); p.textContent = text; parent.appendChild(p); };
  const link = (parent, label, href) => {
    const a = document.createElement("a"); a.textContent = label; a.href = href; parent.appendChild(a);
  };
  const post = async (url, body) => {
    const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "服务暂时不可用");
    return data;
  };

  const conceptPage = document.querySelector("[data-learning-id]");
  if (conceptPage) {
    const id = conceptPage.dataset.learningId;
    const render = () => { $("learning-progress-state").textContent = state.verified.includes(id) ? "已答对检查题" : state.read.includes(id) ? "已读，尚未完成检查题" : "尚未记录进度"; };
    $("learning-mark-read").addEventListener("click", () => { if (!state.read.includes(id)) state.read.push(id); save(); render(); });
    $("learning-mark-verified").addEventListener("click", () => { if (!state.verified.includes(id)) state.verified.push(id); save(); render(); });
    render();
  }

  if ($('learning-plan-form')) {
    $("learning-goal").value = state.goal_id;
    $("learning-custom-goal").value = state.goal_text;
    $("learning-background").value = state.background;
    $("learning-plan-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const box = $("learning-plan-result"); box.replaceChildren(); note(box, "正在整理学习方向…");
      state.goal_id = $("learning-goal").value; state.goal_text = $("learning-custom-goal").value.trim(); state.background = $("learning-background").value; save();
      try {
        const data = await post("/api/v1/learning/plan", { goal_id: state.goal_id, goal_text: state.goal_text, background: state.background, known_ids: [] });
        box.replaceChildren();
        const h = document.createElement("h3"); h.textContent = data.title; box.appendChild(h);
        if (data.message) note(box, data.message);
        if (data.starting_note) note(box, data.starting_note);
        if (data.steps.length) note(box, "建议按以下顺序了解这些主题；遇到具体疑问可进入知识点页面提问。");
        const list = document.createElement("ol");
        for (const step of data.steps) {
          const li = document.createElement("li");
          link(li, step.title, `/learn/concepts/${encodeURIComponent(step.id)}`);
          li.append(` — ${step.reason}`);
          list.appendChild(li);
        }
        box.appendChild(list);
      } catch (error) { box.replaceChildren(); note(box, `生成失败：${error.message}`); }
    });
  }

  if ($('learning-chat-form')) {
    let timer;
    $("concept-search").addEventListener("input", () => {
      clearTimeout(timer);
      timer = setTimeout(async () => {
        const box = $("concept-results"); box.replaceChildren();
        const q = $("concept-search").value.trim(); if (!q) return;
        try {
          const response = await fetch(`/api/v1/learning/concepts?q=${encodeURIComponent(q)}`);
          const data = await response.json();
          if (!data.items.length) note(box, "未找到已审核的相关概念。");
          for (const item of data.items) {
            const p = document.createElement("p");
            link(p, `${item.title} · 教材 ${item.source_section}`, `/learn/concepts/${encodeURIComponent(item.id)}`);
            box.appendChild(p);
          }
        } catch { note(box, "搜索暂时不可用。"); }
      }, 250);
    });
    const params = new URLSearchParams(location.search);
    if (params.get("card_id")) $("learning-news-context").textContent = "当前对话会结合刚才打开的已审核消息卡片。";
    if (params.get("concept_id")) $("learning-message").value = `请解释「${params.get("concept_id").replace(/^concept:/, "")}」，并举一个例子。`;
    const renderHistory = () => {
      const log = $("learning-chat-log"); log.replaceChildren();
      for (const entry of state.history) {
        const block = document.createElement("div"); block.className = "learning-message";
        note(block, (entry.role === "user" ? "你：" : "学习助手：") + entry.content);
        for (const source of entry.sources || []) {
          link(block, `[${source.ref}] ${source.type === "news" ? "消息" : "教材"}：${source.title}${source.date ? `（${source.date}）` : ""}`, source.url);
        }
        log.appendChild(block);
      }
    };
    renderHistory();
    $("learning-chat-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const input = $("learning-message"); const message = input.value.trim(); if (!message) return;
      const prior = state.history.slice(-12).map(({ role, content }) => ({ role, content: content.slice(0, 500) }));
      state.history.push({ role: "user", content: message }); state.history = state.history.slice(-20); save(); renderHistory();
      input.value = "";
      try {
        const cardId = params.get("card_id") || "";
        const data = await post("/api/v1/learning/chat", { message, depth: $("learning-depth").value, card_id: cardId, history: prior });
        state.history.push({ role: "assistant", content: `${data.answer}\n\n检查理解：${data.followup}`, sources: data.sources });
        state.history = state.history.slice(-20); save(); renderHistory();
      } catch (error) {
        state.history.push({ role: "assistant", content: `暂时无法回答：${error.message}` }); save(); renderHistory();
      }
    });
    $("learning-clear").addEventListener("click", () => {
      state.history = []; save(); renderHistory();
    });
  }
})();
