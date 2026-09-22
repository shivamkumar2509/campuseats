class OrderStore:
    def __init__(self):
        self._orders = {}
        self.idempotency_cache = {}
    
    def save(self, order):
        self._orders[order.order_id] = order
    
    def get(self, order_id):
        return self._orders.get(order_id)
    
    def filter(self, user_id=None, status=None):
        result = list(self._orders.values())
        if user_id:
            result = [o for o in result if o.user_id == user_id]
        if status:
            result = [o for o in result if o.status == status]
        return result
    
    def delete(self, order_id):
        if order_id in self._orders:
            del self._orders[order_id]