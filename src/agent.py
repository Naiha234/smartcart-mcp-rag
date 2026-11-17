
import asyncio
import json
import sys
from pathlib import Path
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ==================================================
# 1. PROJECT CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.rag_pipeline import (
    build_rag_database,
    answer_customer_question
)

print("Initializing SmartCart RAG system...")

collection, embedding_model, bm25_index, policy_chunks = (
    build_rag_database()
)


# ==================================================
# 2. SHARED AGENT STATE
# ==================================================

class SmartCartState(TypedDict):
    question: str
    intent: str
    customer_id: Optional[str]
    order_id: Optional[str]
    product_id: Optional[str]
    answer: str


# ==================================================
# 3. INTENT DETECTION
# ==================================================

def route_intent(state: SmartCartState):

    question = state["question"].lower()

    refund_keywords = [
        "refund",
        "money back",
        "return my money",
        "request a refund"
    ]

    order_keywords = [
        "order status",
        "where is my order",
        "track my order",
        "order tracking",
        "my order",
        "track order",
        "order update"
    ]

    stock_keywords = [
        "stock",
        "available",
        "availability",
        "in stock",
        "product price",
        "product availability"
    ]

    if any(word in question for word in refund_keywords):
        intent = "refund"

    elif any(word in question for word in order_keywords):
        intent = "order"

    elif any(word in question for word in stock_keywords):
        intent = "stock"

    else:
        intent = "policy"

    print(f"\nDetected intent: {intent}")

    return {"intent": intent}


# ==================================================
# 4. MCP CONNECTION
# ==================================================

async def execute_mcp_tool(tool_name: str, arguments: dict):

    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[
            str(BASE_DIR / "src" / "mcp_server.py")
        ],
        env=None
    )

    async with stdio_client(server_parameters) as (
        read_stream,
        write_stream
    ):

        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments
            )

            if result.isError:

                raise RuntimeError(
                    f"MCP tool failed: {result.content}"
                )

            text_parts = [
                item.text
                for item in result.content
                if hasattr(item, "text")
            ]

            return "\n".join(text_parts)


def call_mcp_tool(tool_name: str, arguments: dict):

    return asyncio.run(
        execute_mcp_tool(tool_name, arguments)
    )


# ==================================================
# 5. RESPONSE PARSING
# ==================================================

def parse_mcp_response(response: str):

    try:

        return json.loads(response)

    except (json.JSONDecodeError, TypeError):

        return {
            "success": False,
            "message": str(response)
        }


def find_nested_value(data, possible_keys):

    if isinstance(data, dict):

        for key in possible_keys:

            if key in data and data[key] is not None:
                return data[key]

        for value in data.values():

            found = find_nested_value(
                value,
                possible_keys
            )

            if found is not None:
                return found

    elif isinstance(data, list):

        for item in data:

            found = find_nested_value(
                item,
                possible_keys
            )

            if found is not None:
                return found

    return None


# ==================================================
# 6. POLICY AGENT
# ==================================================

def policy_agent(state: SmartCartState):

    print("\nPolicy Agent activated.")

    try:

        result = answer_customer_question(
            state["question"],
            collection,
            embedding_model,
            bm25_index,
            policy_chunks
        )

        return {
            "answer": result["answer"]
        }

    except Exception as error:

        print(f"Policy Agent Error: {error}")

        return {
            "answer": (
                f"Unable to answer your policy question: {error}"
            )
        }


# ==================================================
# 7. ORDER AGENT
# ==================================================

