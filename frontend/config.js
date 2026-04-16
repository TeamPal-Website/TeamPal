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
  window.tpValidateSalaryAmount = tpValidateSalaryAmount;
  window.tpParseAndValidateSalaryRaw = tpParseAndValidateSalaryRaw;
  window.tpFormatApiDetail = tpFormatApiDetail;
}
