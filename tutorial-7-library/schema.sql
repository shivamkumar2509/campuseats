-- Database: gqldemo
CREATE DATABASE IF NOT EXISTS gqldemo;
USE gqldemo;

-- Table: authors
CREATE TABLE IF NOT EXISTS authors (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  country VARCHAR(50)
);

-- Table: books
CREATE TABLE IF NOT EXISTS books (
  id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  year INT,
  author_id INT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES authors(id)
);

-- Seed Rows
INSERT INTO authors (name, country) VALUES 
('Asha Patel', 'India'), 
('Ravi Kumar', 'India');

INSERT INTO books (title, year, author_id) VALUES 
('Databases 101', 2020, 1), 
('SQL in Practice', 2022, 1), 
('Web Services Basics', 2023, 2);