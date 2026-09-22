Never: `POST /cancelOrder`

---

## A3. Safe & Idempotent (Shivam Kumar)

| Endpoint                       | Method | Safe?  | Idempotent?                   | Notes                     |
| ------------------------------ | ------ | ------ | ----------------------------- | ------------------------- |
| /orders                        | GET    | ✅ Yes | ✅ Yes                        | Read-only                 |
| /orders/{orderId}              | GET    | ✅ Yes | ✅ Yes                        | Read-only                 |
| /orders                        | POST   | ❌ No  | ❌ No                         | Creates new order         |
| /orders/{orderId}              | PUT    | ❌ No  | ✅ Yes                        | Same data = same result   |
| /orders/{orderId}              | PATCH  | ❌ No  | ❌ No                         | Modify, repeat may differ |
| /orders/{orderId}              | DELETE | ❌ No  | ✅ Yes                        | First: 204, repeat: 404   |
| /orders/{orderId}/cancellation | POST   | ❌ No  | ✅ Yes (with Idempotency-Key) | Repeat returns original   |

**Key Points:**

- GET never changes state
- POST is not naturally retry-safe (needs idempotency key)
- PUT/DELETE are naturally idempotent

---

## A4. Reads Take Query Params (Aman Tripathi)

| Query Param | Example    | Purpose          |
| ----------- | ---------- | ---------------- |
| userId      | user_123   | Filter by user   |
| vendorId    | vendor_456 | Filter by vendor |
| status      | CONFIRMED  | Filter by status |
| limit       | 20         | Pagination       |
| offset      | 0          | Pagination       |

---

## A5. OPTIONS + Allow and Override (Aman Tripathi)

**OPTIONS Request:**

```http
OPTIONS /api/orders HTTP/1.1
Host: orders.campuseats.edu
```
