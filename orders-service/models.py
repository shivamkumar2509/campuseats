import uuid
from datetime import datetime

class Order:
    def __init__(self, data):
        self.order_id = str(uuid.uuid4())
        self.user_id = data['userId']
        self.vendor_id = data['vendorId']
        self.items = data['items']
        self.delivery_address = data['deliveryAddress']
        self.status = 'PENDING'
        self.subtotal = 0.0
        self.tax = 0.0
        self.delivery_fee = 20.0
        self.grand_total = 0.0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        # Internal fields - NEVER exposed to API responses
        self._internal_notes = []
        self._payment_retry_count = 0
    
    def calculate_totals(self):
        # Simplified price calculation
        self.subtotal = sum(item['quantity'] * 299.50 for item in self.items)
        self.tax = self.subtotal * 0.08
        self.grand_total = self.subtotal + self.tax + self.delivery_fee
    
    def as_json(self):
        """Public representation - excludes internal fields"""
        return {
            'orderId': self.order_id,
            'userId': self.user_id,
            'vendorId': self.vendor_id,
            'status': self.status,
            'items': self.items,
            'deliveryAddress': self.delivery_address,
            'subtotal': round(self.subtotal, 2),
            'tax': round(self.tax, 2),
            'deliveryFee': round(self.delivery_fee, 2),
            'grandTotal': round(self.grand_total, 2),
            'createdAt': self.created_at.isoformat(),
            'updatedAt': self.updated_at.isoformat()
        }