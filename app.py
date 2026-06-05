from flask import Flask, request, jsonify
import sqlite3
import logging
import time
import os

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db():
    # Use a file-based DB so it persists across requests in the same container
    db_path = '/tmp/demo.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Seed the database with 1000 users and 5000 orders to create a large dataset."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, user_id INTEGER, product TEXT, amount REAL)")
    
    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        logger.info("Seeding database...")
        users = [(i, f"User {i}", f"user{i}@example.com") for i in range(1, 1001)]
        cursor.executemany("INSERT INTO users VALUES (?, ?, ?)", users)
        
        orders = []
        for i in range(1, 1001):
            # Each user has 5 orders
            for j in range(5):
                orders.append((None, i, f"Product {j}", 10.99 * j))
        cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", orders)
        conn.commit()
    conn.close()

# Initialize DB on startup
if not os.path.exists('/tmp/demo.db'):
    init_db()


@app.route('/api/reports/user-orders', methods=['GET'])
def get_user_orders():
    """
    VIBE CODER MISTAKE: The Classic N+1 Query.
    Instead of doing a JOIN, we query the users, and then run a loop 
    that makes a separate SQL query for EVERY single user.
    With 1,000 users, this endpoint executes 1,001 SQL queries!
    """
    conn = get_db()
    cursor = conn.cursor()
    
    # Query 1
    # Optimized: Use a single JOIN query to fetch all users and their orders
    cursor.execute("""
        SELECT 
            u.id as user_id, 
            u.name as user_name, 
            o.product, 
            o.amount
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        ORDER BY u.id
    """)
    rows = cursor.fetchall()

    user_orders_map = {}
    for row in rows:
        user_id = row['user_id']
        if user_id not in user_orders_map:
            user_orders_map[user_id] = {
                "name": row['user_name'],
                "orders": []
            }
        
        # Only add order if it exists (for users with no orders due to LEFT JOIN)
        if row['product'] is not None:
            user_orders_map[user_id]["orders"].append({
                "product": row['product'], 
                "amount": row['amount']
            })
    
    results = list(user_orders_map.values())
        
    conn.close()
    
    # This will take several seconds due to 1000+ DB queries
    return jsonify({
        "status": "success", 
        "total_users": len(results),
        "data": results
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
