const express = require("express");
const router = express.Router();
const { impactSummary } = require("../controllers/impactController");

// Public - shown on landing/impact page
router.get("/", impactSummary);

module.exports = router;
