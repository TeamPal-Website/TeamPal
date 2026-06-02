/**
 * Кэш профиля в sessionStorage — мгновенно показывает имя/аватар при смене роли и перезагрузке страницы.
 */
(function (global) {
  const KEY = "tp_profile_sidebar_cache";

  function normalize(data) {
    if (!data) return null;
    return {
      firstName: data.firstName || data.first_name || "",
      lastName: data.lastName || data.last_name || "",
      age: data.age != null && data.age !== "" ? String(data.age) : "",
      gender: data.gender || "",
      phone: data.phone || (data.contacts && data.contacts.phone) || "",
      telegram: data.telegram || (data.contacts && data.contacts.telegram) || "",
      github: data.github || (data.contacts && data.contacts.github) || "",
      avatar: data.avatar || "",
      email: data.email || "",
    };
  }

  function save(data, email) {
    const p = normalize(data || {});
    if (!p) return;
    if (email) p.email = String(email).trim();
    try {
      sessionStorage.setItem(KEY, JSON.stringify(p));
    } catch (_) {}
  }

  function load() {
    try {
      const raw = sessionStorage.getItem(KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (_) {
      return null;
    }
  }

  function displayNameFromEmail(email) {
    if (!email) return "Пользователь";
    return String(email).split("@")[0];
  }

  function applySidebar(opts) {
    const cached = load();
    if (!cached) return;
    const nameEl = document.getElementById("user-name-display");
    const mailEl = document.getElementById("user-mail");
    const avEl = document.getElementById("profile-avatar");

    if (mailEl && cached.email) mailEl.textContent = cached.email;

    let name = `${cached.firstName} ${cached.lastName}`.trim();
    if (!name && cached.email) name = displayNameFromEmail(cached.email);
    if (!name) name = "Пользователь";
    if (nameEl) nameEl.textContent = name;

    if (avEl && cached.avatar) {
      avEl.src =
        typeof global.tpMyProfileAvatarSrc === "function"
          ? global.tpMyProfileAvatarSrc(cached.avatar)
          : cached.avatar;
    }

    if (opts && opts.form) {
      const setVal = (id, val) => {
        const el = document.getElementById(id);
        if (el && val != null) el.value = val;
      };
      setVal("first-name", cached.firstName);
      setVal("last-name", cached.lastName);
      setVal("age", cached.age);
      setVal("gender", cached.gender);
      setVal("phone", cached.phone);
      setVal("telegram", cached.telegram);
      setVal("github", cached.github);
    }
  }

  function mergeInto(target) {
    const cached = load();
    if (!cached || !target) return target;
    target.firstName = cached.firstName || target.firstName;
    target.lastName = cached.lastName || target.lastName;
    target.age = cached.age || target.age;
    target.gender = cached.gender || target.gender;
    target.phone = cached.phone || target.phone;
    target.telegram = cached.telegram || target.telegram;
    target.github = cached.github || target.github;
    target.avatar = cached.avatar || target.avatar;
    return target;
  }

  global.tpProfileCacheSave = save;
  global.tpProfileCacheLoad = load;
  global.tpProfileCacheApplySidebar = applySidebar;
  global.tpProfileCacheMergeInto = mergeInto;
})();
