const express = require("express");
const router = express.Router();
const { authenticate, requireRole } = require("../middleware/auth");
const {
  createDonation,
  listDonations,
  getDonation,
  updateStatus,
  getRecommendations,
} = require("../controllers/donationController");

router.post("/", authenticate, requireRole("donor"), createDonation);
router.get("/", authenticate, listDonations);
router.get("/:id", authenticate, getDonation);
router.patch("/:id/status", authenticate, updateStatus);
router.get("/:id/recommendations", authenticate, getRecommendations);

module.exports = router;
