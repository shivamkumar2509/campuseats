# CampusEats Orders Service - Assignment 6

## Team Members

| Name | Roll No. | Contribution |
|------|----------|--------------|
| Shivam Kumar | 20251651083 | app.py (status codes, validation) |
| Aman Tripathi | 20251651018 | openapi.yaml (all statuses) |
| Aniket Kumar | 20251651019 | errors.py (problem details) |
| Raghav Soni | 20251651076 | tests, curl transcript |
| Nikhil Singh Tomar | 20251651065 | NOTES.md |

**Team ID:** Group_14

---

## A1. Status Code Map

| Method | Endpoint | Success | Failures |
|--------|----------|---------|----------|
| POST | /orders | 201 Created | 400, 401, 422, 429, 503 |
| GET | /orders | 200 OK | 400, 401 |
| GET | /orders/{id} | 200 OK | 401, 404, 406 |
| PATCH | /orders/{id} | 200 OK | 400, 401, 404, 409, 412 |
| DELETE | /orders/{id} | 204 No Content | 401, 404, 409 |
| POST | /orders/{id}/cancellation | 202 Accepted | 400, 401, 404, 409, 422 |

---

## A2. No 200 for Failure

All failures use proper HTTP status codes. The error shape is always `application/problem+json`, never a 200 with `{"ok": false}`.

**Wrong:**
```json
HTTP/1.1 200 OK
{
  "ok": false,
  "error": "Item not available"
}

---

## A3. Location Header on Create

`POST /orders` returns `201 Created` with:

**Example:**
```http
HTTP/1.1 201 Created
Location: /api/orders/ord_abc123
Content-Type: application/json; charset=utf-8

{
  "orderId": "ord_abc123",
  "status": "CONFIRMED",
  "grandTotal": 506.00
}

---

## A4. Retry-Safety

| Endpoint | Safe to Retry? | Mechanism |
|----------|----------------|-----------|
| GET /orders | ✅ Always | Naturally idempotent |
| GET /orders/{id} | ✅ Always | Naturally idempotent |
| POST /orders | ⚠️ Only with Idempotency-Key | Idempotency-Key |
| PATCH /orders/{id} | ⚠️ Only with If-Match | If-Match |
| DELETE /orders/{id} | ✅ Always | Naturally idempotent |
| POST /orders/{id}/cancellation | ⚠️ Only with Idempotency-Key | Idempotency-Key |

**Never retry 4xx (except 429):**
- 400, 401, 404, 409, 412, 422 → Don't retry
- 429, 503 → Retry with Retry-After

**Rate limit response includes:**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0

{
  "type": "https://campuseats.edu/errors/rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Too many requests. Please retry after 60 seconds."
}

**Content-Type:** `application/problem+json; charset=utf-8`

---

## B1. Problem Details

Every failure goes through `problem()` helper and returns:
```json
{
  "type": "https://campuseats.edu/errors/order-not-found",
  "title": "Order Not Found",
  "status": 404,
  "detail": "Order ord_abc123 not found"
}

---

## B2. Type Catalogue

| Type | When It Occurs |
|------|----------------|
| `https://campuseats.edu/errors/empty-cart` | Order has no items |
| `https://campuseats.edu/errors/item-unavailable` | Item out of stock |
| `https://campuseats.edu/errors/payment-declined` | Payment failed |
| `https://campuseats.edu/errors/order-not-found` | Order ID doesn't exist |
| `https://campuseats.edu/errors/illegal-transition` | Invalid state change |
| `https://campuseats.edu/errors/validation-error` | Field validation failed |
| `https://campuseats.edu/errors/rate-limit-exceeded` | Too many requests |
| `https://campuseats.edu/errors/precondition-failed` | ETag mismatch |
| `https://campuseats.edu/errors/unauthorized` | Missing/invalid token |
| `https://campuseats.edu/errors/not-acceptable` | Unsupported Accept |
| `https://campuseats.edu/errors/internal-error` | Unexpected error |

---

