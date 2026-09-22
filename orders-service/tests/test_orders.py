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
    assert data['status'] == 'CONFIRMED'


def test_idempotent_repeat(client):
    """Test idempotent repeat returns original"""
    key = 'idem_test_002'
    data = {
        'userId': 'user_123',
        'vendorId': 'vendor_456',
        'items': [{'itemId': 'itm_789', 'quantity': 2}],
        'deliveryAddress': {'building': 'Academic Block A', 'room': '301'}
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test_token',
        'Idempotency-Key': key
    }
    
    first = client.post('/api/orders', json=data, headers=headers)
    second = client.post('/api/orders', json=data, headers=headers)
    
    assert first.status_code == 201
    assert second.status_code == 200
    assert json.loads(first.data)['orderId'] == json.loads(second.data)['orderId']


def test_malformed_body_rejected(client):
    """Test malformed body returns 400"""
    response = client.post('/api/orders', 
        json={'userId': 'user_123'},
        headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test_token'
        })
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'title' in data
    assert data['title'] == 'Bad Request'


def test_unknown_id_404(client):
    """Test unknown ID returns 404"""
    response = client.get('/api/orders/unknown_id',
        headers={'Authorization': 'Bearer test_token'})
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['title'] == 'Not Found'