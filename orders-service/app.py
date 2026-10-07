from flask import Flask, request, jsonify, Response
import os
from models import Order
from store import OrderStore
from errors import problem, validate_create_order, validate_cancel_order
from datetime import datetime
import requests
import time
import random
import json

app = Flask(__name__)
store = OrderStore()
PAYMENTS_SERVICE_URL = os.environ.get('PAYMENTS_SERVICE_URL', 'http://localhost:8081/api')

# ============================================================
# RATE LIMITING (A4)
# ============================================================
rate_limit_store = {}

def check_rate_limit(user_id):
    """Check rate limit - 100 requests per minute per user"""
    now = time.time()
    window = now - 60
    
    if user_id not in rate_limit_store:
        rate_limit_store[user_id] = []
    
    # Remove old requests
    rate_limit_store[user_id] = [t for t in rate_limit_store[user_id] if t > window]
    
    if len(rate_limit_store[user_id]) >= 100:
        return False, 0
    
    rate_limit_store[user_id].append(now)
    return True, 100 - len(rate_limit_store[user_id])


# ============================================================
# POST /orders - Create Order
# ============================================================
@app.route('/api/orders', methods=['POST'])
def create_order():
    # Get auth token
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return problem(401, "Unauthorized", "Missing or invalid token")
    
    # Rate limit check
    allowed, remaining = check_rate_limit('user_123')
    if not allowed:
        response, status, headers = problem(429, "Rate Limit Exceeded", 
            "Too many requests. Please retry after 60 seconds.")
        headers['Retry-After'] = '60'
        headers['X-RateLimit-Limit'] = '100'
        headers['X-RateLimit-Remaining'] = '0'
        return response, status, headers
    
    # Validate request body
    data = request.get_json()
    errors = validate_create_order(data)
    if errors:
        return problem(422, "Validation Error", 
            "Request body failed validation", errors=errors)
    
    # Check idempotency
    idempotency_key = request.headers.get('Idempotency-Key')
    if idempotency_key and idempotency_key in store.idempotency_cache:
        return jsonify(store.idempotency_cache[idempotency_key].as_json()), 200
    
    # Create order
    order = Order(data)
    order.calculate_totals()
    
    # Call Payment Service
    try:
        payment_response = call_payment_service(order)
        if payment_response.status_code != 200:
            return problem(402, "Payment Declined", 
                "Payment service declined the transaction")
    except requests.exceptions.Timeout:
        return problem(503, "Service Unavailable", 
            "Payment service timed out")
    except requests.exceptions.ConnectionError:
        return problem(503, "Service Unavailable", 
            "Payment service unreachable")
    
    # Save order
    store.save(order)
    if idempotency_key:
        store.idempotency_cache[idempotency_key] = order
    
    # Success response with Location header (A3)
    response = jsonify(order.as_json())
    response.headers['Location'] = f'/api/orders/{order.order_id}'
    response.headers['X-RateLimit-Limit'] = '100'
    response.headers['X-RateLimit-Remaining'] = str(remaining)
    return response, 201


# ============================================================
# GET /orders - List Orders
# ============================================================
@app.route('/api/orders', methods=['GET'])
def list_orders():
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return problem(401, "Unauthorized", "Missing or invalid token")
    
    user_id = request.args.get('userId')
    status = request.args.get('status')
    
    # Validate filter params
    if status and status not in ['PENDING', 'CONFIRMED', 'PREPARING', 
                                   'READY', 'DELIVERED', 'CANCELLED']:
        return problem(400, "Bad Request", 
            f"Invalid status filter: {status}")
    
    orders = store.filter(user_id=user_id, status=status)
    return jsonify({
        'items': [order.as_json() for order in orders],
        'total': len(orders),
        'limit': 20,
        'offset': 0
    }), 200


