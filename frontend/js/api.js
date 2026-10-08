const API_BASE = "/api";

function getToken() {
  return localStorage.getItem("fr_token");
}

function getUser() {
  const raw = localStorage.getItem("fr_user");
  return raw ? JSON.parse(raw) : null;
}

function setSession(token, user) {
  localStorage.setItem("fr_token", token);
  localStorage.setItem("fr_user", JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem("fr_token");
  localStorage.removeItem("fr_user");
}

async function apiRequest(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return data;
}

// Redirect helper: send user to the right dashboard for their role
function goToDashboard(role) {
  if (role === "donor") window.location.href = "donor.html";
  else if (role === "ngo") window.location.href = "ngo.html";
  else if (role === "admin") window.location.href = "admin.html";
  else window.location.href = "index.html";
}

// Guard: call at top of protected pages, requiring one of the given roles
function requireAuth(...allowedRoles) {
  const user = getUser();
  const token = getToken();
  if (!token || !user) {
    window.location.href = "index.html";
    return null;
  }
  if (allowedRoles.length && !allowedRoles.includes(user.role)) {
    goToDashboard(user.role);
    return null;
  }
  return user;
}
