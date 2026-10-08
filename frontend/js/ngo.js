const user = requireAuth("ngo");
if (user) document.getElementById("userName").textContent = `${user.name} (NGO)`;

document.getElementById("logoutBtn").addEventListener("click", () => {
  clearSession();
  window.location.href = "index.html";
});

// ---- Map preview ----
const defaultCenter = user && user.location ? [user.location.lat, user.location.lng] : [19.076, 72.8777];
const map = L.map("map").setView(defaultCenter, 12);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);
let marker = L.marker(defaultCenter).addTo(map);

function updateMapPreview() {
  const lat = parseFloat(document.getElementById("lat").value);
  const lng = parseFloat(document.getElementById("lng").value);
  if (isNaN(lat) || isNaN(lng)) return;
  marker.setLatLng([lat, lng]);
  map.setView([lat, lng], 13);
}
document.getElementById("lat").addEventListener("input", updateMapPreview);
document.getElementById("lng").addEventListener("input", updateMapPreview);

// Pre-fill lat/lng/address from NGO's registered location, if available
if (user && user.location) {
  document.getElementById("lat").value = user.location.lat ?? "";
  document.getElementById("lng").value = user.location.lng ?? "";
  document.getElementById("address").value = user.location.address ?? "";
}

// ---- Post requirement ----
document.getElementById("requirementForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const msg = document.getElementById("reqMsg");
  msg.textContent = "";
  try {
    const body = {
      foodType: document.getElementById("foodType").value,
      requiredQuantity: document.getElementById("requiredQuantity").value,
      urgency: document.getElementById("urgency").value,
      deadline: document.getElementById("deadline").value,
      location: {
        address: document.getElementById("address").value,
        lat: parseFloat(document.getElementById("lat").value),
        lng: parseFloat(document.getElementById("lng").value),
      },
    };
    await apiRequest("/requirements", { method: "POST", body });
    msg.className = "success-msg";
    msg.textContent = "Requirement posted.";
    e.target.reset();
    loadRequirements();
  } catch (err) {
    msg.className = "error-msg";
    msg.textContent = err.message;
  }
});

// ---- My requirements ----
async function loadRequirements() {
  const tbody = document.getElementById("reqTableBody");
  tbody.innerHTML = `<tr><td colspan="5">Loading...</td></tr>`;
  try {
    const { requirements } = await apiRequest("/requirements?mine=true");
    if (!requirements.length) {
      tbody.innerHTML = `<tr><td colspan="5">No requirements posted yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = requirements
      .slice()
      .reverse()
      .map(
        (r) => `
      <tr>
        <td>${r.foodType}</td>
        <td>${r.requiredQuantity}</td>
        <td><span class="badge urgency-${r.urgency}">${r.urgency}</span></td>
        <td>${r.deadline ? new Date(r.deadline).toLocaleString() : "—"}</td>
        <td><button class="danger" data-del="${r.id}">Delete</button></td>
      </tr>`
      )
      .join("");

    document.querySelectorAll("[data-del]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm("Delete this requirement?")) return;
        await apiRequest(`/requirements/${btn.dataset.del}`, { method: "DELETE" });
        loadRequirements();
      });
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5">Error: ${err.message}</td></tr>`;
  }
}

// ---- Nearby donations ----
async function loadNearby() {
  const tbody = document.getElementById("nearbyTableBody");
  tbody.innerHTML = `<tr><td colspan="7">Loading...</td></tr>`;
  try {
    const radius = document.getElementById("radiusInput").value || 25;
    const lat = user.location?.lat;
    const lng = user.location?.lng;
    const query = lat && lng ? `?status=posted&nearLat=${lat}&nearLng=${lng}&maxDistanceKm=${radius}` : `?status=posted`;
    const { donations } = await apiRequest(`/donations${query}`);
    if (!donations.length) {
      tbody.innerHTML = `<tr><td colspan="7">No nearby donations available right now.</td></tr>`;
      return;
    }
    tbody.innerHTML = donations
      .map(
        (d) => `
      <tr>
        <td>${d.foodType}</td>
        <td>${d.quantity}</td>
        <td>${d.servings}</td>
        <td>${d.distanceKm != null ? d.distanceKm + " km" : "—"}</td>
        <td><span class="badge ${d.status}">${d.status}</span></td>
        <td>${new Date(d.expiryTime).toLocaleString()}</td>
        <td><button data-accept="${d.id}">Accept</button></td>
      </tr>`
      )
      .join("");

    document.querySelectorAll("[data-accept]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        try {
          await apiRequest(`/donations/${btn.dataset.accept}/status`, {
            method: "PATCH",
            body: { status: "accepted", ngoId: user.id },
          });
          loadNearby();
          loadAccepted();
        } catch (err) {
          alert(err.message);
        }
      });
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7">Error: ${err.message}</td></tr>`;
  }
}

document.getElementById("radiusInput").addEventListener("change", loadNearby);

// ---- My accepted donations (track through pickup -> delivered) ----
async function loadAccepted() {
  const tbody = document.getElementById("acceptedTableBody");
  tbody.innerHTML = `<tr><td colspan="5">Loading...</td></tr>`;
  try {
    const { donations } = await apiRequest(`/donations`);
    const mine = donations.filter((d) => d.acceptedNgoId === user.id);
    if (!mine.length) {
      tbody.innerHTML = `<tr><td colspan="5">No accepted donations yet.</td></tr>`;
      return;
    }
    tbody.innerHTML = mine
      .map((d) => {
        const action =
          d.status === "pickup_pending"
            ? `<button data-deliver="${d.id}">Mark Delivered</button>`
            : "";
        return `
        <tr>
          <td>${d.foodType}</td>
          <td>${d.quantity}</td>
          <td><span class="badge ${d.status}">${d.status.replace("_", " ")}</span></td>
          <td>${new Date(d.expiryTime).toLocaleString()}</td>
          <td>${action}</td>
        </tr>`;
      })
      .join("");

    document.querySelectorAll("[data-deliver]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        try {
          await apiRequest(`/donations/${btn.dataset.deliver}/status`, {
            method: "PATCH",
            body: { status: "delivered" },
          });
          loadAccepted();
        } catch (err) {
          alert(err.message);
        }
      });
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5">Error: ${err.message}</td></tr>`;
  }
}

loadRequirements();
loadNearby();
loadAccepted();
