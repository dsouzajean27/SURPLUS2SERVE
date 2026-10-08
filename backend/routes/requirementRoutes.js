const express = require("express");
const router = express.Router();
const { authenticate, requireRole } = require("../middleware/auth");
const {
  createRequirement,
  listRequirements,
  deleteRequirement,
} = require("../controllers/requirementController");

router.post("/", authenticate, requireRole("ngo"), createRequirement);
router.get("/", authenticate, listRequirements);
router.delete("/:id", authenticate, requireRole("ngo", "admin"), deleteRequirement);

module.exports = router;
