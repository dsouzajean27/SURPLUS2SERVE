const { v4: uuidv4 } = require("uuid");
const { readData, writeData, getDistanceKm, hoursUntil } = require("../utils/helpers");
const { recommendNgosForDonation } = require("../utils/recommend");

const VALID_STATUSES = ["posted", "accepted", "pickup_pending", "delivered", "completed", "expired"];

// Forward-only status transitions allowed via the normal flow
const NEXT_STATUS = {
  posted: ["accepted", "expired"],
  accepted: ["pickup_pending", "expired"],
  pickup_pending: ["delivered"],
  delivered: ["completed"],
  completed: [],
  expired: [],
};

function createDonation(req, res) {
  const { foodType, quantity, servings, prepTime, expiryTime, location, imageUrl } = req.body;

  if (!foodType || !quantity || !servings || !expiryTime || !location) {
    return res.status(400).json({
      error: "foodType, quantity, servings, expiryTime, and location are required",
    });
  }

  const donations = readData("donations");

  const newDonation = {
    id: uuidv4(),
    donorId: req.user.id,
    foodType,
    quantity: Number(quantity),
    servings: Number(servings),
    prepTime: prepTime || null,
    expiryTime,
    location, // { lat, lng, address }
    imageUrl: imageUrl || null,
    status: "posted",
    recommendations: [],
    acceptedNgoId: null,
    createdAt: new Date().toISOString(),
    statusHistory: [{ status: "posted", at: new Date().toISOString() }],
  };

  // Run AI-based recommendation engine immediately on posting
  const ranked = recommendNgosForDonation(newDonation);
  newDonation.recommendations = ranked.slice(0, 5); // top 5 matches

  donations.push(newDonation);
  writeData("donations", donations);

  res.status(201).json({ donation: newDonation });
}

function listDonations(req, res) {
  let donations = readData("donations");
  applyExpiry(donations);

  const { mine, status, nearLat, nearLng, maxDistanceKm } = req.query;

  if (mine === "true") {
    donations = donations.filter((d) => d.donorId === req.user.id);
  }
  if (status) {
    donations = donations.filter((d) => d.status === status);
  }
  if (nearLat && nearLng) {
    const origin = { lat: parseFloat(nearLat), lng: parseFloat(nearLng) };
    donations = donations
      .map((d) => ({ ...d, distanceKm: getDistanceKm(origin, d.location) }))
      .filter((d) => (maxDistanceKm ? d.distanceKm <= parseFloat(maxDistanceKm) : true))
      .sort((a, b) => a.distanceKm - b.distanceKm);
  }

  res.json({ donations });
}

function getDonation(req, res) {
  const donations = readData("donations");
  applyExpiry(donations);
  const donation = donations.find((d) => d.id === req.params.id);
  if (!donation) return res.status(404).json({ error: "Donation not found" });
  res.json({ donation });
}

function updateStatus(req, res) {
  const { status, ngoId } = req.body;
  if (!VALID_STATUSES.includes(status)) {
    return res.status(400).json({ error: "Invalid status value" });
  }

  const donations = readData("donations");
  const donation = donations.find((d) => d.id === req.params.id);
  if (!donation) return res.status(404).json({ error: "Donation not found" });

  const allowedNext = NEXT_STATUS[donation.status] || [];
  const isAdmin = req.user.role === "admin";
  if (!isAdmin && !allowedNext.includes(status)) {
    return res.status(400).json({
      error: `Cannot move donation from '${donation.status}' to '${status}'`,
    });
  }

  // Only donor (owner), accepting NGO, or admin can update
  const isOwnerDonor = req.user.role === "donor" && req.user.id === donation.donorId;
  const isAcceptingNgo = req.user.role === "ngo";
  if (!isAdmin && !isOwnerDonor && !isAcceptingNgo) {
    return res.status(403).json({ error: "Not authorized to update this donation" });
  }

  if (status === "accepted") {
    if (!ngoId) return res.status(400).json({ error: "ngoId is required to accept a donation" });
    donation.acceptedNgoId = ngoId;
  }

  donation.status = status;
  donation.statusHistory.push({ status, at: new Date().toISOString() });

  writeData("donations", donations);
  res.json({ donation });
}

function getRecommendations(req, res) {
  const donations = readData("donations");
  const donation = donations.find((d) => d.id === req.params.id);
  if (!donation) return res.status(404).json({ error: "Donation not found" });

  const ranked = recommendNgosForDonation(donation);
  res.json({ recommendations: ranked });
}

// Mark any non-final donation whose expiry time has passed as 'expired'
function applyExpiry(donations) {
  let changed = false;
  donations.forEach((d) => {
    if (!["completed", "expired"].includes(d.status) && hoursUntil(d.expiryTime) <= 0) {
      d.status = "expired";
      d.statusHistory.push({ status: "expired", at: new Date().toISOString() });
      changed = true;
    }
  });
  if (changed) writeData("donations", donations);
}

module.exports = {
  createDonation,
  listDonations,
  getDonation,
  updateStatus,
  getRecommendations,
};
