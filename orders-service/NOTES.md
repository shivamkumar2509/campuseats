## A1. CampusEats Method Map

| Action | Method | URL | Success Code |
|--------|--------|-----|--------------|
| Create order | POST | /orders | 201 |
| List orders | GET | /orders?userId=&status= | 200 |
| Get order | GET | /orders/{orderId} | 200 |
| Update order | PATCH | /orders/{orderId} | 200 |
| Replace order | PUT | /orders/{orderId} | 200 |
| Delete order | DELETE | /orders/{orderId} | 204 |
| Cancel order | POST | /orders/{orderId}/cancellation | 202 |

---

## A2. Non-CRUD Actions

| Action | Why Non-CRUD | Resource Form |
|----------|-------------|--------------|
| Cancel Order | Not simple delete | POST /orders/{id}/cancellation |

---

## A3. Safe & Idempotent

| Endpoint | Safe? | Idempotent? |
|----------|-------|-------------|
| GET /orders | ✅ | ✅ |
| GET /orders/{id} | ✅ | ✅ |
| POST /orders | ❌ | ❌ |
| PUT /orders/{id} | ❌ | ✅ |
| PATCH /orders/{id} | ❌ | ❌ |
| DELETE /orders/{id} | ❌ | ✅ |
| POST /orders/{id}/cancellation | ❌ | ✅ |

---

## A4. Query Parameters

GET /orders?userId=123&status=PLACED

Query Parameters:

- userId → Filter orders by user
- status → Filter orders by order status

This uses GET because it only reads data and does not modify any resource.

---

## A5. OPTIONS & Allow Header

OPTIONS /orders

Allow: GET, POST, OPTIONS

OPTIONS /orders/{id}

Allow: GET, PUT, PATCH, DELETE, OPTIONS

OPTIONS helps clients discover which HTTP methods are supported by a resource.

---

## A6. Full HTTP Exchange

### Request

```http
POST /orders HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Authorization: Bearer abc123
Idempotency-Key: order-001

{
  "userId": "u123",
  "itemId": "burger01",
  "quantity": 2
}
```

### Response

```http
HTTP/1.1 201 Created
Location: /orders/ord123
Content-Type: application/json
ETag: "abc123def456"

{
  "orderId": "ord123",
  "status": "PLACED"
}
```

---

## B1. Content-Type & Content Negotiation

All request and response bodies use:

Content-Type: application/json

Supported Accept Header:

Accept: application/json

Example Unsupported Request:

Accept: application/xml

Response:

```http
HTTP/1.1 406 Not Acceptable
```

```json
{
  "error": "Only application/json is supported"
}
```

---

## B2. Correct Status + Location

| Scenario | Status Code | Reason |
|-----------|------------|---------|
| Create Order | 201 Created | New order created |
| Get Order | 200 OK | Resource found |
| Delete Order | 204 No Content | Deleted successfully |
| Invalid Input | 400 Bad Request | Client sent wrong data |
| Order Not Found | 404 Not Found | Resource does not exist |
| Update with stale ETag | 412 Precondition Failed | Version mismatch |

Location Header Example:

```http
HTTP/1.1 201 Created
Location: /orders/ord123
```

Location header tells the client where the newly created resource can be found.

---

---

## B3. Authorization

Protected endpoints require a Bearer Token in the Authorization header.

### Example Request

```http
GET /orders/ord123 HTTP/1.1
Host: api.campuseats.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### Unauthorized Request

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "error": "Authentication required"
}
```

### Forbidden Request

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "error": "Access denied"
}
```

---

## B4. Cache a Read

GET requests support caching using ETag and Cache-Control headers.

### Example Response

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: max-age=60
ETag: "abc123def456"

{
  "orderId": "ord123",
  "status": "PLACED"
}
```

### Benefits

- Reduces server load.
- Saves network bandwidth.
- Improves response time.
- Enables Conditional GET requests.

---

## B5. Rate Limit Signalling

