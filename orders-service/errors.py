def problem(status_code, title, detail, type_url=None, errors=None):
    """
    Single error handler for all endpoints.
    Returns a tuple of (response_dict, status_code, headers).
    """
    response = {
        'type': type_url or f"https://campuseats.edu/errors/{title.lower().replace(' ', '-')}",
        'title': title,
        'status': status_code,
        'detail': detail
    }
    
    if errors:
        response['errors'] = errors
    
    headers = {
        'Content-Type': 'application/problem+json; charset=utf-8'
    }
    
    return response, status_code, headers


def validate_create_order(data):
    """
    Validation function - collects ALL errors, not just the first.
    Returns a list of error objects with field and message.
    """
    errors = []
    
    if not data:
        return [{"field": "body", "message": "Request body is empty"}]
    
    # Validate userId
    if not data.get('userId'):
        errors.append({"field": "userId", "message": "is required"})
    elif not isinstance(data['userId'], str):
        errors.append({"field": "userId", "message": "must be a string"})
    elif len(data['userId']) < 1:
        errors.append({"field": "userId", "message": "must not be empty"})
    
    # Validate vendorId
    if not data.get('vendorId'):
        errors.append({"field": "vendorId", "message": "is required"})
    elif not isinstance(data['vendorId'], str):
        errors.append({"field": "vendorId", "message": "must be a string"})
    
    # Validate items
    if not data.get('items'):
        errors.append({"field": "items", "message": "must be a non-empty array"})
    elif not isinstance(data['items'], list):
        errors.append({"field": "items", "message": "must be an array"})
    elif len(data['items']) == 0:
        errors.append({"field": "items", "message": "must contain at least one item"})
    else:
        for i, item in enumerate(data['items']):
            if not isinstance(item, dict):
                errors.append({"field": f"items[{i}]", "message": "must be an object"})
                continue
            
            if not item.get('itemId'):
                errors.append({"field": f"items[{i}].itemId", "message": "is required"})
            
            if item.get('quantity') is None:
                errors.append({"field": f"items[{i}].quantity", "message": "is required"})
            elif not isinstance(item['quantity'], int):
                errors.append({"field": f"items[{i}].quantity", "message": "must be an integer"})
            elif item['quantity'] < 1:
                errors.append({"field": f"items[{i}].quantity", "message": "must be >= 1"})
    
    # Validate deliveryAddress
    if not data.get('deliveryAddress'):
        errors.append({"field": "deliveryAddress", "message": "is required"})
    elif not isinstance(data['deliveryAddress'], dict):
        errors.append({"field": "deliveryAddress", "message": "must be an object"})
    elif not data['deliveryAddress'].get('building'):
        errors.append({"field": "deliveryAddress.building", "message": "is required"})
    
    return errors


def validate_cancel_order(data):
    """
    Validation for cancel order request.
    """
    errors = []
    
    if not data:
        return [{"field": "body", "message": "Request body is empty"}]
    
    if not data.get('reason'):
        errors.append({"field": "reason", "message": "is required"})
    elif data['reason'] not in ['USER_REQUEST', 'VENDOR_REQUEST', 
                                  'OUT_OF_STOCK', 'OTHER']:
        errors.append({
            "field": "reason", 
            "message": "must be one of: USER_REQUEST, VENDOR_REQUEST, OUT_OF_STOCK, OTHER"
        })
    
    return errors