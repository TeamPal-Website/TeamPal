const API_BASE_URL = (() => {
  if (typeof window === "undefined") return "http://localhost:8000";
  const override = window.__API_BASE_URL__;
  if (typeof override === "string" && override.trim()) return override.trim().replace(/\/+$/, "");

  const loc = window.location;
  if (!loc || !loc.origin) return "http://localhost:8000";

  if (loc.origin === "null" || loc.protocol === "file:") return "http://localhost:8000";

  const host = loc.hostname;
  const port = loc.port;
  if (host === "localhost" || host === "127.0.0.1") {
    if (port && port !== "8000") return "http://localhost:8000";
  }

  return loc.origin.replace(/\/+$/, "");
})();

/** Лимит как в backend: MAX_SALARY_AMOUNT_RUB в schemas/resumes.py и project_vacancies.py (50_000_000). */
const TP_MAX_SALARY_RUB = 50000000;

/** Как в ORM: String(255) — например resumes.desired_position, resume_experiences.company_name / position. */
const TP_ORM_VARCHAR255 = 255;

/**
 * В ORM поля Text без max_length; верхняя граница для проверки на фронте (защита от случайной вставки очень длинного текста).
 * Согласуйте при изменении лимитов на бэкенде.
 */
const TP_ORM_TEXT_SAFE_MAX = 100000;

/**
 * @param {string|null|undefined} s
 * @param {number} maxLen
 * @param {string} fieldLabel
 * @returns {{ ok: true, value: string } | { ok: false, message: string }}
 */
function tpCheckStringMaxLen(s, maxLen, fieldLabel) {
  const v = s == null ? "" : String(s);
  if (v.length > maxLen) {
    return {
      ok: false,
      message:
        fieldLabel +
        ": не более " +
        String(maxLen) +
        " символов (ограничение поля в базе данных).",
    };
  }
  return { ok: true, value: v };
}

/**
 * @param {number|null|undefined} n
 * @returns {{ ok: true, value: number|null } | { ok: false, message: string }}
 */
function tpValidateSalaryAmount(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return { ok: true, value: null };
  const v = Math.trunc(Number(n));
  if (v < 0) {
    return { ok: false, message: "Сумма заработной платы не может быть отрицательной" };
  }
  if (v > TP_MAX_SALARY_RUB) {
    return {
      ok: false,
      message:
        "Превышена допустимая сумма заработной платы (не более " +
        String(TP_MAX_SALARY_RUB) +
        " ₽).",
    };
  }
  return { ok: true, value: v };
}

/** Только цифры из строки (форматирование суммы в поле ввода). */
function tpSalaryDigitsOnly(raw) {
  return String(raw ?? "").replace(/\D/g, "");
}

/** Группировка цифр пробелами по разрядам (например 10 000 000). */
function tpFormatSalaryGroupedFromDigits(digits) {
  const d = tpSalaryDigitsOnly(digits);
  if (!d) return "";
  return d.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

/** Отформатировать число или строку для отображения в поле зарплаты. */
function tpFormatSalaryGroupedForDisplay(value) {
  return tpFormatSalaryGroupedFromDigits(tpSalaryDigitsOnly(String(value ?? "")));
}

/**
 * Поле ввода суммы: ввод только цифр, отображение с пробелами между тысячами.
 * При отправке использовать tpParseAndValidateSalaryRaw.
 */
function tpBindSalaryGroupedInput(el) {
  if (!el || el.nodeType !== 1) return;
  try {
    if (el.getAttribute("type") === "number") el.type = "text";
  } catch (_) {}
  el.setAttribute("inputmode", "numeric");
  el.setAttribute("autocomplete", "off");
  function refresh() {
    const d = tpSalaryDigitsOnly(el.value);
    const formatted = tpFormatSalaryGroupedFromDigits(d);
    if (el.value !== formatted) {
      const end = formatted.length;
      el.value = formatted;
      try {
        el.setSelectionRange(end, end);
      } catch (_) {}
    }
  }
  if (el.dataset.tpSalaryBound === "1") {
    refresh();
    return;
  }
  el.dataset.tpSalaryBound = "1";
  el.addEventListener("input", refresh);
  el.addEventListener("focus", refresh);
  refresh();
}

/**
 * Разбор суммы из поля ввода: пробелы/NBSP, подчёркивания; пусто → null.
 * @param {string|null|undefined} raw
 * @returns {{ ok: true, value: number|null } | { ok: false, message: string }}
 */
function tpParseAndValidateSalaryRaw(raw) {
  const t = String(raw ?? "").trim();
  if (!t) return { ok: true, value: null };
  let s = t.replace(/[\s\u00a0\u202f_]/g, "");
  if (!s) return { ok: true, value: null };
  if (/^\d{1,3}(\.\d{3})+$/.test(s)) {
    s = s.replace(/\./g, "");
  } else if (/^\d{1,3}(,\d{3})+$/.test(s)) {
    s = s.replace(/,/g, "");
  } else {
    s = s.replace(",", ".");
  }
  const n = Number(s);
  if (!Number.isFinite(n)) {
    return {
      ok: false,
      message: "Укажите корректную сумму заработной платы или оставьте поле пустым.",
    };
  }
  return tpValidateSalaryAmount(n);
}

/** Сообщение об ошибке из ответа FastAPI (422 и др.) */
function tpFormatApiDetail(detail) {
  if (detail == null || detail === "") return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item == null) return "";
        if (typeof item === "string") return item;
        if (typeof item === "object" && item.msg) return String(item.msg);
        try {
          return JSON.stringify(item);
        } catch {
          return String(item);
        }
      })
      .filter(Boolean)
      .join(" ");
  }
  if (typeof detail === "object" && detail.msg) return String(detail.msg);
  try {
    return JSON.stringify(detail);
  } catch {
    return String(detail);
  }
}

if (typeof window !== "undefined") {
  window.TP_MAX_SALARY_RUB = TP_MAX_SALARY_RUB;
  window.TP_ORM_VARCHAR255 = TP_ORM_VARCHAR255;
  window.TP_ORM_TEXT_SAFE_MAX = TP_ORM_TEXT_SAFE_MAX;
  window.tpCheckStringMaxLen = tpCheckStringMaxLen;
  window.tpValidateSalaryAmount = tpValidateSalaryAmount;
  window.tpParseAndValidateSalaryRaw = tpParseAndValidateSalaryRaw;
  window.tpFormatApiDetail = tpFormatApiDetail;
  window.tpSalaryDigitsOnly = tpSalaryDigitsOnly;
  window.tpFormatSalaryGroupedFromDigits = tpFormatSalaryGroupedFromDigits;
  window.tpFormatSalaryGroupedForDisplay = tpFormatSalaryGroupedForDisplay;
  window.tpBindSalaryGroupedInput = tpBindSalaryGroupedInput;
}
