const { readData, writeData } = require("../utils/helpers");

function listUsers(req, res) {
  const users = readData("users").map(({ passwordHash, ...safe }) => safe);
  res.json({ users });
}

function verifyUser(req, res) {
  const users = readData("users");
  const user = users.find((u) => u.id === req.params.id);
  if (!user) return res.status(404).json({ error: "User not found" });
  user.verified = true;
  writeData("users", users);
  const { passwordHash, ...safe } = user;
  res.json({ user: safe });
}

function deleteUser(req, res) {
  let users = readData("users");
  const exists = users.find((u) => u.id === req.params.id);
  if (!exists) return res.status(404).json({ error: "User not found" });
  users = users.filter((u) => u.id !== req.params.id);
  writeData("users", users);
  res.json({ success: true });
}

function platformStats(req, res) {
  const users = readData("users");
  const donations = readData("donations");
  const requirements = readData("requirements");

  res.json({
    totalUsers: users.length,
    totalDonors: users.filter((u) => u.role === "donor").length,
    totalNgos: users.filter((u) => u.role === "ngo").length,
    unverifiedUsers: users.filter((u) => !u.verified).length,
    totalDonations: donations.length,
    donationsByStatus: donations.reduce((acc, d) => {
      acc[d.status] = (acc[d.status] || 0) + 1;
      return acc;
    }, {}),
    totalRequirements: requirements.length,
  });
}

module.exports = { listUsers, verifyUser, deleteUser, platformStats };
