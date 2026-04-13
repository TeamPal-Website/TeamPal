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
