
import json
import uuid
import streamlit as st

from langgraph.types import Command
from src.agent import smartcart_graph


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="SmartCart AI",
    page_icon="🛒",
    layout="wide"
)


# ==================================================
# 2. SESSION STATE
# ==================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "pending_approval" not in st.session_state:
    st.session_state.pending_approval = False

if "approval_details" not in st.session_state:
    st.session_state.approval_details = None

if "customer_id" not in st.session_state:
    st.session_state.customer_id = ""

if "order_id" not in st.session_state:
    st.session_state.order_id = ""

if "product_id" not in st.session_state:
    st.session_state.product_id = ""


def get_config():

    return {
        "configurable": {
            "thread_id": st.session_state.thread_id
        }
    }


# ==================================================
# 3. RESPONSE FORMATTING
# ==================================================

def format_response(response):

    """
    Convert MCP JSON responses into readable
    customer-friendly messages.
    """

    try:
        data = json.loads(response)

    except (json.JSONDecodeError, TypeError):
        return str(response)

    # ORDER RESPONSE

    if isinstance(data, dict) and "order" in data:

        if not data.get("success"):
            return data.get(
                "message",
                "We could not find your order."
            )

        order = data["order"]

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

        return f"""
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

    # PRODUCT STOCK RESPONSE

    if isinstance(data, dict) and "product" in data:

        if not data.get("success"):
            return data.get(
                "message",
                "Product information could not be retrieved."
            )

        product = data["product"]

        stock = product.get("stock", 0)

        availability = (
            "Available in stock"
            if data.get("in_stock")
            else "Currently out of stock"
        )

        return f"""
### 🛍️ Product Details

**Product:** {product.get("name", "N/A")}

**Product ID:** {product.get("product_id", "N/A")}

**Price:** Rs. {product.get("price", 0):,.2f}

**Available Units:** {stock}

**Availability:** {availability}
"""

    # REFUND RESPONSE

    if isinstance(data, dict) and "refund_amount" in data:

        if data.get("success"):

            return f"""
### ✅ Refund Processed Successfully

**Refund Amount:** Rs. {data.get("refund_amount", 0):,.2f}

**Message:** {data.get("message", "Refund processed successfully.")}

Your simulated refund request has been completed.
"""

        return data.get(
            "message",
            "Refund could not be processed."
        )

    # OTHER JSON RESPONSES

    if isinstance(data, dict):

        return data.get(
            "message",
            json.dumps(data, indent=2)
        )

    return str(response)


# ==================================================
# 4. CUSTOM CSS
# ==================================================

st.markdown("""
<style>

.main-title {
    font-size: 38px;
    font-weight: 750;
    color: #2563EB;
    margin-bottom: 0;
}

.subtitle {
    color: #64748b;
    font-size: 16px;
}

div[data-testid="stChatMessage"] {
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# 5. HEADER
# ==================================================

st.markdown(
    '<p class="main-title">🛒 SmartCart AI</p>',
    unsafe_allow_html=True
)

st.markdown(
    '<p class="subtitle">'
    'Your intelligent e-commerce customer support assistant'
    '</p>',
    unsafe_allow_html=True
)

st.divider()


# ==================================================
# 6. SIDEBAR
# ==================================================

with st.sidebar:

    st.title("⚙️ Customer Details")

    st.write(
        "Enter your demo customer information "
        "to access order and refund services."
    )

    customer_id = st.text_input(
        "Customer ID",
        key="customer_id",
        placeholder="e.g. CUST001"
    )

    order_id = st.text_input(
        "Order ID",
        key="order_id",
        placeholder="e.g. ORD1002"
    )

    product_id = st.text_input(
        "Product ID",
        key="product_id",
        placeholder="e.g. PROD001"
    )

    st.divider()

    st.subheader("Available Services")

    st.markdown("""
    📦 Order Tracking

    🛍️ Product Availability

    📋 Return & Refund Policies

    💰 Refund Requests

    🤖 AI Customer Support
    """)

    st.divider()

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True
    ):

        st.session_state.messages = []
        st.session_state.pending_approval = False
        st.session_state.approval_details = None
        st.session_state.thread_id = str(uuid.uuid4())

        st.rerun()

    st.caption(
        "SmartCart AI | Educational Demo"
    )


