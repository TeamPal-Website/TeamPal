(function () {
  "use strict";

  function normalizeErrorMessage(message, type) {
    var raw = message == null ? "" : String(message);
    if (type !== "error") return raw;
    return raw
      .trim()
      .replace(/^Ошибка\s*:\s*/i, "")
      .trim();
  }

  /**
   * @param {string} message
   * @param {'error'|'success'|'warning'} [type]
   * @param {number} [duration]
   */
  window.showNotification = function (message, type, duration) {
    type = type || "error";
    duration =
      duration === undefined || duration === null ? 5000 : duration;
    var container = document.getElementById("notificationContainer");
    if (!container) {
      var fallback = normalizeErrorMessage(message, type);
      console.warn("[TeamPal]", fallback);
      try {
        window.alert(fallback);
      } catch (_) {}
      return;
    }

    var body = normalizeErrorMessage(message, type);

    var notification = document.createElement("div");
    notification.className = "notification " + type;

    var content = document.createElement("div");
    content.className = "notification-content";
    content.textContent = body;

    var closeBtn = document.createElement("div");
    closeBtn.className = "notification-close";
    closeBtn.textContent = "×";
    closeBtn.setAttribute("role", "button");
    closeBtn.setAttribute("aria-label", "Закрыть");

    notification.appendChild(content);
    notification.appendChild(closeBtn);
    container.appendChild(notification);

    function dismiss() {
      if (!notification.parentElement) return;
      notification.style.animation =
        "tpNotifyOut 0.26s ease-out forwards";
      setTimeout(function () {
        notification.remove();
      }, 260);
    }

    closeBtn.addEventListener("click", dismiss);
    setTimeout(function () {
      if (notification.parentElement) dismiss();
    }, duration);
  };
})();