The API returns rate limit information using response headers.

### Example Response

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 75
X-RateLimit-Reset: 3600
```

### Rate Limit Exceeded

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60

{
  "error": "Rate limit exceeded"
}
```

### Purpose

- Prevents API abuse.
- Protects server resources.
- Ensures fair usage.

---

## B6. CORS

Cross-Origin Resource Sharing (CORS) allows browser applications from other origins to access the API.

### Preflight Request

```http
OPTIONS /orders HTTP/1.1
Origin: https://app.campuseats.com
Access-Control-Request-Method: POST
```

### Preflight Response

```http
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://app.campuseats.com
Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization, Idempotency-Key
```

### Purpose

- Allows browser access from trusted origins.
- Improves security.
- Supports frontend-backend communication.

---

## B7. Security & General Headers

The API returns common security headers.

### Example Response

```http
HTTP/1.1 200 OK
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000
Content-Security-Policy: default-src 'self'
```

### Purpose

| Header | Purpose |
|----------|----------|
| X-Content-Type-Options | Prevents MIME type sniffing |
| Strict-Transport-Security | Forces HTTPS connections |
| Content-Security-Policy | Reduces XSS attacks |

---

---

## C1. Conditional GET → 304 Not Modified

The service supports conditional GET requests using ETag headers.

### First Request

```http
GET /orders/ord123 HTTP/1.1
Host: api.campuseats.com
```

### Response

```http
HTTP/1.1 200 OK
Content-Type: application/json
ETag: "abc123def456"

{
  "orderId": "ord123",
  "status": "PLACED"
}
```

### Conditional GET Request

```http
GET /orders/ord123 HTTP/1.1
If-None-Match: "abc123def456"
```

### Response

```http
HTTP/1.1 304 Not Modified
ETag: "abc123def456"
```

### Benefits

- Saves bandwidth.
- Reduces server workload.
- Improves client performance.
- Allows efficient caching.

---

## C2. Conditional Write → 412 Precondition Failed

The service prevents lost updates using ETag and If-Match headers.

### Update Request

```http
PATCH /orders/ord123 HTTP/1.1
If-Match: "old-etag-value"
Content-Type: application/json

{
  "status": "SHIPPED"
}
```

### Response

```http
HTTP/1.1 412 Precondition Failed

{
  "error": "Resource has been modified by another client"
}
```

### Benefits

- Prevents lost updates.
- Protects data consistency.
- Ensures updates are applied only to the latest version.

---

## C3. Idempotency Key

The service supports safe retries for POST requests using an Idempotency-Key.

### First Request

```http
POST /orders HTTP/1.1
Content-Type: application/json
Idempotency-Key: order-001

{
  "userId": "u123",
  "itemId": "burger01",
  "quantity": 2
}
```

### Response

```http
HTTP/1.1 201 Created
Location: /orders/ord123
```

### Retry Request

```http
POST /orders HTTP/1.1
Content-Type: application/json
Idempotency-Key: order-001

{
  "userId": "u123",
  "itemId": "burger01",
  "quantity": 2
}
```

### Response

```http
HTTP/1.1 200 OK
```

### Benefits

- Prevents duplicate order creation.
- Makes POST requests safely retryable.
- Handles network failures gracefully.
- Improves reliability.

---

## D2. Headers Table

| Endpoint | Method | Request Headers | Response Headers |
|----------|--------|-----------------|------------------|
| /orders | POST | Content-Type, Authorization, Idempotency-Key | Location, Content-Type, X-RateLimit-* |
| /orders | GET | Authorization | Content-Type |
| /orders/{id} | GET | Authorization, If-None-Match | ETag, Cache-Control |
| /orders/{id} | PATCH | Content-Type, Authorization, If-Match | ETag |
| /orders/{id} | DELETE | Authorization | - |
| /orders/{id}/cancellation | POST | Content-Type, Authorization, Idempotency-Key | Content-Type |

---

## C4. Safe-Retry Plan

