"""
seed_db.py — Generates a sample e-commerce database for the Gemini + MCP Playground

Run this once to create the database file (store.db).
The AI agent will then use this database to answer your questions.

What's in the database:
  - categories  →  Product categories (Electronics, Clothing, etc.)
  - products    →  Items for sale with prices and stock
  - customers   →  People who buy things
  - orders      →  When someone places an order
  - order_items →  Which products were in each order
"""

import sqlite3
import random
from datetime import datetime, timedelta

# === STEP 1: Connect to the database file ===
# This creates 'store.db' in the same folder as this script
# If 'store.db' already exists, we'll overwrite it
print("🔨 Creating database...")
conn = sqlite3.connect("store.db")
cursor = conn.cursor()

# === STEP 2: Define the table structure ===
# Each table is like a spreadsheet with columns (name, type, etc.)

cursor.executescript("""
    -- Clear any existing data so we can re-run safely
    DROP TABLE IF EXISTS order_items;
    DROP TABLE IF EXISTS orders;
    DROP TABLE IF EXISTS products;
    DROP TABLE IF EXISTS customers;
    DROP TABLE IF EXISTS categories;

    -- Categories: Groups that products belong to
    CREATE TABLE categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT
    );

    -- Products: Items available to buy
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        stock INTEGER NOT NULL DEFAULT 0,
        category_id INTEGER,
        FOREIGN KEY (category_id) REFERENCES categories(id)
    );

    -- Customers: People who place orders
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        city TEXT,
        signup_date TEXT NOT NULL
    );

    -- Orders: A purchase made by a customer
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        order_date TEXT NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    );

    -- Order Items: Individual products within an order
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );
""")

print("✅ Tables created!")

# === STEP 3: Fill the tables with sample data ===

# --- Categories ---
categories = [
    ("Electronics", "Gadgets, devices, and tech accessories"),
    ("Clothing", "Apparel, shoes, and accessories"),
    ("Home & Kitchen", "Furniture, cookware, and home decor"),
    ("Books", "Fiction, non-fiction, and educational"),
    ("Sports & Outdoors", "Fitness gear and outdoor equipment"),
]

cursor.executemany(
    "INSERT INTO categories (name, description) VALUES (?, ?)",
    categories
)
print(f"✅ {len(categories)} categories added!")

# --- Products ---
products = [
    # (name, description, price, stock, category_id)
    # Electronics (category_id = 1)
    ("Wireless Headphones", "Noise-cancelling Bluetooth headphones", 79.99, 50, 1),
    ("USB-C Hub", "7-in-1 multiport adapter", 34.99, 120, 1),
    ("Bluetooth Speaker", "Portable waterproof speaker", 49.99, 80, 1),
    ("Laptop Stand", "Adjustable aluminum stand", 29.99, 65, 1),
    ("Mechanical Keyboard", "RGB backlit mechanical keyboard", 89.99, 40, 1),
    
    # Clothing (category_id = 2)
    ("Cotton T-Shirt", "100% organic cotton crew neck", 24.99, 200, 2),
    ("Denim Jacket", "Classic blue denim jacket", 89.99, 35, 2),
    ("Running Shoes", "Lightweight mesh running shoes", 119.99, 45, 2),
    ("Winter Scarf", "Wool blend scarf", 19.99, 90, 2),
    ("Baseball Cap", "Adjustable cotton cap", 14.99, 150, 2),
    
    # Home & Kitchen (category_id = 3)
    ("Coffee Maker", "12-cup programmable coffee maker", 44.99, 30, 3),
    ("Cast Iron Pan", "12-inch pre-seasoned skillet", 39.99, 55, 3),
    ("Desk Lamp", "LED desk lamp with USB charging", 34.99, 70, 3),
    ("Throw Blanket", "Soft microfiber throw blanket", 29.99, 100, 3),
    ("Food Container Set", "10-piece glass container set", 24.99, 85, 3),
    
    # Books (category_id = 4)
    ("Python Crash Course", "A hands-on introduction to Python", 39.99, 60, 4),
    ("Atomic Habits", "An easy way to build good habits", 16.99, 95, 4),
    ("Design Patterns", "Elements of reusable software", 54.99, 40, 4),
    ("The Alchemist", "A fable about following your dream", 13.99, 110, 4),
    ("Clean Code", "A handbook of agile software craftsmanship", 44.99, 50, 4),
    
    # Sports & Outdoors (category_id = 5)
    ("Yoga Mat", "Non-slip exercise mat", 25.99, 75, 5),
    ("Water Bottle", "Stainless steel insulated bottle", 22.99, 120, 5),
    ("Resistance Bands", "Set of 5 exercise bands", 15.99, 90, 5),
    ("Camping Tent", "4-person waterproof tent", 159.99, 20, 5),
    ("Hiking Backpack", "40L lightweight daypack", 69.99, 35, 5),
]

