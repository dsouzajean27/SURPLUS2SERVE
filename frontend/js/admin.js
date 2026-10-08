const user = requireAuth("admin");
if (user) document.getElementById("userName").textContent = `${user.name} (Admin)`;

document.getElementById("logoutBtn").addEventListener("click", () => {
  clearSession();
  window.location.href = "index.html";
});

async function loadStats() {
  const grid = document.getElementById("statsGrid");
  try {
    const stats = await apiRequest("/admin/stats");
    grid.innerHTML = `
      ${statBox(stats.totalUsers, "Total Users")}
      ${statBox(stats.totalDonors, "Donors")}
      ${statBox(stats.totalNgos, "NGOs")}
      ${statBox(stats.unverifiedUsers, "Pending Verification")}
      ${statBox(stats.totalDonations, "Total Donations")}
      ${statBox(stats.totalRequirements, "Total Requirements")}
    `;
  } catch (err) {
    grid.innerHTML = `<div class="error-msg">Error: ${err.message}</div>`;
  }
}
function statBox(num, label) {
  return `<div class="stat-box"><div class="num">${num}</div><div class="label">${label}</div></div>`;
}

async function loadUsers() {
  const tbody = document.getElementById("usersTableBody");
  tbody.innerHTML = `<tr><td colspan="5">Loading...</td></tr>`;
  try {
    const { users } = await apiRequest("/admin/users");
    tbody.innerHTML = users
      .map(
        (u) => `
      <tr>
        <td>${u.name}</td>
        <td>${u.email}</td>
        <td>${u.role}</td>
        <td>${u.verified ? "✅" : "❌"}</td>
        <td>
          ${!u.verified ? `<button data-verify="${u.id}">Verify</button>` : ""}
          <button class="danger" data-deluser="${u.id}">Delete</button>
        </td>
      </tr>`
      )
      .join("");

    document.querySelectorAll("[data-verify]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        await apiRequest(`/admin/users/${btn.dataset.verify}/verify`, { method: "PATCH" });
        loadUsers();
        loadStats();
      });
    });
    document.querySelectorAll("[data-deluser]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm("Delete this user?")) return;
        await apiRequest(`/admin/users/${btn.dataset.deluser}`, { method: "DELETE" });
        loadUsers();
        loadStats();
      });
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5">Error: ${err.message}</td></tr>`;
  }
}

async function loadDonations() {
  const tbody = document.getElementById("donationsTableBody");
  tbody.innerHTML = `<tr><td colspan="5">Loading...</td></tr>`;
  try {
    const { donations } = await apiRequest("/donations");
    if (!donations.length) {
      tbody.innerHTML = `<tr><td colspan="5">No donations yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = donations
      .slice()
      .reverse()
      .map(
        (d) => `
      <tr>
        <td>${d.foodType}</td>
        <td>${d.quantity}</td>
        <td>${d.servings}</td>
        <td><span class="badge ${d.status}">${d.status.replace("_", " ")}</span></td>
        <td>${new Date(d.expiryTime).toLocaleString()}</td>
      </tr>`
      )
      .join("");
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5">Error: ${err.message}</td></tr>`;
  }
}

loadStats();
loadUsers();
loadDonations();
