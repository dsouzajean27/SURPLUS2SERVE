const { readData, getDistanceKm, hoursUntil } = require("./helpers");

const URGENCY_SCORE = { high: 3, medium: 2, low: 1 };

/**
 * Recommends the best-matching NGO requirement(s) for a donation.
 * Considers: food type match, quantity fit, distance, and urgency/demand.
 * Returns a ranked array of { requirement, ngo, score, distanceKm }.
 */
function recommendNgosForDonation(donation) {
  const requirements = readData("requirements");
  const users = readData("users");

  const scored = requirements
    .map((req) => {
      const ngo = users.find((u) => u.id === req.ngoId && u.role === "ngo");
      if (!ngo) return null;

      const distanceKm = getDistanceKm(donation.location, req.location);
      if (distanceKm === null) return null;

      let score = 0;

      // Food type match (case-insensitive), "any" always matches
      const typeMatch =
        req.foodType.toLowerCase() === "any" ||
        req.foodType.toLowerCase() === donation.foodType.toLowerCase();
      score += typeMatch ? 40 : 0;

      // Quantity fit: reward requirements whose need is close to (or less than) supply
      if (req.requiredQuantity <= donation.quantity) {
        score += 25;
      } else {
        // partial credit if donation at least covers some of the need
        score += Math.max(0, 15 - (req.requiredQuantity - donation.quantity));
      }

      // Distance: closer is better (max 20 points, decays with distance)
      score += Math.max(0, 20 - distanceKm);

      // Urgency/demand
      score += (URGENCY_SCORE[req.urgency] || 1) * 5;

      // Deadline proximity bonus - requirement deadline coming up soon gets priority
      if (req.deadline) {
        const hrsLeft = hoursUntil(req.deadline);
        if (hrsLeft > 0 && hrsLeft < 24) score += 10;
      }

      return {
        requirement: req,
        ngo: { id: ngo.id, name: ngo.name, location: ngo.location },
        distanceKm,
        score: Math.round(score * 10) / 10,
      };
    })
    .filter(Boolean)
    .sort((a, b) => b.score - a.score);

  return scored;
}

module.exports = { recommendNgosForDonation };
