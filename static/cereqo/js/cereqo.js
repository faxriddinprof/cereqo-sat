(() => {
  const toggles = document.querySelectorAll("[data-theme-toggle]");
  const root = document.documentElement;

  const updateThemeControls = (theme) => {
    toggles.forEach((button) => {
      const isDark = theme === "dark";
      const icon = button.querySelector("[data-theme-icon]");
      if (icon) icon.className = isDark ? "bi bi-sun" : "bi bi-moon-stars";
      const label = isDark ? button.dataset.lightLabel : button.dataset.darkLabel;
      button.setAttribute("aria-label", label);
      button.setAttribute("title", label);
    });
  };

  const applyTheme = (theme) => {
    root.dataset.theme = theme;
    root.dataset.bsTheme = theme;
    localStorage.setItem("cereqo.theme", theme);
    updateThemeControls(theme);
  };

  updateThemeControls(root.dataset.theme || "light");
  toggles.forEach((button) => button.addEventListener("click", () => {
    applyTheme(root.dataset.theme === "dark" ? "light" : "dark");
  }));
})();

(() => {
  const form = document.querySelector("[data-homework-form]");
  if (!form || !form.dataset.autosaveUrl) return;

  const status = form.closest("main").querySelector("[data-save-status]");
  const count = form.closest("main").querySelector("[data-answered-count]");
  const bar = form.closest("main").querySelector("[data-progress-bar]");
  const csrf = form.querySelector("[name=csrfmiddlewaretoken]")?.value;

  form.querySelectorAll('input[type="radio"]').forEach((input) => {
    input.addEventListener("change", async () => {
      const group = input.closest(".answer-options");
      group?.querySelectorAll(".answer-option").forEach((option) => option.classList.remove("selected"));
      input.closest(".answer-option")?.classList.add("selected");
      if (status) status.textContent = form.dataset.savingLabel || "Saving…";

      try {
        const response = await fetch(form.dataset.autosaveUrl, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
          body: JSON.stringify({ question_id: input.dataset.questionId, selected_option: input.value }),
        });
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.error || "Could not save");
        if (status) status.textContent = `${form.dataset.savedLabel || "Saved at"} ${data.saved_at}`;
        if (count) count.textContent = data.answered;
        if (bar) bar.style.width = `${Math.round((data.answered / data.total) * 100)}%`;
      } catch (error) {
        if (status) status.textContent = form.dataset.failedLabel || "Save failed — use Save & exit";
        status?.classList.add("text-danger");
      }
    });
  });
})();
