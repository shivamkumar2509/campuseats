# CampusEats - GraphQL Orders Service

## Team Members

| Name               | Roll No.    |
| ------------------ | ----------- |
| Shivam Kumar       | 20251651083 |
| Aman Tripathi      | 20251651018 |
| Aniket Kumar       | 20251651019 |
| Raghav Soni        | 20251651076 |
| Nikhil Singh Tomar | 20251651065 |

**Team ID:** Group_14

---

## How to Run

### Prerequisites

- Node.js (v16 or higher)
- MySQL (v8 or higher) or XAMPP

### Setup Steps

1. **Clone the repository:**

   ```bash
   git clone https://github.com/shivamkumar2509/campuseats.git
   cd campuseats/graphql-orders-service


   1. Which CampusEats service did you pick?
   A: We picked the Orders Service (Dishes entity). The Dish entity is the core part of the menu. We modeled it with fields: id, name, price, available, and restaurantId. This helps the frontend fetch the menu dynamically and allows vendors to add new items to the menu using a mutation.

   ```

2. Name one field a client can skip and one it cannot (why we use the "!" sign).
   A:

Cannot skip: id, name, price, available — These are marked with ! (non-nullable) in the schema. A client must receive these fields and they will never return null. The ! sign enforces strict data integrity.

Can skip: The client can skip requesting restaurantId in their query if they don't need it.
Example query where restaurantId is skipped:
query {
dishes {
id
name
price
}
}

GraphQL allows the client to ask for exactly what they need, reducing over-fetching.

3. Map it to SQL/other database: which part of your query became the WHERE, and which resolver ran the INSERT?
   A:

WHERE clause: The GraphQL query dish(id: ID!) maps to the SQL query SELECT \* FROM dishes WHERE id = ?. The id argument provided by the client becomes the WHERE clause. This is executed by the Query.dish resolver.

INSERT clause: The GraphQL mutation addDish(input: AddDishInput!) maps to the SQL query INSERT INTO dishes (name, price, available, restaurant_id) VALUES (?, ?, ?, ?). This is executed by the Mutation.addDish resolver.
