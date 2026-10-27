-- Database: campuseats
CREATE DATABASE IF NOT EXISTS campuseats;
USE campuseats;

-- Table: dishes
CREATE TABLE IF NOT EXISTS dishes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  available BOOLEAN DEFAULT TRUE,
  restaurant_id INT NOT NULL
);

-- Seed Rows (3-4 rows)
INSERT INTO dishes (name, price, available, restaurant_id) VALUES
('Paneer Butter Masala', 250.00, TRUE, 1),
('Veg Biryani', 180.00, TRUE, 1),
('Masala Dosa', 120.00, TRUE, 2),
('Chole Bhature', 150.00, FALSE, 2);