# Assignment 4 Notes

## A4 Resource Table

| Resource | Description |
|----------|-------------|
| /orders | Create and list orders |
| /orders/{id} | Retrieve order details |
| /orders/{id}/cancellation | Cancel an existing order |

---

## A5 Justification

The REST API design uses resource-oriented endpoints. Each resource is identified through a URI and manipulated using standard HTTP methods such as GET and POST.

---

## D3 Fallback Reasoning

If the external payment service becomes unavailable, the service will fail fast and return an error response. This prevents invalid orders from being created without successful payment verification.

---

## Question 1

The WSDL file contained SOAP-specific definitions such as bindings, messages, and service descriptions. The OpenAPI file focuses on REST endpoints, request bodies, and response schemas.

---

## Question 2

SOAP faults were replaced by HTTP status codes and problem response bodies. Returning an error inside HTTP 200 OK can confuse clients and network intermediaries because the request appears successful.

---

## Question 3

The publish, find, and bind concepts still exist in REST. APIs are published through deployment, found through documentation, and bound through HTTP requests.

---

## Question 4

Earlier validation was enforced through XML Schema. In the REST implementation validation is performed using the validate_order() function before processing incoming data.

---

## Question 5

One guarantee lost when moving from SOAP to REST is strict XML Schema enforcement. REST relies more on application-level validation.