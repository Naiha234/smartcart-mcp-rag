
import sqlite3
from pathlib import Path
from mcp.server.fastmcp import FastMCP


# ==========================================
# 1. CREATE MCP SERVER
# ==========================================

mcp = FastMCP("SmartCart")


# ==========================================
# 2. DATABASE CONNECTION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "ecommerce.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# 3. TOOL: GET ORDER STATUS
# ==========================================

@mcp.tool()
def get_order_status(order_id: str, customer_id: str) -> dict:
    """Get order information for a customer."""

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                o.order_id,
                c.name AS customer_name,
                p.name AS product_name,
                o.quantity,
                o.total_amount,
                o.order_status,
                o.order_date
            FROM orders o
            JOIN customers c
                ON o.customer_id = c.customer_id
            JOIN products p
                ON o.product_id = p.product_id
            WHERE o.order_id = ?
            AND o.customer_id = ?
        """, (order_id, customer_id))

        order = cursor.fetchone()

        if order is None:
            return {
                "success": False,
                "message": "Order not found."
            }

        return {
            "success": True,
            "order": dict(order)
        }

    finally:
        conn.close()


# ==========================================
# 4. TOOL: CHECK PRODUCT STOCK
# ==========================================

@mcp.tool()
def check_product_stock(product_id: str) -> dict:
    """Check product price and available stock."""

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                product_id,
                name,
                price,
                stock
            FROM products
            WHERE product_id = ?
        """, (product_id,))

        product = cursor.fetchone()

        if product is None:
            return {
                "success": False,
                "message": "Product not found."
            }

        return {
            "success": True,
            "product": dict(product),
            "in_stock": product["stock"] > 0
        }

    finally:
        conn.close()


# ==========================================
# 5. TOOL: PROCESS REFUND REQUEST
# ==========================================

@mcp.tool()
def process_refund_request(
    order_id: str,
    customer_id: str,
    confirmed: bool
) -> dict:
    """Process a demo refund after customer confirmation."""

    if not confirmed:
        return {
            "success": False,
            "message": "Customer confirmation is required."
        }

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Verify order ownership and status
        cursor.execute("""
            SELECT
                order_id,
                total_amount,
                order_status
            FROM orders
            WHERE order_id = ?
            AND customer_id = ?
        """, (order_id, customer_id))

        order = cursor.fetchone()

        if order is None:
            return {
                "success": False,
                "message": "Order not found."
            }

        # Only delivered orders can be refunded
        if order["order_status"] != "DELIVERED":
            return {
                "success": False,
                "message": (
                    "Only delivered orders are eligible "
                    "for this demo refund."
                )
            }

        # Prevent duplicate refunds
        cursor.execute("""
            SELECT refund_id
            FROM refunds
            WHERE order_id = ?
        """, (order_id,))

        if cursor.fetchone() is not None:
            return {
                "success": False,
                "message": "Refund has already been processed."
            }

        # Insert refund record
        cursor.execute("""
            INSERT INTO refunds (
                order_id,
                customer_id,
                reason,
                refund_amount,
                refund_status
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            order_id,
            customer_id,
            "Customer requested a refund",
            order["total_amount"],
            "PROCESSED"
        ))

        # Update order status
        cursor.execute("""
            UPDATE orders
            SET order_status = 'REFUNDED'
            WHERE order_id = ?
            AND customer_id = ?
        """, (order_id, customer_id))

        conn.commit()

        return {
            "success": True,
            "message": "Demo refund processed successfully.",
            "refund_amount": order["total_amount"]
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ==========================================
# 6. START MCP SERVER
# ==========================================

if __name__ == "__main__":
    mcp.run(transport="stdio")
