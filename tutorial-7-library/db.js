const mysql = require("mysql2/promise");

const pool = mysql.createPool({
  host: "localhost",
  user: "root",
  password: "shivam25082003",
  database: "gqldemo",
});

module.exports = pool;
