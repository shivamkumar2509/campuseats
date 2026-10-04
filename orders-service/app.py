from flask import Flask, request, jsonify
import os
from models import Order
from store import OrderStore
from errors import problem, validate_create_order, validate_cancel_order
from datetime import datetime, timedelta
import uuid
import time
import random
from functools import wraps
from collections import defaultdict
import requests

app = Flask(__name__)
store = OrderStore()
PAYMENTS_SERVICE_URL = os.environ.get('PAYMENTS_SERVICE_URL', 'http://localhost:8081/api')

rate_limit_store = defaultdict(list)


@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Idempotency-Key, If-None-Match, If-Match'
    return response


def check_rate_limit(user_id):
    now = datetime.now()
    window = now - timedelta(minutes=1)
    rate_limit_store[user_id] = [
        t for t in rate_limit_store[user_id] if t > window
    ]
    if len(rate_limit_store[user_id]) >= 100:
        return False, 0
    rate_limit_store[user_id].append(now)
    return True, 100 - len(rate_limit_store[user_id])


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization')
        if not auth or not auth.startswith('Bearer '):
            return problem(401, "Unauthorized", "Missing or invalid token")
        token = auth.split(' ')[1]
        if not token:
            return problem(401, "Unauthorized", "Empty token")
        return f(*args, **kwargs)
    return decorated


@app.route('/api/orders', methods=['OPTIONS'])
def options_orders():
    response = app.make_default_options_response()
    response.headers['Allow'] = 'GET, POST, OPTIONS'
    return response


@app.route('/api/orders', methods=['POST'])
@require_auth
def create_order():
    user_id = request.headers.get('X-User-Id', 'anonymous')
    allowed, remaining = check_rate_limit(user_id)
    if not allowed:
        response = problem(429, "Too Many Requests", "Rate limit exceeded")
        response[0].headers['Retry-After'] = '60'
        return response

    data = request.get_json()

    errors = validate_create_order(data)
    if errors:
        return problem(400, "Bad Request", ", ".join(errors))

    idempotency_key = request.headers.get('Idempotency-Key')
    if idempotency_key and idempotency_key in store.idempotency_cache:
        return jsonify(store.idempotency_cache[idempotency_key].as_json()), 200

    order = Order(data)
    order.calculate_totals()

    try:
        payment_response = call_payment_service(order)
        if payment_response.status_code != 200:
            return problem(402, "Payment Failed", "Payment service declined the transaction")
    except requests.exceptions.Timeout:
        return problem(503, "Service Unavailable", "Payment service timed out")
    except requests.exceptions.ConnectionError:
        return problem(503, "Service Unavailable", "Payment service unreachable")
    except Exception as e:
        return problem(503, "Service Unavailable", f"Payment service error: {str(e)}")

    store.save(order)
    if idempotency_key:
        store.idempotency_cache[idempotency_key] = order

    response = jsonify(order.as_json())
    response.headers['Location'] = f'/api/orders/{order.order_id}'
    response.headers['X-RateLimit-Limit'] = '100'
    response.headers['X-RateLimit-Remaining'] = str(remaining)
    response.headers['Cache-Control'] = 'no-store'
    return response, 201


@app.route('/api/orders/<order_id>', methods=['GET'])
@require_auth
def get_order(order_id):
    order = store.get(order_id)
    if not order:
        return problem(404, "Not Found", f"Order {order_id} not found")

    etag = f'"{hash(order.updated_at.isoformat())}"'

    if request.headers.get('If-None-Match') == etag:
        return '', 304

    response = jsonify(order.as_json())
    response.headers['ETag'] = etag
    response.headers['Cache-Control'] = 'max-age=3600, must-revalidate'
    return response, 200


@app.route('/api/orders', methods=['GET'])
@require_auth
def list_orders():
    user_id = request.args.get('userId')
    status = request.args.get('status')
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    orders = store.filter(user_id=user_id, status=status)
    paginated = orders[offset:offset+limit]

    return jsonify({
        'items': [order.as_json() for order in paginated],
        'total': len(orders),
        'limit': limit,
        'offset': offset
    }), 200


@app.route('/api/orders/<order_id>/cancellation', methods=['POST'])
@require_auth
def cancel_order(order_id):
    data = request.get_json()
    errors = validate_cancel_order(data)
    if errors:
        return problem(400, "Bad Request", ", ".join(errors))

    order = store.get(order_id)
    if not order:
        return problem(404, "Not Found", f"Order {order_id} not found")

    if order.status in ['DELIVERED', 'CANCELLED']:
        return problem(409, "Conflict", f"Order cannot be cancelled (status: {order.status})")

    order.status = 'CANCELLED'
    order.updated_at = datetime.now()
    store.save(order)

    return jsonify({
        'orderId': order.order_id,
        'status': 'CANCELLED',
        'refundAmount': order.grand_total,
        'cancelledAt': order.updated_at.isoformat()
    }), 202


@app.route('/api/orders/<order_id>', methods=['PATCH'])
@require_auth
def update_order(order_id):
    order = store.get(order_id)
    if not order:
        return problem(404, "Not Found", f"Order {order_id} not found")

    if_match = request.headers.get('If-Match')
    current_etag = f'"{hash(order.updated_at.isoformat())}"'

    if if_match and if_match != current_etag:
        return problem(412, "Precondition Failed", "The resource has been modified by another user")

    data = request.get_json()
    if 'status' in data:
        order.status = data['status']
    order.updated_at = datetime.now()
    store.save(order)

    response = jsonify(order.as_json())
    response.headers['ETag'] = f'"{hash(order.updated_at.isoformat())}"'
    return response, 200


@app.route('/api/orders/<order_id>', methods=['DELETE'])
@require_auth
def delete_order(order_id):
    order = store.get(order_id)
    if not order:
        return problem(404, "Not Found", f"Order {order_id} not found")

    store.delete(order_id)
    return '', 204


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
        except requests.exceptions.Timeout:
            if attempt == retries - 1:
                raise
            sleep_time = backoff * (2 ** attempt) + random.uniform(0, 0.1)
            time.sleep(sleep_time)
        except requests.exceptions.ConnectionError:
            if attempt == retries - 1:
                raise
            sleep_time = backoff * (2 ** attempt) + random.uniform(0, 0.1)
            time.sleep(sleep_time)


if __name__ == '__main__':
    app.run(port=8080, debug=True) 