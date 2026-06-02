(function (global) {
  "use strict";

  const CHEVRON_SVG =
    '<svg class="tp-rec-picker__chevron" viewBox="0 0 14 8" fill="none" aria-hidden="true">' +
    '<path d="M1.5 1.5L7 6l5.5-4.5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>' +
    "</svg>";

  function esc(v) {
    return String(v == null ? "" : v).replace(/[&<>"]/g, (m) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
    })[m]);
  }

  function getUi(select) {
    return select && select._tpRecPicker ? select._tpRecPicker : null;
  }

  function closeMenu(ui) {
    if (!ui || !ui.menu) return;
    ui.menu.hidden = true;
    ui.wrap.classList.remove("is-open");
    ui.trigger.setAttribute("aria-expanded", "false");
  }

  function openMenu(ui) {
    if (!ui || !ui.menu || ui.wrap.hidden) return;
    ui.menu.hidden = false;
    ui.wrap.classList.add("is-open");
    ui.trigger.setAttribute("aria-expanded", "true");
    const selected = ui.menu.querySelector(".tp-rec-picker__option.is-selected");
    if (selected && typeof selected.scrollIntoView === "function") {
      selected.scrollIntoView({ block: "nearest" });
    }
  }

  function toggleMenu(ui) {
    if (!ui) return;
    if (ui.menu.hidden) openMenu(ui);
    else closeMenu(ui);
  }

  function bind(select) {
    if (!select || select.dataset.tpRecPickerBound === "1") return;
    select.dataset.tpRecPickerBound = "1";
    select.classList.add("tp-rec-picker__native");

    const wrap = document.createElement("div");
    wrap.className = "tp-rec-picker";

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "tp-rec-picker__trigger";
    trigger.setAttribute("aria-haspopup", "listbox");

    const menu = document.createElement("div");
    menu.className = "tp-rec-picker__menu";
    menu.setAttribute("role", "listbox");
    menu.hidden = true;

    wrap.appendChild(trigger);
    wrap.appendChild(menu);
    select.parentNode.insertBefore(wrap, select);

    const ui = { wrap, trigger, menu };
    select._tpRecPicker = ui;

    trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleMenu(ui);
    });

    menu.addEventListener("click", (e) => e.stopPropagation());

    if (!global._tpRecPickerDocClose) {
      global._tpRecPickerDocClose = true;
      document.addEventListener("click", () => {
        document.querySelectorAll(".tp-rec-picker.is-open").forEach((w) => {
          const sel = w.parentNode && w.parentNode.querySelector(".tp-rec-picker__native");
          const u = sel && getUi(sel);
          if (u) closeMenu(u);
        });
      });
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
          document.querySelectorAll(".tp-rec-picker.is-open").forEach((w) => {
            const sel = w.parentNode && w.parentNode.querySelector(".tp-rec-picker__native");
            const u = sel && getUi(sel);
            if (u) closeMenu(u);
          });
        }
      });
    }

    sync(select);
  }

  function sync(select) {
    const ui = getUi(select);
    if (!ui) return;

    const options = Array.from(select.options || []);
    const show = !select.hidden && options.length > 0;
    ui.wrap.hidden = !show;
    if (!show) {
      closeMenu(ui);
      return;
    }

    const current = select.value;
    const selectedOpt = options.find((o) => o.value === current) || options[0];

    ui.menu.innerHTML = options
      .map((opt) => {
        const isSel = opt.value === (selectedOpt && selectedOpt.value);
        return (
          '<button type="button" class="tp-rec-picker__option' +
          (isSel ? " is-selected" : "") +
          '" role="option" aria-selected="' +
          (isSel ? "true" : "false") +
          '" data-value="' +
          esc(opt.value) +
          '">' +
          '<span class="tp-rec-picker__option-text">' +
          esc(opt.textContent) +
          "</span>" +
          (isSel ? '<span class="tp-rec-picker__check" aria-hidden="true">✓</span>' : "") +
          "</button>"
        );
      })
      .join("");

    ui.trigger.innerHTML =
      '<span class="tp-rec-picker__label">' +
      esc(selectedOpt ? selectedOpt.textContent : "Выберите") +
      "</span>" +
      CHEVRON_SVG;
    ui.trigger.setAttribute(
      "aria-label",
      select.getAttribute("aria-label") || "Выбор из списка"
    );

    ui.menu.querySelectorAll(".tp-rec-picker__option").forEach((btn) => {
      btn.addEventListener("click", () => {
        const val = btn.getAttribute("data-value");
        if (val == null || val === select.value) {
          closeMenu(ui);
          return;
        }
        select.value = val;
        select.dispatchEvent(new Event("change", { bubbles: true }));
        sync(select);
        closeMenu(ui);
      });
    });
  }

  global.tpBindRecEntityPicker = bind;
  global.tpSyncRecEntityPicker = sync;
})(typeof window !== "undefined" ? window : globalThis);
