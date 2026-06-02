(function (global) {
  "use strict";

  const API = typeof global.API_BASE_URL === "string" ? global.API_BASE_URL : "";

  const INTENT_LABELS = { commercial: "Коммерческий", noncommercial: "Учебный" };
  const WORK_LABELS = { remote: "Удалённо", office: "Офис", hybrid: "Гибрид" };
  const EXP_LABELS = { none: "Без опыта", "<1": "До 1 года", "1-3": "1–3 года", "3-6": "3–6 лет", "6+": "6+ лет" };

  function esc(v) {
    return String(v == null ? "" : v).replace(/[&<>"]/g, (m) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
    }[m]));
  }

  function formatMatchScore(score, peerScores) {
    const n = Number(score);
    if (!Number.isFinite(n)) return "—";
    const absolute = Math.round(Math.max(0, Math.min(1, n)) * 100);
    const peers = Array.isArray(peerScores)
      ? peerScores.map(Number).filter(Number.isFinite)
      : [];
    if (peers.length < 2) return absolute + "%";
    const min = Math.min(...peers);
    const max = Math.max(...peers);
    const span = max - min;
    if (span < 0.06) return absolute + "%";
    const rankRatio = (n - min) / span;
    const rankPct = Math.round(28 + rankRatio * 62);
    const blended = Math.round(0.6 * absolute + 0.4 * rankPct);
    return Math.max(15, Math.min(97, blended)) + "%";
  }

  const MATCH_SCORE_TITLE =
    "Совпадение с учётом семантики текста, роли и пересечения навыков";

  function vacancySalaryRub(amount) {
    if (amount == null || amount === "") return "—";
    const n = Number(amount);
    if (!Number.isFinite(n)) return "—";
    return n.toLocaleString("ru-RU") + " ₽";
  }

  function vacancySalaryType(st) {
    if (st === "per_project") return "За проект";
    if (st === "monthly") return "В месяц";
    return "—";
  }

  async function fetchJson(path) {
    const r = await fetch(API + path, { credentials: "include" });
    if (r.status === 401) {
      const err = new Error("unauthorized");
      err.code = 401;
      throw err;
    }
    if (!r.ok) {
      const body = await r.json().catch(() => ({}));
      const err = new Error(global.tpFormatApiDetail ? global.tpFormatApiDetail(body.detail) : "request failed");
      err.status = r.status;
      throw err;
    }
    return r.json();
  }

  async function fetchRecommendedVacancies(resumeId, opts) {
    const o = opts || {};
    const q = new URLSearchParams();
    q.set("limit", String(o.limit != null ? o.limit : 10));
    if (o.role_match_only) q.set("role_match_only", "true");
    if (o.city_id) q.set("city_id", String(o.city_id));
    if (o.work_format) q.set("work_format", String(o.work_format));
    return fetchJson("/resumes/" + encodeURIComponent(String(resumeId)) + "/recommended-vacancies?" + q.toString());
  }

  async function fetchRecommendedResumes(vacancyId, opts) {
    const o = opts || {};
    const q = new URLSearchParams();
    q.set("limit", String(o.limit != null ? o.limit : 10));
    if (o.role_match_only) q.set("role_match_only", "true");
    if (o.city_id) q.set("city_id", String(o.city_id));
    if (o.work_format) q.set("work_format", String(o.work_format));
    return fetchJson("/vacancies/" + encodeURIComponent(String(vacancyId)) + "/recommended-resumes?" + q.toString());
  }

  async function applyToVacancy(resumeId, vacancyId) {
    const r = await fetch(API + "/applications", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_id: Number(resumeId), vacancy_id: Number(vacancyId) }),
    });
    if (!r.ok) {
      const body = await r.json().catch(() => ({}));
      throw new Error(global.tpFormatApiDetail ? global.tpFormatApiDetail(body.detail) : "Не удалось отправить отклик");
    }
    return r.json();
  }

  async function inviteResumeToVacancy(vacancyId, resumeId) {
    const r = await fetch(API + "/vacancies/" + encodeURIComponent(String(vacancyId)) + "/invite_resume", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resume_id: Number(resumeId) }),
    });
    if (!r.ok) {
      const body = await r.json().catch(() => ({}));
      throw new Error(global.tpFormatApiDetail ? global.tpFormatApiDetail(body.detail) : "Не удалось отправить приглашение");
    }
    return r.json();
  }

  function renderVacancyCards(list, container, options) {
    const el = typeof container === "string" ? document.getElementById(container) : container;
    if (!el) return;
    const opts = options || {};
    const rolesMap = opts.rolesMap || {};
    const citiesMap = opts.citiesMap || {};

    if (!Array.isArray(list) || list.length === 0) {
      el.innerHTML =
        '<div class="rec-empty">' +
        esc(opts.emptyText || "Пока нет подходящих вакансий. Обновите резюме или загляните позже — подбор пересчитывается автоматически.") +
        "</div>";
      return;
    }

    const peerScores = list.map((v) => v.match_score);

    el.innerHTML =
      '<div class="rec-list">' +
      list
        .map((v) => {
          const roleName = rolesMap[String(v.role_type_id)] || "Должность #" + v.role_type_id;
          const cityName = citiesMap[String(v.project_city_id)] || "";
          const commProj = v.project_employment_intent === "commercial";
          const metaItems = [];
          if (commProj) {
            const salaryRub = vacancySalaryRub(v.salary_amount);
            const salaryTyp = vacancySalaryType(v.salary_type);
            let salaryVal = null;
            if (salaryRub !== "—") salaryVal = salaryTyp !== "—" ? salaryRub + " · " + salaryTyp : salaryRub;
            else if (salaryTyp !== "—") salaryVal = salaryTyp;
            if (salaryVal) metaItems.push(["Зарплата", salaryVal]);
            const wf = WORK_LABELS[v.work_format];
            if (wf) metaItems.push(["Формат", wf]);
            if (String(cityName || "").trim()) metaItems.push(["Город", String(cityName).trim()]);
          } else if (String(cityName || "").trim()) {
            metaItems.push(["Город", String(cityName).trim()]);
          }
          metaItems.push(["Опыт", EXP_LABELS[v.experience] || EXP_LABELS.none]);

          return (
            '<article class="rec-card" data-vacancy-id="' +
            esc(String(v.vacancy_id)) +
            '">' +
            '<div class="rec-card-head">' +
            '<div><div class="rec-card-title">' +
            esc(roleName) +
            '</div><div class="rec-card-sub">' +
            esc(v.project_title) +
            (v.project_company_name ? " · " + esc(v.project_company_name) : "") +
            "</div></div>" +
            '<span class="rec-score" title="' +
            esc(MATCH_SCORE_TITLE) +
            '">' +
            esc(formatMatchScore(v.match_score, peerScores)) +
            "</span></div>" +
            '<div class="rec-meta">' +
            metaItems.map(([k, val]) => '<span class="rec-meta-item"><b>' + esc(k) + ":</b>" + esc(val) + "</span>").join("") +
            '<span class="rec-meta-item"><b>Тип:</b>' +
            esc(INTENT_LABELS[v.project_employment_intent] || v.project_employment_intent) +
            "</span></div>" +
            '<div class="rec-actions">' +
            '<button type="button" class="action-btn" data-rec-view-vacancy="' +
            esc(String(v.vacancy_id)) +
            '" data-rec-view-project="' +
            esc(String(v.project_id)) +
            '">Проект</button>' +
            (opts.showApply !== false
              ? '<button type="button" class="action-btn action-btn--accent" data-rec-apply-vacancy="' +
                esc(String(v.vacancy_id)) +
                '">Откликнуться</button>'
              : "") +
            "</div></article>"
          );
        })
        .join("") +
      "</div>";

    el.querySelectorAll("[data-rec-view-vacancy]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const vacancyId = btn.getAttribute("data-rec-view-vacancy");
        const projectId = btn.getAttribute("data-rec-view-project");
        const vacancyData = list.find((x) => String(x.vacancy_id) === vacancyId);
        if (vacancyData) {
          try {
            sessionStorage.setItem("tp_vacancy_view_" + vacancyId, JSON.stringify(vacancyData));
          } catch (_) {}
        }
        global.location.href =
          "./card_project.html?vacancy=" +
          encodeURIComponent(vacancyId) +
          "&project=" +
          encodeURIComponent(projectId) +
          "&catalog=1";
      });
    });

    el.querySelectorAll("[data-rec-apply-vacancy]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const vacancyId = btn.getAttribute("data-rec-apply-vacancy");
        if (!vacancyId) return;
        if (typeof opts.onApply === "function") {
          opts.onApply(vacancyId, btn);
          return;
        }
        const resumeId = opts.resumeId;
        if (resumeId == null) return;
        btn.disabled = true;
        try {
          await applyToVacancy(resumeId, vacancyId);
          if (typeof global.showNotification === "function") {
            global.showNotification("Отклик отправлен.", "success", 4000);
          } else {
            global.alert("Отклик отправлен.");
          }
        } catch (e) {
          const line = e && e.message ? e.message : "Не удалось отправить отклик";
          if (typeof global.showNotification === "function") {
            global.showNotification(typeof global.tpUserFacingErrorLine === "function" ? global.tpUserFacingErrorLine(line) : line, "error", 5000);
          } else {
            global.alert(line);
          }
        }
        btn.disabled = false;
      });
    });
  }

  function renderResumeCards(list, container, options) {
    const el = typeof container === "string" ? document.getElementById(container) : container;
    if (!el) return;
    const opts = options || {};

    if (!Array.isArray(list) || list.length === 0) {
      el.innerHTML =
        '<div class="rec-empty">' +
        esc(opts.emptyText || "Пока нет подходящих резюме. Попробуйте позже или расширьте требования вакансии.") +
        "</div>";
      return;
    }

    const peerScores = list.map((r) => r.match_score);

    el.innerHTML =
      '<div class="rec-list">' +
      list
        .map((r) => {
          const avatar =
            r.avatar_url && typeof global.tpAvatarSrcFromApiField === "function"
              ? global.tpAvatarSrcFromApiField(r.avatar_url)
              : "./assets/avatar-default.png";
          const params = new URLSearchParams({ id: String(r.id) });
          if (r.user_id) params.set("user_id", String(r.user_id));
          params.set("from", "projects");
          return (
            '<article class="rec-card">' +
            '<div class="rec-resume-row">' +
            '<img class="rec-resume-avatar" src="' +
            esc(avatar) +
            '" alt="" onerror="this.src=\'./assets/avatar-default.png\'">' +
            '<div class="rec-resume-main">' +
            '<div class="rec-card-head">' +
            '<div><div class="rec-card-title">' +
            esc(r.desired_position || "Резюме") +
            '</div><div class="rec-card-sub">' +
            esc(INTENT_LABELS[r.employment_intent] || r.employment_intent) +
            (r.skills_count ? " · навыков: " + esc(String(r.skills_count)) : "") +
            "</div></div>" +
            '<span class="rec-score" title="' +
            esc(MATCH_SCORE_TITLE) +
            '">' +
            esc(formatMatchScore(r.match_score, peerScores)) +
            "</span></div>" +
            '<div class="rec-actions">' +
            '<button type="button" class="action-btn" data-rec-view-resume="' +
            esc(params.toString()) +
            '">Резюме</button>' +
            (opts.showInvite !== false
              ? '<button type="button" class="action-btn action-btn--accent" data-rec-invite-resume="' +
                esc(String(r.id)) +
                '">Пригласить</button>'
              : "") +
            "</div></div></div></article>"
          );
        })
        .join("") +
      "</div>";

    el.querySelectorAll("[data-rec-view-resume]").forEach((btn) => {
      btn.addEventListener("click", () => {
        global.location.href = "./card_resume.html?" + btn.getAttribute("data-rec-view-resume");
      });
    });

    el.querySelectorAll("[data-rec-invite-resume]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const resumeId = btn.getAttribute("data-rec-invite-resume");
        const vacancyId = opts.vacancyId;
        if (!resumeId || vacancyId == null) return;
        if (typeof opts.onInvite === "function") {
          opts.onInvite(resumeId, btn);
          return;
        }
        btn.disabled = true;
        try {
          await inviteResumeToVacancy(vacancyId, resumeId);
          if (typeof global.showNotification === "function") {
            global.showNotification("Приглашение отправлено.", "success", 4000);
          } else {
            global.alert("Приглашение отправлено.");
          }
        } catch (e) {
          const line = e && e.message ? e.message : "Не удалось отправить приглашение";
          if (typeof global.showNotification === "function") {
            global.showNotification(typeof global.tpUserFacingErrorLine === "function" ? global.tpUserFacingErrorLine(line) : line, "error", 5000);
          } else {
            global.alert(line);
          }
        }
        btn.disabled = false;
      });
    });
  }

  async function loadDictionaries() {
    const [cities, roles] = await Promise.all([
      fetchJson("/cities").catch(() => []),
      fetchJson("/roles_dictionary").catch(() => []),
    ]);
    const citiesMap = {};
    const rolesMap = {};
    if (Array.isArray(cities)) cities.forEach((c) => { if (c && c.id != null) citiesMap[String(c.id)] = c.title || ""; });
    if (Array.isArray(roles)) roles.forEach((r) => { if (r && r.id != null) rolesMap[String(r.id)] = r.name || ""; });
    return { citiesMap, rolesMap };
  }

  global.tpRecFormatMatchScore = formatMatchScore;
  global.tpFetchRecommendedVacancies = fetchRecommendedVacancies;
  global.tpFetchRecommendedResumes = fetchRecommendedResumes;
  global.tpRenderRecommendedVacancyCards = renderVacancyCards;
  global.tpRenderRecommendedResumeCards = renderResumeCards;
  global.tpRecLoadDictionaries = loadDictionaries;
  global.tpRecApplyToVacancy = applyToVacancy;
  global.tpRecInviteResume = inviteResumeToVacancy;
})(typeof window !== "undefined" ? window : globalThis);