cursor.executemany(
    "INSERT INTO products (name, description, price, stock, category_id) VALUES (?, ?, ?, ?, ?)",
    products
)
print(f"✅ {len(products)} products added!")

# --- Customers ---
customers = [
    ("Alice Johnson", "alice@email.com", "New York", "2024-01-15"),
    ("Bob Smith", "bob@email.com", "Los Angeles", "2024-02-20"),
    ("Charlie Brown", "charlie@email.com", "Chicago", "2024-03-10"),
    ("Diana Prince", "diana@email.com", "Houston", "2024-04-05"),
    ("Eve Wilson", "eve@email.com", "Phoenix", "2024-05-12"),
    ("Frank Miller", "frank@email.com", "Philadelphia", "2024-06-18"),
    ("Grace Lee", "grace@email.com", "San Antonio", "2024-07-22"),
    ("Henry Davis", "henry@email.com", "San Diego", "2024-08-30"),
    ("Ivy Chen", "ivy@email.com", "Dallas", "2024-09-14"),
    ("Jack Taylor", "jack@email.com", "San Jose", "2024-10-01"),
]

cursor.executemany(
    "INSERT INTO customers (name, email, city, signup_date) VALUES (?, ?, ?, ?)",
    customers
)
print(f"✅ {len(customers)} customers added!")

# --- Orders & Order Items ---
# Let's generate ~30 orders with random items
order_statuses = ["delivered", "delivered", "delivered", "shipped", "pending", "cancelled"]
# "delivered" is listed 3x to make it more common (weighted random)

base_date = datetime(2024, 6, 1)

for order_num in range(1, 31):
    customer_id = random.randint(1, len(customers))
    # Random date between June 2024 and March 2025
    days_offset = random.randint(0, 300)
    order_date = base_date + timedelta(days=days_offset)
    status = random.choice(order_statuses)
    
    # Pick 1-4 random products for this order
    num_items = random.randint(1, 4)
    ordered_products = random.sample(range(1, len(products) + 1), num_items)
    
    total = 0
    items_data = []
    for prod_id in ordered_products:
        qty = random.randint(1, 3)
        # Get the product's price from our products list
        unit_price = products[prod_id - 1][2]  # price is index 2 in the tuple
        total += unit_price * qty
        items_data.append((prod_id, qty, unit_price))
    
    # Round total to 2 decimal places
    total = round(total, 2)
    
    cursor.execute(
        "INSERT INTO orders (customer_id, order_date, total_amount, status) VALUES (?, ?, ?, ?)",
        (customer_id, order_date.strftime("%Y-%m-%d"), total, status)
    )
    order_id = cursor.lastrowid
    
    for prod_id, qty, price in items_data:
        cursor.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
            (order_id, prod_id, qty, price)
        )

print("✅ 30 orders with items added!")

# === STEP 4: Commit and close ===
conn.commit()
conn.close()

print("\n🎉 Database created successfully!")
print("📁 File: store.db")
print("\n📊 Tables in the database:")
print("  1. categories  — 5 product categories")
print("  2. products    — 25 products across categories")
print("  3. customers   — 10 customers")
print("  4. orders      — 30 orders with different statuses")
print("  5. order_items — Items within each order")

# Bonus: Show a quick preview
print("\n👀 Quick Preview:")
conn = sqlite3.connect("store.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) || ' products' FROM products")
print(f"  📦 {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) || ' orders' FROM orders")
print(f"  🧾 {cursor.fetchone()[0]}")

cursor.execute("SELECT ROUND(SUM(total_amount), 2) || ' total revenue' FROM orders")
print(f"  💰 ${cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) || ' customers' FROM customers")
print(f"  👤 {cursor.fetchone()[0]}")

conn.close()
print("\nType this to explore the data:")
print("  sqlite3 store.db \"SELECT * FROM products;\"")