| Endpoint | Mechanism | Why |
|----------|-----------|-----|
| POST /orders | Idempotency-Key | Prevents duplicate orders |
| GET /orders/{id} | If-None-Match | 304 caching |
| PATCH /orders/{id} | If-Match | Prevents lost updates |
| POST /orders/{id}/cancellation | Idempotency-Key | Prevents double refund |

---

## Answers to the Eight Questions

### Q1. For three of your endpoints, give the method, the success status, and the single response header that matters most - and why.

*A:*

| Endpoint | Method | Status | Header | Why |
|----------|--------|--------|--------|-----|
| POST /orders | POST | 201 | Location | Tells client where to find the new order |
| GET /orders/{id} | GET | 200 | ETag | Enables caching and conditional requests |
| DELETE /orders/{id} | DELETE | 204 | - | No body, no headers needed |

---

### Q2. Which of your endpoints are safe, and which are idempotent? Which one is neither, and how did you make it retry-safe?

*A:*

*Safe:* GET /orders, GET /orders/{id}

*Idempotent:* GET /orders, GET /orders/{id}, PUT /orders/{id}, DELETE /orders/{id}, POST /orders/{id}/cancellation

*Neither:* POST /orders (not safe, not idempotent)

*How made retry-safe:* Added Idempotency-Key header. Same key returns original result without creating duplicate order.

---

### Q3. Show one ETag from your service, the request that returns 304, and the write that returns 412. What does each save or prevent?

**A:**

**ETag:**

```http
ETag: "abc123def456"
```

**304 Request:**

```http
GET /api/orders/ord_abc123 HTTP/1.1
Authorization: Bearer abc123
If-None-Match: "abc123def456"
```

**304 Response:**

```http
HTTP/1.1 304 Not Modified
ETag: "abc123def456"
```

**What it saves:**

- Saves bandwidth because the response body is not sent again.
- Saves server processing and network usage.
- Allows the client to reuse its cached copy.

---

**412 Write Request:**

```http
PATCH /api/orders/ord_abc123 HTTP/1.1
Authorization: Bearer abc123
Content-Type: application/json
If-Match: "old-etag-value"

{
  "status": "SHIPPED"
}
```

**412 Response:**

```http
HTTP/1.1 412 Precondition Failed
```

**What it prevents:**

- Prevents lost updates.
- Prevents overwriting a newer version with stale data.
- Ensures updates are applied only to the latest resource version.

---

**Summary:**

- **ETag** identifies the current version of a resource.
- **304 Not Modified** saves bandwidth and improves caching efficiency.
- **412 Precondition Failed** prevents update conflicts and protects data consistency.

---

### Q4. You return 422 for one case and 400 for another. Give the exact request that triggers each and explain the difference.

**A:**

**400 Bad Request Example**

```http
POST /orders HTTP/1.1
Content-Type: application/json
Authorization: Bearer abc123

{
  "userId":
}
```

**Response**

```http
HTTP/1.1 400 Bad Request
```

**Reason:**
The request body is malformed JSON and cannot be parsed by the server.

---

**422 Unprocessable Entity Example**

```http
POST /orders HTTP/1.1
Content-Type: application/json
Authorization: Bearer abc123

{
  "userId": "u123",
  "itemId": "burger01",
  "quantity": -5
}
```

**Response**

```http
HTTP/1.1 422 Unprocessable Entity
```

**Reason:**
The JSON is syntactically correct, but the data violates business validation rules because quantity cannot be negative.

---

**Difference**

| Status | Meaning |
|----------|----------|
| 400 Bad Request | Request format is invalid and cannot be parsed correctly. |
| 422 Unprocessable Entity | Request format is valid, but the data fails validation rules. |

**Summary:**

- **400** = Invalid JSON / malformed request.
- **422** = Valid JSON but invalid business data.
---

### Q5. A browser page on another origin calls your API and is blocked — yet your server logs show a 200. Who blocked it, and which response header fixes it?

