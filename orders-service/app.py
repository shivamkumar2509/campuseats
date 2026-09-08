from flask import Flask, request, jsonify
import os
from models import Order
from store import OrderStore
from errors import problem, validate_create_order, validate_cancel_order
from datetime import datetime
import requests
import uuid
import time
import random

app = Flask(__name__)
store = OrderStore()
PAYMENTS_SERVICE_URL = os.environ.get('PAYMENTS_SERVICE_URL', 'http://localhost:8081/api')

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    
    # Validate request body
    errors = validate_create_order(data)
    if errors:
        return problem(400, "Bad Request", ", ".join(errors))
    
    # Check idempotency
    idempotency_key = request.headers.get('Idempotency-Key')
    if idempotency_key and idempotency_key in store.idempotency_cache:
        return jsonify(store.idempotency_cache[idempotency_key].as_json()), 200
    
    # Create order
    order = Order(data)
    order.calculate_totals()
    
    # Call Payment Service with timeout and retry
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
    
    # Save order
    store.save(order)
    if idempotency_key:
        store.idempotency_cache[idempotency_key] = order
    
    return jsonify(order.as_json()), 201, {'Location': f'/api/orders/{order.order_id}'}

@app.route('/api/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    order = store.get(order_id)
    if not order:
        return problem(404, "Not Found", f"Order {order_id} not found")
    return jsonify(order.as_json()), 200

@app.route('/api/orders', methods=['GET'])
def list_orders():
    user_id = request.args.get('userId')
    status = request.args.get('status')
    orders = store.filter(user_id=user_id, status=status)
    return jsonify({
        'items': [order.as_json() for order in orders],
        'total': len(orders),
        'limit': 20,
        'offset': 0
    }), 200

@app.route('/api/orders/<order_id>/cancellation', methods=['POST'])
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

def call_payment_service(order):
    """Call the Payments service (Tutorial 4) with timeout and retry"""
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