## B3. Field-Level Validation Errors

422 response includes `errors[]` array:
```json
{
  "type": "https://campuseats.edu/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "Request body failed validation",
  "errors": [
    {"field": "items", "message": "must be a non-empty array"},
    {"field": "items[0].quantity", "message": "must be >= 1"},
    {"field": "deliveryAddress.building", "message": "is required"}
  ]
}

---

## B4. Don't Leak Internals

All risky work is wrapped in try/catch. Internal errors are logged server-side but mapped to clean `internal-error` responses.

**Wrong:**
```json
HTTP/1.1 500 Internal Server Error
{
  "error": "Traceback (most recent call last):\n  File \"app.py\", line 45..."
}

HTTP/1.1 500 Internal Server Error
Content-Type: application/problem+json

{
  "type": "https://campuseats.edu/errors/internal-error",
  "title": "Internal Server Error",
  "status": 500,
  "detail": "An unexpected error occurred. Please try again later."
}

---

## C1. Request Body Schema

`POST /orders` body requirements:
- `items` must be non-empty array
- Each `quantity` must be an integer ≥ 1
- `deliveryAddress.building` is required

**JSON Schema:**
```yaml
CreateOrderRequest:
  type: object
  required: [userId, vendorId, items, deliveryAddress]
  properties:
    userId:
      type: string
      minLength: 1
    vendorId:
      type: string
      minLength: 1
    items:
      type: array
      minItems: 1
      items:
        type: object
        required: [itemId, quantity]
        properties:
          itemId:
            type: string
            minLength: 1
          quantity:
            type: integer
            minimum: 1
    deliveryAddress:
      type: object
      required: [building]
      properties:
        building:
          type: string
          minLength: 1

          ---

## C2. Validate, Then Act

Validation happens **before** any work. All errors are collected (not just first) and returned in a single 422 response.

---

## C3. Content Negotiation

- `Accept: application/json` → JSON response (default)
- `Accept: application/xml` → XML response
- `Accept: application/pdf` → 406 Not Acceptable

---

## C4. Content-Type on Every Response

| Response | Content-Type |
|----------|--------------|
| JSON success | `application/json; charset=utf-8` |
| JSON error | `application/problem+json; charset=utf-8` |
| XML success | `application/xml; charset=utf-8` |

---

## D1. Success Transcript

```bash
curl -i -X POST http://localhost:8080/api/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test_token" \
  -H "Idempotency-Key: idem_abc123" \
  -d '{"userId":"user_123","vendorId":"vendor_456","items":[{"itemId":"itm_789","quantity":2}],"deliveryAddress":{"building":"Academic Block A","room":"301"}}'

  HTTP/1.1 201 CREATED
Location: /api/orders/ord_abc123
Content-Type: application/json; charset=utf-8

{
  "orderId": "ord_abc123",
  "status": "CONFIRMED",
  "grandTotal": 506.00
}
curl -i -X POST http://localhost:8080/api/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test_token" \
  -d '{"userId":"user_123","vendorId":"vendor_456","items":[],"deliveryAddress":{"building":"A"}}'

  HTTP/1.1 422 UNPROCESSABLE ENTITY
Content-Type: application/problem+json; charset=utf-8

{
  "type": "https://campuseats.edu/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "Request body failed validation",
  "errors": [
    {"field": "items", "message": "must contain at least one item"}
  ]
}

