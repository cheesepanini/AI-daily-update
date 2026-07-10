(function () {
  function setBusy(actions, busy) {
    if (!actions) {
      return;
    }
    actions.classList.toggle("is-updating", busy);
    actions.querySelectorAll("button").forEach((button) => {
      button.disabled = busy;
    });
  }

  function updateCardBlocks(payload) {
    document.querySelectorAll("[data-card-id]").forEach((block) => {
      if (block.dataset.cardId !== payload.card_id) {
        return;
      }
      const statusLabel = block.querySelector("[data-card-status-label]");
      if (statusLabel) {
        statusLabel.className = `status ${payload.status}`;
        statusLabel.textContent = payload.status_label;
      }
      const actions = block.querySelector("[data-card-status-actions]");
      if (actions && payload.actions_html) {
        actions.outerHTML = payload.actions_html;
      }
    });
  }

  function updateSourceSuggestionBlocks(payload) {
    document.querySelectorAll("[data-source-suggestion-id]").forEach((block) => {
      if (block.dataset.sourceSuggestionId !== payload.suggestion_id) {
        return;
      }
      const statusLabel = block.querySelector("[data-source-suggestion-status-label]");
      if (statusLabel) {
        statusLabel.className = `status ${payload.status_class}`;
        statusLabel.textContent = payload.status_label;
      }
      const actions = block.querySelector("[data-source-suggestion-actions]");
      if (actions && payload.actions_html) {
        actions.outerHTML = payload.actions_html;
      }
    });
  }

  function ajaxActionKind(form) {
    const action = form.getAttribute("action");
    if (action === "/actions/review") {
      return "card-review";
    }
    if (
      action === "/actions/source-suggestion-review" ||
      action === "/actions/source-suggestion-add"
    ) {
      return "source-suggestion";
    }
    return "";
  }

  document.addEventListener("submit", async (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) {
      return;
    }
    const actionKind = ajaxActionKind(form);
    if (!actionKind) {
      return;
    }
    if (!window.fetch || !window.FormData) {
      return;
    }

    event.preventDefault();
    const actions = form.closest("[data-card-status-actions], [data-source-suggestion-actions]");
    setBusy(actions, true);

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "X-Requested-With": "fetch",
        },
      });
      if (!response.ok) {
        throw new Error(`review failed: ${response.status}`);
      }
      const payload = await response.json();
      if (!payload.ok) {
        throw new Error(payload.error || "review failed");
      }
      if (actionKind === "card-review") {
        updateCardBlocks(payload);
      } else {
        updateSourceSuggestionBlocks(payload);
      }
    } catch (error) {
      setBusy(actions, false);
      HTMLFormElement.prototype.submit.call(form);
    }
  });
})();
