report_data = []
# Ensure 'orders' are fetched with their associated items using eager loading or a JOIN
# Example: orders = db.get_orders_with_items(user_id)
for order in orders:
    # Items are now efficiently loaded with the order object
    report_data.append({
        "order_id": order.id,
        "items": [item.to_dict() for item in order.items]
    })