# ==================================================
# 7. WELCOME SCREEN
# ==================================================

if not st.session_state.messages:

    st.info(
        "Welcome to SmartCart AI! "
        "Ask me about your orders, products, "
        "shipping, returns or refunds."
    )

    st.markdown("### What can I help you with?")

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("""
        **📦 Order Support**

        - Where is my order?
        - Check my order status.

        **🛍️ Product Support**

        - Is this product available?
        - Check product stock.
        """)

    with col2:

        st.markdown("""
        **📋 Policy Support**

        - What is the return period?
        - What is your shipping policy?

        **💰 Refund Support**

        - I want to request a refund.
        - How can I get my money back?
        """)


# ==================================================
# 8. DISPLAY CHAT HISTORY
# ==================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# ==================================================
# 9. HUMAN APPROVAL INTERFACE
# ==================================================

if st.session_state.pending_approval:

    details = st.session_state.approval_details

    st.divider()

    st.warning(
        "Human approval is required before "
        "processing this simulated refund."
    )

    st.subheader("💰 Refund Approval Details")

    if details:

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Order ID",
            details.get("order_id", "N/A")
        )

        col2.metric(
            "Order Status",
            details.get("order_status", "N/A")
        )

        amount = details.get("order_amount")

        col3.metric(
            "Refund Amount",
            (
                f"Rs. {amount:,.2f}"
                if isinstance(amount, (int, float))
                else "Not available"
            )
        )

    st.write(
        "Do you explicitly approve this simulated refund?"
    )

    yes_col, no_col = st.columns(2)

    with yes_col:

        approve = st.button(
            "✅ YES - Approve Refund",
            type="primary",
            use_container_width=True
        )

    with no_col:

        reject = st.button(
            "❌ NO - Reject Refund",
            use_container_width=True
        )

    if approve or reject:

        approved = approve

        try:

            with st.spinner(
                "Processing your decision..."
            ):

                result = smartcart_graph.invoke(
                    Command(
                        resume={
                            "approved": approved
                        }
                    ),
                    config=get_config()
                )

            interruptions = result.get(
                "__interrupt__",
                []
            )

            if interruptions:

                st.error(
                    "The workflow is still waiting for approval."
                )

            else:

                st.session_state.pending_approval = False
                st.session_state.approval_details = None

                answer = format_response(
                    result.get(
                        "answer",
                        "No response generated."
                    )
                )

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })

                st.rerun()

        except Exception as error:

            st.error(
                f"Unable to complete the approval workflow: {error}"
            )


# ==================================================
# 10. CHAT INPUT
# ==================================================

question = st.chat_input(
    "Ask SmartCart AI anything...",
    disabled=st.session_state.pending_approval
)


# ==================================================
# 11. PROCESS CUSTOMER QUESTIONS
# ==================================================

if question:

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    initial_state = {

        "question": question,

        "intent": "",

        "customer_id": (
            st.session_state.customer_id.strip() or None
        ),

        "order_id": (
            st.session_state.order_id.strip() or None
        ),

        "product_id": (
            st.session_state.product_id.strip() or None
        ),

        "answer": ""
    }

    try:

        with st.chat_message("assistant"):

            with st.spinner(
                "SmartCart AI is thinking..."
            ):

                result = smartcart_graph.invoke(
                    initial_state,
                    config=get_config()
                )

            interruptions = result.get(
                "__interrupt__",
                []
            )

            if interruptions:

                details = interruptions[0].value

                st.session_state.pending_approval = True

                st.session_state.approval_details = details

                response = (
                    "Your refund request passed the initial "
                    "eligibility check. Please review the "
                    "approval details and choose YES or NO below."
                )

                st.markdown(response)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })

            else:

                raw_answer = result.get(
                    "answer",
                    "No response generated."
                )

                response = format_response(raw_answer)

                st.markdown(response)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response
                })

        if st.session_state.pending_approval:
            st.rerun()

    except Exception as error:

        error_message = (
            f"An error occurred: {error}"
        )

        st.error(error_message)

        st.session_state.messages.append({
            "role": "assistant",
            "content": error_message
        })


# ==================================================
# 12. FOOTER
# ==================================================

st.divider()

st.caption(
    "SmartCart AI | Advanced RAG + MCP + LangGraph Agents "
    "| Educational Demo Project"
)
