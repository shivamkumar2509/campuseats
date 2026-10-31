const express = require("express");
const path = require("path");
const app = express();
const PORT = 3000;

// Middleware to parse JSON bodies
app.use(express.json());

// Serve static files from 'public' folder
app.use(express.static(path.join(__dirname, "public")));

// In-memory data array (3-4 seed records)
let items = [
  { id: 1, name: "Paneer Butter Masala", price: 250, available: true },
  { id: 2, name: "Veg Biryani", price: 180, available: true },
  { id: 3, name: "Masala Dosa", price: 120, available: true },
  { id: 4, name: "Chole Bhature", price: 150, available: false },
];
let nextId = 5;

// 1. GET /items (List all items)
app.get("/items", (req, res) => {
  res.status(200).json(items);
});

// 2. GET /items/:id (Get one item by ID)
app.get("/items/:id", (req, res) => {
  const id = parseInt(req.params.id);
  const item = items.find((i) => i.id === id);

  if (!item) {
    return res.status(404).json({ error: "Item not found" });
  }

  res.status(200).json(item);
});

// 3. POST /items (Create a new item)
app.post("/items", (req, res) => {
  const { name, price } = req.body;

  // Validation: 422 if required field missing
  if (!name || !price) {
    return res.status(422).json({ error: "Name and price are required" });
  }

  const newItem = {
    id: nextId++,
    name,
    price,
    available: true, // Default value
  };

  items.push(newItem);
  res.status(201).json(newItem);
});

// Start the server
app.listen(PORT, () => {
  console.log(`REST API running at http://localhost:${PORT}`);
});