# ============================================================
# GET /orders/{id} - Get Single Order (with content negotiation)
# ============================================================
@app.route('/api/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return problem(401, "Unauthorized", "Missing or invalid token")
    
    order = store.get(order_id)
    if not order:
        return problem(404, "Order Not Found", f"Order {order_id} not found")
    
    # Content negotiation (C3)
    accept = request.headers.get('Accept', 'application/json')
    
    if 'application/xml' in accept:
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<order>
    <orderId>{order.order_id}</orderId>
    <userId>{order.user_id}</userId>
    <vendorId>{order.vendor_id}</vendorId>
    <status>{order.status}</status>
    <grandTotal>{order.grand_total}</grandTotal>
    <createdAt>{order.created_at.isoformat()}</createdAt>
</order>"""
        return Response(xml, status=200, 
            content_type='application/xml; charset=utf-8')
    
    elif 'application/json' in accept or '*/*' in accept or not accept:
        return jsonify(order.as_json()), 200
    
    else:
        return problem(406, "Not Acceptable", 
            f"Content type '{accept}' not supported")


# ============================================================
# PATCH /orders/{id} - Update Order (with If-Match)
# ============================================================
@app.route('/api/orders/<order_id>', methods=['PATCH'])
def update_order(order_id):
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return problem(401, "Unauthorized", "Missing or invalid token")
    
    order = store.get(order_id)
    if not order:
        return problem(404, "Order Not Found", f"Order {order_id} not found")
    
    # Check If-Match (C2)
    if_match = request.headers.get('If-Match')
    current_etag = f'"{hash(order.updated_at.isoformat())}"'
    
    if if_match and if_match != current_etag:
        return problem(412, "Precondition Failed", 
            "The resource has been modified by another user.")
    
    data = request.get_json()
    if not data or 'status' not in data:
        return problem(400, "Bad Request", "Missing 'status' field")
    
    new_status = data['status']
    if new_status not in ['PENDING', 'CONFIRMED', 'PREPARING', 
                          'READY', 'DELIVERED', 'CANCELLED']:
        return problem(400, "Bad Request", f"Invalid status: {new_status}")
    
    # Check illegal transitions (B2)
    if order.status == 'DELIVERED' and new_status != 'DELIVERED':
        return problem(409, "Illegal Transition", 
            f"Cannot change status from DELIVERED to {new_status}")
    
    order.status = new_status
    order.updated_at = datetime.now()
    store.save(order)
    
    return jsonify(order.as_json()), 200


# ============================================================
# DELETE /orders/{id} - Delete Order
# ============================================================
@app.route('/api/orders/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return problem(401, "Unauthorized", "Missing or invalid token")
    
    order = store.get(order_id)
    if not order:
        return problem(404, "Order Not Found", f"Order {order_id} not found")
    
    if order.status == 'DELIVERED':
        return problem(409, "Conflict", 
            "Cannot delete a delivered order")
    
    store.delete(order_id)
    return '', 204


# ============================================================
# OPTIONS - Allow Header (A5 from Assignment 5)
# ============================================================
@app.route('/api/orders/<order_id>', methods=['OPTIONS'])
def options_order(order_id):
    response = app.make_default_options_response()
    response.headers['Allow'] = 'GET, PATCH, DELETE, OPTIONS'
    return response


# ============================================================
# POST /orders/{id}/cancellation - Cancel Order
# ============================================================
@app.route('/api/orders/<order_id>/cancellation', methods=['POST'])
def cancel_order(order_id):
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        return problem(401, "Unauthorized", "Missing or invalid token")
    
    data = request.get_json()
    errors = validate_cancel_order(data)
    if errors:
        return problem(422, "Validation Error", 
            "Request body failed validation", errors=errors)
    
    order = store.get(order_id)
    if not order:
        return problem(404, "Order Not Found", f"Order {order_id} not found")
    
    # Illegal transitions
    if order.status in ['DELIVERED', 'CANCELLED']:
        return problem(409, "Illegal Transition", 
            f"Order cannot be cancelled (status: {order.status})")
    
    order.status = 'CANCELLED'
    order.updated_at = datetime.now()
    store.save(order)
    
    return jsonify({
        'orderId': order.order_id,
        'status': 'CANCELLED',
        'refundAmount': order.grand_total,
        'cancelledAt': order.updated_at.isoformat()
    }), 202


# ============================================================
# Helper - Call Payment Service with retry
# ============================================================
def call_payment_service(order):
    retries = 3
    backoff = 0.5
    
    for attempt in range(retries):
        try:
            response = requests.post(
                f"{PAYMENTS_SERVICE_URL}/payments",
                json={
                    'orderId': order.order_id,
                    'amount': order.grand_total,
                    'paymentMethod': 'CARD',
                    'token': 'tok_student_9f2c4a8b'
                },
                timeout=5.0,
                headers={'Idempotency-Key': f'pay_{order.order_id}'}
            )
            return response
        except (requests.exceptions.Timeout, 
                requests.exceptions.ConnectionError):
            if attempt == retries - 1:
                raise
            sleep_time = backoff * (2 ** attempt) + random.uniform(0, 0.1)
            time.sleep(sleep_time)


if __name__ == '__main__':
    app.run(port=8080, debug=True)