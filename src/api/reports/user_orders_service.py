from sqlalchemy.orm import joinedload

class OrderService:
    def get_user_orders(self, user_id):
        # Optimized query using joinedload to fetch orders and their items in a single query
        orders = db.session.query(Order).options(joinedload(Order.items)).filter_by(user_id=user_id).all()
        result = []
        for order in orders:
            result.append({
                "order_id": order.id,
                "items": [{"item_id": item.id, "product_name": item.product_name} for item in order.items]
            })
        return result