(() => {
  const key = "ai-learning-v1";
  const initial = { goal_text: "", read: [], verified: [], history: [] };
  let state;
  try { state = { ...initial, ...JSON.parse(localStorage.getItem(key) || "{}") }; }
  catch { state = { ...initial }; }
  const save = () => { try { localStorage.setItem(key, JSON.stringify(state)); } catch {} };
  const $ = (id) => document.getElementById(id);
  const note = (parent, text) => { const p = document.createElement("p"); p.textContent = text; parent.appendChild(p); };
  const link = (parent, label, href) => {
    if (typeof href !== "string" || (!(href.startsWith("/") && !href.startsWith("//")) && !/^https?:\/\//i.test(href))) return;
    const a = document.createElement("a"); a.textContent = label; a.href = href; parent.appendChild(a);
  };
  const post = async (url, body, signal) => {
    const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal });
    const data = await response.json();
    if (!response.ok) throw new Error({ model_unverified: "回答缺少可靠的资料引用，请重试。", model_failed: "回答生成失败，请稍后重试。" }[data.error] || data.error || "服务暂时不可用");
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

  const planForm = $("learning-plan-form");
  if (planForm) {
    const dialog = $("graph-plan");
    const input = $("learning-custom-goal");
    const status = $("learning-plan-status");
    const submit = planForm.querySelector("button[type=submit]");
    let pending;
    input.value = state.goal_text;
    dialog.addEventListener("close", () => {
      pending?.abort();
      submit.disabled = false;
      status.textContent = "";
    });
    planForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (submit.disabled) return;
      const goal = input.value.trim();
      if (!goal) {
        status.textContent = "请输入学习目标。";
        return;
      }
      const request = new AbortController();
      pending = request;
      submit.disabled = true;
      status.textContent = "正在规划学习路径…";
      state.goal_text = goal;
      save();
      try {
        const data = await post("/api/v1/learning/plan", { goal_text: goal }, request.signal);
        if (request.signal.aborted || !dialog.open) return;
        if (!data.steps.length) {
          status.textContent = data.message || "请换一个更具体的学习目标。";
          return;
        }
        dialog.close();
        $("learning-plan-result").dispatchEvent(new CustomEvent("textbook-plan", { detail: data }));
      } catch (error) {
        if (!request.signal.aborted) status.textContent = "暂时无法生成学习路径，请稍后重试。";
      } finally {
        if (pending === request) {
          pending = undefined;
          submit.disabled = false;
        }
      }
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
    if (params.get("concept_id")) $("learning-message").value = `请解释「${params.get("concept_id").replace(/^(?:concept:|microtopic:[\d.]+-\d+-)/, "")}」，并举一个例子。`;
    const renderHistory = () => {
      const log = $("learning-chat-log"); log.replaceChildren();
      if (!state.history.length) {
        const empty = document.createElement("p"); empty.className = "learning-empty";
        empty.textContent = "从一个具体问题开始，例如“智能体如何调用工具？”"; log.appendChild(empty);
      }
      const answers = [];
      for (const entry of state.history) {
        const block = document.createElement("article"); block.className = `learning-message ${entry.role === "user" ? "user" : "assistant"}`;
        const label = document.createElement("span"); label.className = "learning-role";
        label.textContent = entry.role === "user" ? "你" : "学习助手"; block.appendChild(label);
        const content = document.createElement("div"); content.className = "learning-markdown";
        content.textContent = entry.content; block.appendChild(content);
        if (entry.role === "assistant") answers.push([content, entry.content]);
        if (entry.followup) {
          const followup = document.createElement("p"); followup.className = "learning-followup";
          followup.textContent = `检查理解：${entry.followup}`; block.appendChild(followup);
        }
        const sources = document.createElement("div"); sources.className = "learning-sources";
        for (const source of entry.sources || []) {
          link(sources, `[${source.ref}] ${source.type === "news" ? "消息" : "教材"}：${source.title}${source.date ? `（${source.date}）` : ""}`, source.url);
        }
        if (sources.childElementCount) block.appendChild(sources);
        log.appendChild(block);
      }
      if (answers.length) post("/api/v1/learning/render", { messages: answers.map(([, content]) => content.slice(0, 6000)) })
        .then(({ html }) => {
          answers.forEach(([node], index) => { if (node.isConnected && typeof html[index] === "string") node.innerHTML = html[index]; });
          log.scrollTop = log.scrollHeight;
        })
        .catch(() => {});
      log.scrollTop = log.scrollHeight;
    };
    renderHistory();
    $("learning-chat-form").addEventListener("submit", async (event) => {
      event.preventDefault();
      const input = $("learning-message"); const message = input.value.trim(); if (!message) return;
      const send = $("learning-send"); if (send.disabled) return; send.disabled = true;
      const prior = state.history.slice(-12).map(({ role, content }) => ({ role, content: content.slice(0, 500) }));
      state.history.push({ role: "user", content: message }); state.history = state.history.slice(-20); save(); renderHistory();
      const pending = document.createElement("p"); pending.className = "learning-pending";
      pending.textContent = "正在查找资料并组织回答…"; $("learning-chat-log").appendChild(pending);
      input.value = "";
      try {
        const cardId = params.get("card_id") || "";
        const data = await post("/api/v1/learning/chat", { message, depth: $("learning-depth").value, card_id: cardId, history: prior });
        state.history.push({ role: "assistant", content: data.answer, followup: data.followup, sources: data.sources });
        state.history = state.history.slice(-20); save(); renderHistory();
      } catch (error) {
        state.history.push({ role: "assistant", content: `暂时无法回答：${error.message}` }); save(); renderHistory();
      } finally { send.disabled = false; }
    });
    $("learning-clear").addEventListener("click", () => {
      state.history = []; save(); renderHistory();
    });
  }
})();
