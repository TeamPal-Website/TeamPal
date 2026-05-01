(function (g) {
  var RU = /^[А-ЯЁа-яё]+(?:[-' ][А-ЯЁа-яё]+)*$/;
  var PHONE = /^(\+7|8)\d{10}$/;
  var TG = /^@[A-Za-z0-9_]{5,32}$/;
  var GH = /^https?:\/\/.+/;

  function ws(s) {
    return String(s || "").replace(/\s+/g, " ").trim();
  }

  g.tpProfileIncompleteMessage = function (data) {
    if (!data) return "Сначала заполните личную информацию в кабинете";
    var fn = ws(data.first_name);
    var ln = ws(data.last_name);
    if (!fn) return "Укажите имя в разделе «Личная информация»";
    if (!ln) return "Укажите фамилию в разделе «Личная информация»";
    if (!RU.test(fn) || !RU.test(ln))
      return "Имя и фамилия: только русские буквы, как в личном кабинете";

    var age = data.age;
    if (age == null || age === "" || Number(age) < 16 || Number(age) > 100)
      return "Укажите возраст (от 16 до 100 лет) в личном кабинете";

    if (!data.gender) return "Выберите пол в личном кабинете";

    var c = data.contacts;
    if (!c || typeof c !== "object") return "Заполните контакты в личном кабинете (телефон, Telegram, GitHub)";

    var phone = String(c.phone || "")
      .replace(/\s/g, "")
      .replace(/-/g, "")
      .replace(/\(/g, "")
      .replace(/\)/g, "");
    if (!phone || !PHONE.test(phone))
      return "Укажите корректный российский телефон в личном кабинете";

    var tg = String(c.telegram || "").trim();
    if (!tg || !TG.test(tg)) return "Укажите Telegram в формате @username в личном кабинете";

    var gh = String(c.github || "").trim();
    if (!gh || !GH.test(gh)) return "Укажите ссылку на GitHub (https://…) в личном кабинете";

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
