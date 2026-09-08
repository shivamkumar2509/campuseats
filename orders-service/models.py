import uuid


class Order:
    def __init__(self, customer_name, item_name, quantity, idempotency_key):
        self.id = str(uuid.uuid4())
        self.customer_name = customer_name
        self.item_name = item_name
        self.quantity = quantity
        self.status = "pending"

        # Internal data - not exposed in API response
        self.idempotency_key = idempotency_key

    def as_json(self):
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "item_name": self.item_name,
            "quantity": self.quantity,
            "status": self.status
        }