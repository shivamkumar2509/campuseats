def problem(status_code, title, detail, type_url=None):
    """Single error handler for all endpoints"""
    return {
        'type': type_url or f"https://campuseats.edu/errors/{title.lower().replace(' ', '-')}",
        'title': title,
        'status': status_code,
        'detail': detail
    }, status_code


def validate_create_order(data):
    """Validation function - does the job of XML Schema"""
    errors = []

    if not data:
        errors.append("Request body is empty")
        return errors

    if not data.get('userId'):
        errors.append("'userId' is required and must be a string")
    elif not isinstance(data['userId'], str):
        errors.append("'userId' must be a string")

    if not data.get('vendorId'):
        errors.append("'vendorId' is required and must be a string")
    elif not isinstance(data['vendorId'], str):
        errors.append("'vendorId' must be a string")

    if not data.get('items'):
        errors.append("'items' must be a non-empty array")
    elif not isinstance(data['items'], list):
        errors.append("'items' must be an array")
    else:
        for i, item in enumerate(data['items']):
            if not item.get('itemId'):
                errors.append(f"items[{i}].itemId is required")

            if (
                not item.get('quantity')
                or not isinstance(item['quantity'], int)
                or item['quantity'] < 1
            ):
                errors.append(
                    f"items[{i}].quantity must be an integer >= 1"
                )

    if not data.get('deliveryAddress'):
        errors.append("'deliveryAddress' is required")
    elif not isinstance(data['deliveryAddress'], dict):
        errors.append("'deliveryAddress' must be an object")
    elif not data['deliveryAddress'].get('building'):
        errors.append("deliveryAddress.building is required")

    return errors


def validate_cancel_order(data):
    errors = []

    if not data:
        errors.append("Request body is empty")
        return errors

    if not data.get('reason'):
        errors.append("'reason' is required")
    elif data['reason'] not in [
        'USER_REQUEST',
        'VENDOR_REQUEST',
        'OUT_OF_STOCK',
        'OTHER'
    ]:
        errors.append(
            "'reason' must be one of: USER_REQUEST, VENDOR_REQUEST, OUT_OF_STOCK, OTHER"
        )

    return errors 