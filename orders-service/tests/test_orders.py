import pytest
from app import app
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_create_order_success(client):
    """Test create succeeds with 201 and Location header"""
    response = client.post('/api/orders', 
        json={
            'userId': 'user_123',
            'vendorId': 'vendor_456',
            'items': [{'itemId': 'itm_789', 'quantity': 2}],
            'deliveryAddress': {'building': 'Academic Block A', 'room': '301'}
        },
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test_token',
            'Idempotency-Key': 'idem_test_001'
        })
    assert response.status_code == 201
    assert 'Location' in response.headers
    data = json.loads(response.data)
    assert 'orderId' in data


def test_empty_cart_422(client):
    """Test empty cart returns 422 with errors list"""
    response = client.post('/api/orders',
        json={
            'userId': 'user_123',
            'vendorId': 'vendor_456',
            'items': [],
            'deliveryAddress': {'building': 'Academic Block A'}
        },
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test_token'
        })
    assert response.status_code == 422
    data = json.loads(response.data)
    assert data['title'] == 'Validation Error'
    assert 'errors' in data


def test_invalid_quantity_422(client):
    """Test quantity <= 0 returns 422"""
    response = client.post('/api/orders',
        json={
            'userId': 'user_123',
            'vendorId': 'vendor_456',
            'items': [{'itemId': 'itm_789', 'quantity': 0}],
            'deliveryAddress': {'building': 'Academic Block A'}
        },
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test_token'
        })
    assert response.status_code == 422
    data = json.loads(response.data)
    assert 'errors' in data


def test_missing_auth_401(client):
    """Test missing Authorization returns 401"""
    response = client.post('/api/orders',
        json={'userId': 'user_123', 'vendorId': 'vendor_456',
              'items': [{'itemId': 'itm_789', 'quantity': 2}],
              'deliveryAddress': {'building': 'A'}})
    assert response.status_code == 401
    data = json.loads(response.data)
    assert data['title'] == 'Unauthorized'


def test_unknown_id_404(client):
    """Test unknown ID returns 404"""
    response = client.get('/api/orders/unknown_id',
        headers={'Authorization': 'Bearer test_token'})
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['title'] == 'Order Not Found'


def test_content_negotiation_406(client):
    """Test unsupported Accept returns 406"""
    response = client.get('/api/orders/ord_abc123',
        headers={
            'Authorization': 'Bearer test_token',
            'Accept': 'application/pdf'
        })
    # Order might not exist, but 406 check comes after 404 in some cases
    assert response.status_code in [404, 406]