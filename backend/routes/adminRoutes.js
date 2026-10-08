const express = require("express");
const router = express.Router();
const { authenticate, requireRole } = require("../middleware/auth");
const {
  listUsers,
  verifyUser,
  deleteUser,
  platformStats,
} = require("../controllers/adminController");

router.get("/users", authenticate, requireRole("admin"), listUsers);
router.patch("/users/:id/verify", authenticate, requireRole("admin"), verifyUser);
router.delete("/users/:id", authenticate, requireRole("admin"), deleteUser);
router.get("/stats", authenticate, requireRole("admin"), platformStats);

module.exports = router;
