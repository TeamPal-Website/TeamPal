const API_BASE_URL =
  typeof window !== "undefined" && window.location && window.location.origin
    ? window.location.origin
    : "http://localhost:8000";