def order_agent(state: SmartCartState):

    print("\nOrder Agent activated.")

    order_id = state.get("order_id")
    customer_id = state.get("customer_id")

    if not order_id or not customer_id:

        return {
            "answer": (
                "Please provide both your order ID "
                "and customer ID."
            )
        }

    try:

        response = call_mcp_tool(
            "get_order_status",
            {
                "order_id": order_id,
                "customer_id": customer_id
            }
        )

        data = parse_mcp_response(response)

        if data.get("success") is not True:

            return {
                "answer": (
                    "We could not find your order. "
                    "Please verify your order ID and customer ID."
                )
            }

        order = data.get("order", {})

        status = order.get(
            "order_status",
            "UNKNOWN"
        )

        status_messages = {
            "PROCESSING": "Your order is currently being prepared.",
            "SHIPPED": "Your order has been dispatched and is on its way.",
            "DELIVERED": "Your order has been successfully delivered.",
            "REFUNDED": "Your order has been refunded."
        }

        answer = f"""
### 📦 Your Order Details

**Order ID:** {order.get("order_id", "N/A")}

**Customer:** {order.get("customer_name", "N/A")}

**Product:** {order.get("product_name", "N/A")}

**Quantity:** {order.get("quantity", "N/A")}

**Total Amount:** Rs. {order.get("total_amount", 0):,.2f}

**Order Status:** {status}

**Order Date:** {order.get("order_date", "N/A")}

---

{status_messages.get(status, "Please contact customer support for more information.")}
"""

        return {
            "answer": answer
        }

    except Exception as error:

        return {
            "answer": f"Unable to retrieve order details: {error}"
        }


# ==================================================
# 8. STOCK AGENT
# ==================================================

def stock_agent(state: SmartCartState):

    print("\nStock Agent activated.")

    product_id = state.get("product_id")

    if not product_id:

        return {
            "answer": "Please provide a product ID."
        }

    try:

        response = call_mcp_tool(
            "check_product_stock",
            {
                "product_id": product_id
            }
        )

        data = parse_mcp_response(response)

        if data.get("success") is not True:

            return {
                "answer": (
                    "Product information could not be retrieved. "
                    "Please check the product ID."
                )
            }

        product = data.get("product", {})

        stock = product.get("stock", 0)

        availability = (
            "Available in stock"
            if data.get("in_stock")
            else "Currently out of stock"
        )

        answer = f"""
### 🛍️ Product Details

**Product:** {product.get("name", "N/A")}

**Product ID:** {product.get("product_id", "N/A")}

**Price:** Rs. {product.get("price", 0):,.2f}

**Available Units:** {stock}

**Availability:** {availability}
"""

        return {
            "answer": answer
        }

    except Exception as error:

        return {
            "answer": f"Unable to check product stock: {error}"
        }


# ==================================================
# 9. HUMAN-IN-THE-LOOP REFUND AGENT
# ==================================================

def refund_agent(state: SmartCartState):

    print("\nRefund Agent activated.")

    order_id = state.get("order_id")
    customer_id = state.get("customer_id")

    # STEP 1: Validate required information

    if not order_id or not customer_id:

        return {
            "answer": (
                "Please provide both your order ID "
                "and customer ID to check refund eligibility."
            )
        }

    # STEP 2: Verify order ownership

    try:

        order_response = call_mcp_tool(
            "get_order_status",
            {
                "order_id": order_id,
                "customer_id": customer_id
            }
        )

        order_data = parse_mcp_response(
            order_response
        )

    except Exception as error:

        return {
            "answer": (
                f"Order verification failed: {error}. "
                "No refund was processed."
            )
        }

    print("\nVerified order information:")

    print(json.dumps(
        order_data,
        indent=2
    ))

    # STEP 3: Verify successful order lookup

    success = find_nested_value(
        order_data,
        ["success"]
    )

    if success is not True:

        return {
            "answer": (
                "Order verification failed. "
                "Please check your order ID and customer ID. "
                "No refund was processed."
            )
        }

    # STEP 4: Extract order status

    order_status = find_nested_value(
        order_data,
        ["order_status", "status"]
    )

    if order_status is None:

        return {
            "answer": (
                "Order status could not be verified. "
                "No refund was processed."
            )
        }

    order_status = str(order_status).upper()

    print(f"\nVerified order status: {order_status}")

    # STEP 5: Check eligibility

    if order_status != "DELIVERED":

        return {
            "answer": (
                f"Refund cannot proceed because your order status "
                f"is {order_status}. Only delivered orders are "
                "eligible under the demo policy. "
                "No refund was processed."
            )
        }

    order_amount = find_nested_value(
        order_data,
        ["total_amount", "amount"]
    )

    print("\nRefund eligibility check passed.")

    # STEP 6: Request explicit human approval
    # Keep interrupt outside try/except blocks.

    approval = interrupt({

        "message": (
            "This order is DELIVERED and has passed "
            "the initial eligibility check. "
            "Do you explicitly approve the simulated refund?"
        ),

        "order_id": order_id,

        "customer_id": customer_id,

        "order_status": order_status,

        "order_amount": order_amount

    })

    # STEP 7: Validate approval

    if not isinstance(approval, dict):

        return {
            "answer": (
                "Invalid approval response. "
                "No refund was processed."
            )
        }

    if approval.get("approved") is not True:

        return {
            "answer": (
                "Refund approval was not provided. "
                "The request was cancelled. "
                "No refund was processed."
            )
        }

    # STEP 8: Process refund through MCP

    print("\nHuman approval received.")

    print("Calling MCP refund tool...")

    try:

        refund_response = call_mcp_tool(
            "process_refund_request",
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "confirmed": True
            }
        )

        refund_data = parse_mcp_response(
            refund_response
        )

        return {
            "answer": json.dumps(
                refund_data,
                indent=2
            )
        }

    except Exception as error:

        return {
            "answer": (
                f"Refund processing failed: {error}. "
                "Please verify the refund status before retrying."
            )
        }


