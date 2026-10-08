const user = requireAuth("donor");
if (user) document.getElementById("userName").textContent = `${user.name} (Donor)`;

document.getElementById("logoutBtn").addEventListener("click", () => {
  clearSession();
  window.location.href = "index.html";
});

// ---- Map preview ----
const map = L.map("map").setView([19.076, 72.8777], 11); // default: Mumbai
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);
let marker = null;

function updateMapPreview() {
  const lat = parseFloat(document.getElementById("lat").value);
  const lng = parseFloat(document.getElementById("lng").value);
  if (isNaN(lat) || isNaN(lng)) return;
  if (marker) marker.setLatLng([lat, lng]);
  else marker = L.marker([lat, lng]).addTo(map);
  map.setView([lat, lng], 13);
}
document.getElementById("lat").addEventListener("input", updateMapPreview);
document.getElementById("lng").addEventListener("input", updateMapPreview);

// ---- Post donation ----
document.getElementById("donationForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = document.getElementById("donationMsg");
  msg.textContent = "";
  try {
    const body = {
      foodType: document.getElementById("foodType").value,
      quantity: document.getElementById("quantity").value,
      servings: document.getElementById("servings").value,
      prepTime: document.getElementById("prepTime").value || null,
      expiryTime: document.getElementById("expiryTime").value,
      imageUrl: document.getElementById("imageUrl").value || null,
      location: {
        address: document.getElementById("address").value,
        lat: parseFloat(document.getElementById("lat").value),
        lng: parseFloat(document.getElementById("lng").value),
      },
    };
    await apiRequest("/donations", { method: "POST", body });
    msg.className = "success-msg";
    msg.textContent = "Donation posted! AI has generated NGO recommendations.";
    e.target.reset();
    loadDonations();
  } catch (err) {
    msg.className = "error-msg";
    msg.textContent = err.message;
  }
});

// ---- List my donations ----
async function loadDonations() {
  const tbody = document.getElementById("donationsTableBody");
  tbody.innerHTML = `<tr><td colspan="7">Loading...</td></tr>`;
  try {
    const { donations } = await apiRequest("/donations?mine=true");
    if (!donations.length) {
      tbody.innerHTML = `<tr><td colspan="7">No donations posted yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = donations
      .slice()
      .reverse()
      .map((d) => {
        const topRec = d.recommendations && d.recommendations[0];
        const actionBtn = renderActionButton(d);
        return `
        <tr>
          <td>${d.foodType}</td>
          <td>${d.quantity}</td>
          <td>${d.servings}</td>
          <td><span class="badge ${d.status}">${d.status.replace("_", " ")}</span></td>
          <td>${new Date(d.expiryTime).toLocaleString()}</td>
          <td>${topRec ? `${topRec.ngo.name} (score ${topRec.score})` : "—"}</td>
          <td>${actionBtn}</td>
        </tr>`;
      })
      .join("");

    // wire up action buttons
    document.querySelectorAll("[data-action]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        try {
          await apiRequest(`/donations/${btn.dataset.id}/status`, {
            method: "PATCH",
            body: { status: btn.dataset.action },
          });
          loadDonations();
        } catch (err) {
          alert(err.message);
        }
      });
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7">Error loading donations: ${err.message}</td></tr>`;
  }
}

function renderActionButton(d) {
  if (d.status === "accepted") {
    return `<button data-action="pickup_pending" data-id="${d.id}">Mark Ready for Pickup</button>`;
  }
  if (d.status === "delivered") {
    return `<button data-action="completed" data-id="${d.id}">Mark Completed</button>`;
  }
  return "";
}

loadDonations();
