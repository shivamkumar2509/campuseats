require("dotenv").config();
const express = require("express");
const jwt = require("jsonwebtoken");
const bcrypt = require("bcryptjs");

const app = express();
const PORT = process.env.PORT || 3000;
const SECRET = process.env.JWT_SECRET || "fallback_secret";

app.use(express.json());

// Dummy Users (Password: "password123")
// Hash generated using bcrypt
const users = [
  {
    id: 1,
    username: "customer",
    passwordHash:
      "$2b$10$BttYZSfNw44E83PqeI1lRu6s3vpgih/srbL8imsS6Fpg7GJ4hHh9m",
    role: "customer",
  },
  {
    id: 2,
    username: "restaurant",
    passwordHash:
      "$2b$10$BttYZSfNw44E83PqeI1lRu6s3vpgih/srbL8imsS6Fpg7GJ4hHh9m",
    role: "restaurant",
  },
];

let items = [
  { id: 1, name: "Paneer Butter Masala", price: 250 },
  { id: 2, name: "Veg Biryani", price: 180 },
];

// 1. LOGIN ROUTE
app.post("/login", async (req, res) => {
  const { username, password } = req.body;
  const user = users.find((u) => u.username === username);

  if (!user) return res.status(401).json({ error: "Invalid credentials" });

  const validPassword = await bcrypt.compare(password, user.passwordHash);
  if (!validPassword)
    return res.status(401).json({ error: "Invalid credentials" });

  const token = jwt.sign({ userId: user.id, role: user.role }, SECRET, {
    expiresIn: "1h",
  });
  res.status(200).json({ token, role: user.role });
});

// 2. AUTHENTICATION MIDDLEWARE
function auth(req, res, next) {
  const authHeader = req.headers["authorization"];
  const token = authHeader && authHeader.split(" ")[1];

  if (!token) return res.status(401).json({ error: "Token required" });

  try {
    const decoded = jwt.verify(token, SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(401).json({ error: "Invalid or expired token" });
  }
}

// 3. AUTHORIZATION MIDDLEWARE
function requireRole(...allowedRoles) {
  return (req, res, next) => {
    if (!req.user || !allowedRoles.includes(req.user.role)) {
      return res
        .status(403)
        .json({ error: "Forbidden: Insufficient privileges" });
    }
    next();
  };
}

// ROUTES
// Read (Requires Auth)
app.get("/items", auth, (req, res) => {
  res.status(200).json(items);
});

// Write (Requires Auth + Role)
app.post("/items", auth, requireRole("restaurant"), (req, res) => {
  const { name, price } = req.body;
  if (!name || !price) {
    return res.status(422).json({ error: "Name and price are required" });
  }
  const newItem = { id: items.length + 1, name, price };
  items.push(newItem);
  res.status(201).json(newItem);
});

app.listen(PORT, () =>
  console.log(`Secure API running at http://localhost:${PORT}`),
);
