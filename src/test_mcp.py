
import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ==========================================
# 1. PROJECT CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

SERVER_FILE = BASE_DIR / "src" / "mcp_server.py"


# ==========================================
# 2. MCP SERVER PARAMETERS
# ==========================================

server_params = StdioServerParameters(
    command=sys.executable,
    args=[str(SERVER_FILE)],
    cwd=str(BASE_DIR)
)


# ==========================================
# 3. MCP CLIENT TEST
# ==========================================

async def main():

    print("Starting SmartCart MCP Client...")

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            # Initialize connection
            await session.initialize()

            print("\nMCP connection established!")

            # Discover available tools
            tools_result = await session.list_tools()

            print("\nAvailable MCP Tools:")

            for tool in tools_result.tools:
                print(f"- {tool.name}: {tool.description}")

            # ==================================
            # TEST 1: ORDER STATUS
            # ==================================

            print("\nTEST 1: Checking order status...")

            order_result = await session.call_tool(
                "get_order_status",
                arguments={
                    "order_id": "ORD1002",
                    "customer_id": "CUST002"
                }
            )

            print("\nOrder Status Result:")

            for item in order_result.content:
                if hasattr(item, "text"):
                    print(item.text)

            if order_result.isError:
                raise RuntimeError("Order status tool failed.")

            # ==================================
            # TEST 2: PRODUCT STOCK
            # ==================================

            print("\nTEST 2: Checking product stock...")

            stock_result = await session.call_tool(
                "check_product_stock",
                arguments={
                    "product_id": "PROD001"
                }
            )

            print("\nProduct Stock Result:")

            for item in stock_result.content:
                if hasattr(item, "text"):
                    print(item.text)

            if stock_result.isError:
                raise RuntimeError("Product stock tool failed.")

            print("\nMCP CLIENT TEST COMPLETED!")


# ==========================================
# 4. RUN CLIENT
# ==========================================

if __name__ == "__main__":

    asyncio.run(main())
