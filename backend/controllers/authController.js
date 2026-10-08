const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const { v4: uuidv4 } = require("uuid");
const { readData, writeData } = require("../utils/helpers");
const { JWT_SECRET } = require("../middleware/auth");

function register(req, res) {
  const { name, email, password, role, phone, location } = req.body;

  if (!name || !email || !password || !role) {
    return res.status(400).json({ error: "name, email, password, and role are required" });
  }
  if (!["donor", "ngo", "admin"].includes(role)) {
    return res.status(400).json({ error: "role must be donor, ngo, or admin" });
  }

  const users = readData("users");
  if (users.find((u) => u.email.toLowerCase() === email.toLowerCase())) {
    return res.status(409).json({ error: "Email already registered" });
  }

  const passwordHash = bcrypt.hashSync(password, 10);

  const newUser = {
    id: uuidv4(),
    name,
    email,
    passwordHash,
    role,
    phone: phone || "",
    location: location || null, // { lat, lng, address }
    verified: role === "admin" ? true : false, // donors/NGOs need admin verification
    createdAt: new Date().toISOString(),
  };

  users.push(newUser);
  writeData("users", users);

  const { passwordHash: _, ...safeUser } = newUser;
  res.status(201).json({ user: safeUser });
}

function login(req, res) {
  const { email, password } = req.body;
  if (!email || !password) {
    return res.status(400).json({ error: "email and password are required" });
  }

  const users = readData("users");
  const user = users.find((u) => u.email.toLowerCase() === email.toLowerCase());
  if (!user || !bcrypt.compareSync(password, user.passwordHash)) {
    return res.status(401).json({ error: "Invalid email or password" });
  }

  const token = jwt.sign(
    { id: user.id, role: user.role, name: user.name },
    JWT_SECRET,
    { expiresIn: "7d" }
  );

  const { passwordHash: _, ...safeUser } = user;
  res.json({ token, user: safeUser });
}

module.exports = { register, login };
