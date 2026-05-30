(function () {
  "use strict";

  if (window.__tpNotifyBellInit) return;
  window.__tpNotifyBellInit = true;

  var POLL_MS = 20000;
  var BADGE_STYLE =
    "position:absolute;top:-4px;right:-4px;background:#f85a0b;color:#fff;border-radius:50%;font-size:10px;font-weight:700;min-width:18px;height:18px;padding:0 4px;display:flex;align-items:center;justify-content:center;pointer-events:none;";

  function apiBase() {
    var u = typeof window.API_BASE_URL === "string" ? window.API_BASE_URL.trim() : "";
    return u ? u.replace(/\/+$/, "") : "";
  }

  function styleNotifyButtons() {
    var list = document.querySelectorAll(".notify-btn");
    for (var i = 0; i < list.length; i++) {
      list[i].style.position = "relative";
    }
  }

  async function updateAllNotifyBadges() {
    var base = apiBase();
    if (!base) return;

    var buttons = document.querySelectorAll(".notify-btn");
    if (!buttons.length) return;
    styleNotifyButtons();

    var resp;
    try {
      resp = await fetch(base + "/notifications/unread_count", {
        credentials: "include",
        cache: "no-store",
      });
    } catch (_) {
      return;
    }

    if (resp.status === 401 || resp.status === 403) {
      document.querySelectorAll(".notify-btn .notif-badge").forEach(function (b) {
        b.remove();
      });
      return;
    }

    if (!resp.ok) {
      return;
    }

    var data;
    try {
      data = await resp.json();
    } catch (_) {
      return;
    }

    var count = Number(data.unread_count ?? 0);
    if (!Number.isFinite(count) || count < 0) count = 0;

    document.querySelectorAll(".notify-btn").forEach(function (notifyBtn) {
      var badge = notifyBtn.querySelector(".notif-badge");
      if (count > 0) {
        if (!badge) {
          badge = document.createElement("span");
          badge.className = "notif-badge";
          badge.setAttribute("aria-hidden", "true");
          badge.style.cssText = BADGE_STYLE;
          notifyBtn.appendChild(badge);
        }
        badge.textContent = count > 99 ? "99+" : String(count);
      } else if (badge) {
        badge.remove();
      }
    });
  }

  function startPolling() {
    void updateAllNotifyBadges();
    setInterval(function () {
      void updateAllNotifyBadges();
    }, POLL_MS);
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "visible") {
        void updateAllNotifyBadges();
      }
    });
  }

  window.tpRefreshUnreadBell = function () {
    void updateAllNotifyBadges();
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", startPolling);
  } else {
    startPolling();
  }
})();
