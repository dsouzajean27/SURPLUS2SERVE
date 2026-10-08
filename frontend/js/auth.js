// If already logged in, skip straight to the dashboard
(function redirectIfLoggedIn() {
  const user = getUser();
  if (user && getToken()) goToDashboard(user.role);
})();

const tabLogin = document.getElementById("tabLogin");
const tabRegister = document.getElementById("tabRegister");
const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");

tabLogin.addEventListener("click", () => {
  tabLogin.classList.add("active");
  tabRegister.classList.remove("active");
  loginForm.style.display = "block";
  registerForm.style.display = "none";
});

tabRegister.addEventListener("click", () => {
  tabRegister.classList.add("active");
  tabLogin.classList.remove("active");
  registerForm.style.display = "block";
  loginForm.style.display = "none";
});

loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = document.getElementById("loginMsg");
  msg.textContent = "";
  try {
    const email = document.getElementById("loginEmail").value;
    const password = document.getElementById("loginPassword").value;
    const data = await apiRequest("/auth/login", {
      method: "POST",
      body: { email, password },
      auth: false,
    });
    setSession(data.token, data.user);
    goToDashboard(data.user.role);
  } catch (err) {
    msg.className = "error-msg";
    msg.textContent = err.message;
  }
});

registerForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = document.getElementById("registerMsg");
  msg.textContent = "";
  try {
    const body = {
      role: document.getElementById("regRole").value,
      name: document.getElementById("regName").value,
      email: document.getElementById("regEmail").value,
      password: document.getElementById("regPassword").value,
      phone: document.getElementById("regPhone").value,
      location: {
        address: document.getElementById("regAddress").value,
        lat: parseFloat(document.getElementById("regLat").value),
        lng: parseFloat(document.getElementById("regLng").value),
      },
    };
    await apiRequest("/auth/register", { method: "POST", body, auth: false });
    msg.className = "success-msg";
    msg.textContent = "Registered! You can now log in." +
      (body.role !== "admin" ? " (Awaiting admin verification.)" : "");
    registerForm.reset();
  } catch (err) {
    msg.className = "error-msg";
    msg.textContent = err.message;
  }
});
