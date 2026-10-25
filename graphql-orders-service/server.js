const { ApolloServer } = require("apollo-server");
const fs = require("fs");
const path = require("path");
const pool = require("./db");

// Read schema
const typeDefs = fs.readFileSync(
  path.join(__dirname, "schema.graphql"),
  "utf8",
);

// Resolvers
const resolvers = {
  Query: {
    dishes: async () => {
      const [rows] = await pool.query("SELECT * FROM dishes");
      return rows.map((row) => ({
        id: row.id,
        name: row.name,
        price: row.price,
        available: Boolean(row.available),
        restaurantId: row.restaurant_id,
      }));
    },
    dish: async (_, { id }) => {
      const [rows] = await pool.query("SELECT * FROM dishes WHERE id = ?", [
        id,
      ]);
      if (rows.length === 0) return null;
      const row = rows[0];
      return {
        id: row.id,
        name: row.name,
        price: row.price,
        available: Boolean(row.available),
        restaurantId: row.restaurant_id,
      };
    },
  },
  Mutation: {
    addDish: async (_, { input }) => {
      const { name, price, available = true, restaurantId } = input;
      const [result] = await pool.query(
        "INSERT INTO dishes (name, price, available, restaurant_id) VALUES (?, ?, ?, ?)",
        [name, price, available, restaurantId],
      );
      return {
        id: result.insertId,
        name,
        price,
        available,
        restaurantId,
      };
    },
    updateDish: async (_, { input }) => {
      const { id, name, price, available } = input;
      const updates = [];
      const values = [];
      if (name !== undefined) {
        updates.push("name = ?");
        values.push(name);
      }
      if (price !== undefined) {
        updates.push("price = ?");
        values.push(price);
      }
      if (available !== undefined) {
        updates.push("available = ?");
        values.push(available);
      }

      if (updates.length > 0) {
        values.push(id);
        await pool.query(
          `UPDATE dishes SET ${updates.join(", ")} WHERE id = ?`,
          values,
        );
      }

      const [rows] = await pool.query("SELECT * FROM dishes WHERE id = ?", [
        id,
      ]);
      if (rows.length === 0) return null;
      const row = rows[0];
      return {
        id: row.id,
        name: row.name,
        price: row.price,
        available: Boolean(row.available),
        restaurantId: row.restaurant_id,
      };
    },
  },
};

const server = new ApolloServer({ typeDefs, resolvers });

server.listen({ port: 4000 }).then(({ url }) => {
  console.log(`🚀 Server ready at ${url}`);
});
