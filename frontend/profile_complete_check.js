(function (g) {
  var RU = /^[А-ЯЁа-яё]+(?:[-' ][А-ЯЁа-яё]+)*$/;
  var PHONE = /^(\+7|8)\d{10}$/;
  var TG = /^@[A-Za-z0-9_]{5,32}$/;
  var GH = /^https?:\/\/.+/;
  var PROFILE_INCOMPLETE_MSG = "Заполните полностью данные в Личном кабинете";

  function ws(s) {
    return String(s || "").replace(/\s+/g, " ").trim();
  }

  g.tpProfileIncompleteMessage = function (data) {
    if (!data) return PROFILE_INCOMPLETE_MSG;
    var fn = ws(data.first_name);
    var ln = ws(data.last_name);
    if (!fn || !ln || !RU.test(fn) || !RU.test(ln)) return PROFILE_INCOMPLETE_MSG;

    var age = data.age;
    if (age == null || age === "" || Number(age) < 16 || Number(age) > 100) return PROFILE_INCOMPLETE_MSG;

    if (!data.gender) return PROFILE_INCOMPLETE_MSG;

    var c = data.contacts;
    if (!c || typeof c !== "object") return PROFILE_INCOMPLETE_MSG;

    var phone = String(c.phone || "")
      .replace(/\s/g, "")
      .replace(/-/g, "")
      .replace(/\(/g, "")
      .replace(/\)/g, "");
    if (!phone || !PHONE.test(phone)) return PROFILE_INCOMPLETE_MSG;

    var tg = String(c.telegram || "").trim();
    if (!tg || !TG.test(tg)) return PROFILE_INCOMPLETE_MSG;

    var gh = String(c.github || "").trim();
    if (!gh || !GH.test(gh)) return PROFILE_INCOMPLETE_MSG;

    return null;
  };

  g.tpFetchProfileIncompleteMessage = function (apiBaseUrl, credentials) {
    return fetch(apiBaseUrl + "/profiles/me", { credentials: credentials || "include" }).then(function (r) {
      if (!r.ok) return "Не удалось проверить профиль";
      return r.json().then(function (data) {
        return g.tpProfileIncompleteMessage(data);
      });
    });
  };
})(typeof window !== "undefined" ? window : globalThis);
