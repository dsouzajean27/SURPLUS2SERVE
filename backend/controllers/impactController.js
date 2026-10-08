const { readData } = require("../utils/helpers");

function impactSummary(req, res) {
  const donations = readData("donations");

  const completed = donations.filter((d) => d.status === "completed");

  const totalFoodDonatedServings = donations.reduce((sum, d) => sum + (d.servings || 0), 0);
  const servingsRedistributed = completed.reduce((sum, d) => sum + (d.servings || 0), 0);
  const quantityRedistributed = completed.reduce((sum, d) => sum + (d.quantity || 0), 0);

  res.json({
    totalDonations: donations.length,
    donationsCompleted: completed.length,
    totalFoodDonatedServings,
    servingsRedistributed,
    quantityRedistributed,
    estimatedServingsSupported: servingsRedistributed,
  });
}

module.exports = { impactSummary };