**2. Quantity ≤ 0 (422):**
```bash
curl -i -X POST http://localhost:8080/api/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test_token" \
  -d '{"userId":"user_123","vendorId":"vendor_456","items":[{"itemId":"itm_789","quantity":0}],"deliveryAddress":{"building":"A"}}'

  HTTP/1.1 422 UNPROCESSABLE ENTITY
Content-Type: application/problem+json; charset=utf-8

{
  "type": "https://campuseats.edu/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "Request body failed validation",
  "errors": [
    {"field": "items[0].quantity", "message": "must be >= 1"}
  ]
}
curl -i http://localhost:8080/api/orders/unknown_id \
  -H "Authorization: Bearer test_token"

  HTTP/1.1 404 NOT FOUND
Content-Type: application/problem+json; charset=utf-8

{
  "type": "https://campuseats.edu/errors/order-not-found",
  "title": "Order Not Found",
  "status": 404,
  "detail": "Order unknown_id not found"
}
curl -i -X POST http://localhost:8080/api/orders/ord_delivered/cancellation \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test_token" \
  -d '{"reason":"USER_REQUEST"}'

  HTTP/1.1 409 CONFLICT
Content-Type: application/problem+json; charset=utf-8

{
  "type": "https://campuseats.edu/errors/illegal-transition",
  "title": "Illegal Transition",
  "status": 409,
  "detail": "Order cannot be cancelled (status: DELIVERED)"
}
curl -i http://localhost:8080/api/orders \
  -H "Authorization: Bearer test_token"

  HTTP/1.1 429 TOO MANY REQUESTS
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
Content-Type: application/problem+json; charset=utf-8

{
  "type": "https://campuseats.edu/errors/rate-limit-exceeded",
  "title": "Rate Limit Exceeded",
  "status": 429,
  "detail": "Too many requests. Please retry after 60 seconds."
}
---

## D3. Negotiation Check

```bash
curl -i http://localhost:8080/api/orders/ord_abc123 \
  -H "Authorization: Bearer test_token" \
  -H "Accept: application/xml"
  HTTP/1.1 200 OK
Content-Type: application/xml; charset=utf-8

<?xml version="1.0" encoding="UTF-8"?>
<order>
    <orderId>ord_abc123</orderId>
    <status>CONFIRMED</status>
    <grandTotal>506.0</grandTotal>
</order>
curl -i http://localhost:8080/api/orders/ord_abc123 \
  -H "Authorization: Bearer test_token" \
  -H "Accept: application/pdf"
  HTTP/1.1 406 NOT ACCEPTABLE
Content-Type: application/problem+json; charset=utf-8

{
  "type": "https://campuseats.edu/errors/not-acceptable",
  "title": "Not Acceptable",
  "status": 406,
  "detail": "Content type 'application/pdf' not supported"
}
---

## Answers to Assignment Questions

### Q1. Which responses were returning 200 for failures, and how did you fix them?

**A:** We ensured no endpoint returns 200 for a failure. All failures return proper 4xx/5xx status codes:
- Validation failures → 422
- Not found → 404
- Conflict → 409
- Unauthorized → 401
- Rate limit → 429
- Service unavailable → 503

The status code **is** the result. Never a 200 with `{"ok": false}`.

---

### Q2. Which endpoints are safe to retry, and which need special headers?

**A:**

| Endpoint | Retry Safety |
|----------|--------------|
| GET endpoints | ✅ Always safe |
| DELETE | ✅ Always safe |
| POST /orders | ⚠️ Needs Idempotency-Key |
| PATCH /orders/{id} | ⚠️ Needs If-Match |
| POST /orders/{id}/cancellation | ⚠️ Needs Idempotency-Key |

Never retry 4xx (except 429). Always retry 429/503 with Retry-After.

---

### Q3. What does 422 vs 400 mean in your service?

**A:**

| Status | Meaning | Example |
|--------|---------|---------|
| **400 Bad Request** | Malformed syntax (can't parse) | Invalid JSON |
| **422 Unprocessable Entity** | Valid syntax but domain refusal | `quantity: 0`, empty cart |

400 = parsing failed.
422 = parsing OK, business rule violated.

---

### Q4. How do you prevent internal details from leaking?

**A:** All risky work is wrapped in try/catch. Internal errors are logged server-side via `app.logger.error()` but mapped to a generic `internal-error` response. Stack traces and DB messages never go to clients.

---

### Q5. Which type strings are stable in your catalogue?

**A:** All type strings are documented in section B2. They are stable URIs like `https://campuseats.edu/errors/order-not-found`. The same type is returned for the same class of failure, making client handling predictable.