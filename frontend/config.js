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

/** Явно в window — иначе в Safari/отдельных окружениях другие скрипты видят `typeof API_BASE_URL === "undefined"`. */
if (typeof window !== "undefined") {
  window.API_BASE_URL = API_BASE_URL;
}

function tpAvatarSrcFromApiField(apiAvatarField) {
  if (apiAvatarField == null || String(apiAvatarField).trim() === "") {
    return "./assets/avatar-default.png";
  }
  const v = String(apiAvatarField).trim();
  if (v.startsWith("http://") || v.startsWith("https://")) {
    return v;
  }
  if (v.startsWith("/")) {
    return API_BASE_URL + v;
  }
  return v;
}

function tpMyProfileAvatarSrc(apiAvatarValue) {
  return tpAvatarSrcFromApiField(apiAvatarValue);
}

/** Аватар соискателя в списках откликов работодателя: URL из API или прямой /profiles/:userId/avatar/file. */
function tpApplicationApplicantAvatarSrc(applicationLike) {
  if (!applicationLike || typeof tpAvatarSrcFromApiField !== "function") return "./assets/avatar-default.png";
  const raw = applicationLike.applicant_avatar_url;
  if (raw != null && String(raw).trim() !== "") {
    return tpAvatarSrcFromApiField(raw);
  }
  const uid = applicationLike.applicant_user_id;
  if (uid != null && String(uid).trim() !== "") {
    return API_BASE_URL + "/profiles/" + encodeURIComponent(String(uid)) + "/avatar/file";
  }
  return "./assets/avatar-default.png";
}

/** Подпись резюме в выпадающем списке: желаемая должность из карточки; при пустой — номер резюме; дата для различения копий. */
function tpResumeSelectOptionLabel(r) {
  if (!r || r.id == null) return "Резюме";
  const raw = r.desired_position != null ? String(r.desired_position).trim() : "";
  const base = raw || "Резюме №" + String(r.id);
  let suffix = "";
  if (r.created_at) {
    try {
      const d = new Date(r.created_at);
      if (!Number.isNaN(d.getTime())) {
        suffix = " · " + d.toLocaleDateString("ru-RU");
      }
    } catch (_) {}
  }
  return base + suffix;
}

const TP_MAX_SALARY_RUB = 50000000;

const TP_ORM_VARCHAR255 = 255;

const TP_ORM_TEXT_SAFE_MAX = 100000;

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

function tpSalaryDigitsOnly(raw) {
  return String(raw ?? "").replace(/\D/g, "");
}

function tpFormatSalaryGroupedFromDigits(digits) {
  const d = tpSalaryDigitsOnly(digits);
  if (!d) return "";
  return d.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
}

function tpFormatSalaryGroupedForDisplay(value) {
  return tpFormatSalaryGroupedFromDigits(tpSalaryDigitsOnly(String(value ?? "")));
}

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

function tpUserFacingValidationMsg(msg) {
  if (typeof msg !== "string") return "";
  let s = msg;
  const prefixes = ["Value error, ", "Assertion failed, "];
  for (let i = 0; i < prefixes.length; i++) {
    const p = prefixes[i];
    if (s.startsWith(p)) {
      s = s.slice(p.length).trimStart();
      break;
    }
  }
  return s;
}

function tpFormatApiDetail(detail) {
  if (detail == null || detail === "") return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const sorted = [...detail].sort((a, b) => {
      const locA = a && typeof a === "object" && Array.isArray(a.loc) ? a.loc.join(".") : "";
      const locB = b && typeof b === "object" && Array.isArray(b.loc) ? b.loc.join(".") : "";
      const rank = (s) => (s.endsWith("first_name") ? 0 : s.endsWith("last_name") ? 1 : 50);
      return rank(locA) - rank(locB);
    });
    const parts = sorted
      .map((item) => {
        if (item == null) return "";
        if (typeof item === "string") return tpUserFacingValidationMsg(item);
        if (typeof item === "object" && item.msg) return tpUserFacingValidationMsg(String(item.msg));
        if (typeof item === "object" && item.message) return tpUserFacingValidationMsg(String(item.message));
        try {
          return JSON.stringify(item);
        } catch {
          return String(item);
        }
      })
      .filter(Boolean);
    const uniq = [...new Set(parts)];
    const onlyNameHints = uniq.every((p) => p === "Укажите имя" || p === "Укажите фамилию");
    if (onlyNameHints && uniq.includes("Укажите имя")) {
      return "Укажите имя";
    }
    return uniq.join("; ");
  }
  if (typeof detail === "object" && detail.msg) return tpUserFacingValidationMsg(String(detail.msg));
  if (typeof detail === "object" && detail.message) return tpUserFacingValidationMsg(String(detail.message));
  try {
    return JSON.stringify(detail);
  } catch {
    return String(detail);
  }
}

function tpUserFacingErrorLine(message) {
  let s = String(message == null ? "" : message).replace(/^\uFEFF/, "").trim();
  if (!s) return "";
  const stripped = s.match(/^\s*ошибка\s*:\s*(.*)$/i);
  if (stripped) {
    s = (stripped[1] || "").trim();
    if (!s) return "";
  }
  const first = s.charAt(0).toUpperCase();
  return first + s.slice(1);
}

if (typeof window !== "undefined") {
  window.tpMyProfileAvatarSrc = tpMyProfileAvatarSrc;
  window.TP_MAX_SALARY_RUB = TP_MAX_SALARY_RUB;
  window.TP_ORM_VARCHAR255 = TP_ORM_VARCHAR255;
  window.TP_ORM_TEXT_SAFE_MAX = TP_ORM_TEXT_SAFE_MAX;
  window.tpCheckStringMaxLen = tpCheckStringMaxLen;
  window.tpValidateSalaryAmount = tpValidateSalaryAmount;
  window.tpParseAndValidateSalaryRaw = tpParseAndValidateSalaryRaw;
  window.tpFormatApiDetail = tpFormatApiDetail;
  window.tpUserFacingErrorLine = tpUserFacingErrorLine;
  window.tpSalaryDigitsOnly = tpSalaryDigitsOnly;
  window.tpFormatSalaryGroupedFromDigits = tpFormatSalaryGroupedFromDigits;
  window.tpFormatSalaryGroupedForDisplay = tpFormatSalaryGroupedForDisplay;
  window.tpBindSalaryGroupedInput = tpBindSalaryGroupedInput;
}