**A:**

The request was blocked by the **browser**, not by the server.

The server successfully processed the request and returned **200 OK**, but the browser enforced the **Same-Origin Policy (SOP)** and blocked access to the response because the required CORS headers were missing.

**Example Response Causing Block:**

```http
HTTP/1.1 200 OK
Content-Type: application/json
```

The browser receives the response but does not allow JavaScript to read it.

**Fix:**

Add the following response header:

```http
Access-Control-Allow-Origin: *
```

or

```http
Access-Control-Allow-Origin: https://example.com
```

**Explanation:**

- Server returns 200 OK.
- Browser checks CORS policy.
- Browser blocks the response if Access-Control-Allow-Origin is missing.
- Adding the header allows cross-origin access.

**Summary:**

The browser blocks the request due to CORS restrictions. The response header **Access-Control-Allow-Origin** fixes the issue.

---

### Q6. Name one response where Cache-Control to allow caching and one where you must use no-store. Why each?

**A:**

**Cacheable Response Example**

```http
GET /orders/ord123 HTTP/1.1
```

```http
HTTP/1.1 200 OK
Cache-Control: max-age=300
ETag: "abc123def456"
Content-Type: application/json
```

**Why cache it?**

- Order details do not change frequently.
- Reduces server load.
- Improves response time.
- Saves bandwidth.

---

**No-Store Response Example**

```http
POST /login HTTP/1.1
```

```http
HTTP/1.1 200 OK
Cache-Control: no-store
Content-Type: application/json
```

**Why use no-store?**

- Response may contain sensitive information.
- Prevents browsers and proxies from storing credentials or tokens.
- Improves security and privacy.

---

**Summary**

| Response | Cache-Control | Reason |
|-----------|--------------|---------|
| GET /orders/{id} | max-age=300 | Improves performance and reduces server load |
| POST /login | no-store | Protects sensitive authentication data |

---

### Q7. Show one example of a rate-limit response from your service. Which headers tell the client what happened?

**A:**

**Request:**

```http
GET /orders HTTP/1.1
Authorization: Bearer abc123
```

**Response:**

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
Retry-After: 60

{
  "error": "Rate limit exceeded"
}
```

**Headers that tell the client what happened:**

- **X-RateLimit-Limit** → Maximum requests allowed.
- **X-RateLimit-Remaining** → Requests remaining in the current window.
- **Retry-After** → Number of seconds the client should wait before retrying.

**Explanation:**

The server returns **429 Too Many Requests** when the client exceeds the allowed request limit. These headers help the client understand the limit and when it can send requests again.

---
### Q8. Why is an Idempotency-Key safer than retrying a POST blindly after a timeout?

**A:**

When a client sends a POST request, the server may successfully process it, but the response can be lost because of a network timeout.

If the client blindly retries the same POST request, the server may create the resource again, resulting in duplicate orders.

An **Idempotency-Key** uniquely identifies the request. When the same key is received again, the server recognizes it as a retry of an already processed request and returns the original result instead of creating a duplicate resource.

**Example:**

**First Request**

```http
POST /orders HTTP/1.1
Idempotency-Key: order-001

{
  "userId": "u123",
  "itemId": "burger01",
  "quantity": 2
}
```

**Response**

```http
HTTP/1.1 201 Created
```

Suppose the response is lost due to a timeout.

**Retry Request**

```http
POST /orders HTTP/1.1
Idempotency-Key: order-001

{
  "userId": "u123",
  "itemId": "burger01",
  "quantity": 2
}
```

**Server Behavior**

The server detects the same Idempotency-Key and returns the previous result instead of creating a second order.

**Benefits:**

- Prevents duplicate orders.
- Makes POST requests safely retryable.
- Handles network failures gracefully.
- Improves reliability of distributed systems.

**Summary:**

Idempotency-Key ensures that repeated retries of the same POST request produce only one logical result, preventing duplicate resource creation.

---