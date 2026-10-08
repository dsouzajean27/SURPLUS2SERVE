const { v4: uuidv4 } = require("uuid");
const { readData, writeData } = require("../utils/helpers");

function createRequirement(req, res) {
  const { foodType, requiredQuantity, location, urgency, deadline } = req.body;

  if (!foodType || !requiredQuantity || !location || !urgency) {
    return res.status(400).json({
      error: "foodType, requiredQuantity, location, and urgency are required",
    });
  }
  if (!["low", "medium", "high"].includes(urgency)) {
    return res.status(400).json({ error: "urgency must be low, medium, or high" });
  }

  const requirements = readData("requirements");

  const newRequirement = {
    id: uuidv4(),
    ngoId: req.user.id,
    foodType,
    requiredQuantity: Number(requiredQuantity),
    location,
    urgency,
    deadline: deadline || null,
    createdAt: new Date().toISOString(),
  };

  requirements.push(newRequirement);
  writeData("requirements", requirements);

  res.status(201).json({ requirement: newRequirement });
}

function listRequirements(req, res) {
  let requirements = readData("requirements");
  const { mine } = req.query;
  if (mine === "true") {
    requirements = requirements.filter((r) => r.ngoId === req.user.id);
  }
  res.json({ requirements });
}

function deleteRequirement(req, res) {
  let requirements = readData("requirements");
  const requirement = requirements.find((r) => r.id === req.params.id);
  if (!requirement) return res.status(404).json({ error: "Requirement not found" });
  if (requirement.ngoId !== req.user.id && req.user.role !== "admin") {
    return res.status(403).json({ error: "Not authorized to delete this requirement" });
  }
  requirements = requirements.filter((r) => r.id !== req.params.id);
  writeData("requirements", requirements);
  res.json({ success: true });
}

module.exports = { createRequirement, listRequirements, deleteRequirement };
