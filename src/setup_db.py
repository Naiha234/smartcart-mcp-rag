
import sqlite3
from pathlib import Path


# STEP 1: Define database location

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

DB_PATH = DATA_DIR / "ecommerce.db"


# STEP 2: Connect to database

def get_connection():

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# STEP 3: Create database tables

def create_tables(conn):

    cursor = conn.cursor()

    # Customers table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (

            customer_id TEXT PRIMARY KEY,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            phone TEXT

        )
    """)

    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (

            product_id TEXT PRIMARY KEY,

            name TEXT NOT NULL,

            category TEXT NOT NULL,

            price REAL NOT NULL,

            stock INTEGER NOT NULL,

            description TEXT

        )
    """)

    # Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (

            order_id TEXT PRIMARY KEY,

            customer_id TEXT NOT NULL,

            product_id TEXT NOT NULL,

            quantity INTEGER NOT NULL,

            total_amount REAL NOT NULL,

            order_status TEXT NOT NULL,

            order_date TEXT NOT NULL,

            FOREIGN KEY(customer_id)
                REFERENCES customers(customer_id),

            FOREIGN KEY(product_id)
                REFERENCES products(product_id)

        )
    """)

    # Refunds table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS refunds (

            refund_id INTEGER PRIMARY KEY AUTOINCREMENT,

            order_id TEXT NOT NULL,

            customer_id TEXT NOT NULL,

            reason TEXT NOT NULL,

            refund_amount REAL NOT NULL,

            refund_status TEXT NOT NULL,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(order_id)
                REFERENCES orders(order_id),

            FOREIGN KEY(customer_id)
                REFERENCES customers(customer_id)

        )
    """)

    conn.commit()


# STEP 4: Insert sample customers

def insert_sample_data(conn):

    cursor = conn.cursor()

    customers = [

        ("CUST001", "Ayesha Khan",
         "ayesha@example.com", "03001234567"),

        ("CUST002", "Ahmed Ali",
         "ahmed@example.com", "03007654321"),

        ("CUST003", "Sara Malik",
         "sara@example.com", "03001112223")

    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO customers
        (customer_id, name, email, phone)

        VALUES (?, ?, ?, ?)
    """, customers)


    # STEP 5: Insert sample products

    products = [

        ("PROD001", "Wireless Headphones",
         "Electronics", 8500, 15,
         "Wireless headphones with noise cancellation"),

        ("PROD002", "Smart Watch",
         "Electronics", 12000, 8,
         "Smart watch with fitness tracking"),

        ("PROD003", "Laptop",
         "Computers", 125000, 5,
         "High performance laptop"),

        ("PROD004", "Bluetooth Speaker",
         "Electronics", 4500, 0,
         "Portable Bluetooth speaker")

    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO products
        (product_id, name, category, price, stock, description)

        VALUES (?, ?, ?, ?, ?, ?)
    """, products)


    # STEP 6: Insert sample orders

    orders = [

        ("ORD1001", "CUST001", "PROD001",
         1, 8500, "DELIVERED", "2026-11-10"),

        ("ORD1002", "CUST002", "PROD002",
         1, 12000, "SHIPPED", "2026-11-12"),

        ("ORD1003", "CUST003", "PROD003",
         1, 125000, "PROCESSING", "2026-11-14"),

        ("ORD1004", "CUST001", "PROD004",
         1, 4500, "DELIVERED", "2026-11-09")

    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO orders
        (order_id, customer_id, product_id,
         quantity, total_amount, order_status, order_date)

        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, orders)

    conn.commit()


# STEP 7: Display database records

def display_records(conn):

    cursor = conn.cursor()

    tables = ["customers", "products", "orders", "refunds"]

    print("\nSMARTCART DATABASE SUMMARY")

    for table in tables:

        result = cursor.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()

        print(f"{table}: {result[0]} records")


# STEP 8: Main function

def main():

    print("Starting SmartCart database setup...")

    conn = get_connection()

    try:

        create_tables(conn)

        insert_sample_data(conn)

        display_records(conn)

        print("\nDatabase created successfully!")

        print(f"Location: {DB_PATH}")

    finally:

        conn.close()


if __name__ == "__main__":

    main()