# ==================================================
# 10. AGENT SELECTION
# ==================================================

def select_agent(state: SmartCartState):

    intent = state["intent"]

    if intent == "order":
        return "order_agent"

    elif intent == "stock":
        return "stock_agent"

    elif intent == "refund":
        return "refund_agent"

    return "policy_agent"


# ==================================================
# 11. LANGGRAPH WORKFLOW
# ==================================================

workflow = StateGraph(SmartCartState)

workflow.add_node("router", route_intent)
workflow.add_node("policy_agent", policy_agent)
workflow.add_node("order_agent", order_agent)
workflow.add_node("stock_agent", stock_agent)
workflow.add_node("refund_agent", refund_agent)

workflow.add_edge(START, "router")

workflow.add_conditional_edges(
    "router",
    select_agent,
    {
        "policy_agent": "policy_agent",
        "order_agent": "order_agent",
        "stock_agent": "stock_agent",
        "refund_agent": "refund_agent"
    }
)

workflow.add_edge("policy_agent", END)
workflow.add_edge("order_agent", END)
workflow.add_edge("stock_agent", END)
workflow.add_edge("refund_agent", END)


# ==================================================
# 12. CHECKPOINTING
# ==================================================

memory = MemorySaver()

smartcart_graph = workflow.compile(
    checkpointer=memory
)


# ==================================================
# 13. RUN SMARTCART AGENT
# ==================================================

def run_smartcart_agent(
    question: str,
    customer_id: Optional[str] = None,
    order_id: Optional[str] = None,
    product_id: Optional[str] = None
):

    initial_state = {
        "question": question,
        "intent": "",
        "customer_id": customer_id,
        "order_id": order_id,
        "product_id": product_id,
        "answer": ""
    }

    config = {
        "configurable": {
            "thread_id": str(__import__("uuid").uuid4())
        }
    }

    result = smartcart_graph.invoke(
        initial_state,
        config=config
    )

    interruptions = result.get(
        "__interrupt__",
        []
    )

    if interruptions:

        approval_details = interruptions[0].value

        print("\n" + "=" * 50)
        print("HUMAN APPROVAL REQUIRED")
        print("=" * 50)

        print(json.dumps(
            approval_details,
            indent=2
        ))

        print("\nType YES to approve the simulated refund.")
        print("Type NO to reject the refund.")

        user_response = input(
            "\nYour decision: "
        ).strip().upper()

        result = smartcart_graph.invoke(
            Command(
                resume={
                    "approved": user_response == "YES"
                }
            ),
            config=config
        )

    print("\n" + "=" * 50)
    print("SMARTCART AI RESPONSE")
    print("=" * 50)

    print(
        result.get(
            "answer",
            "No response generated."
        )
    )

    print("=" * 50)

    return result


# ==================================================
# 14. OPTIONAL COMMAND-LINE TEST
# ==================================================

if __name__ == "__main__":

    run_smartcart_agent(
        question="Where is my order?",
        customer_id="CUST002",
        order_id="ORD1002"
    )
