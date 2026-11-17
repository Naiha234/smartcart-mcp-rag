
# SmartCart AI
### E-commerce Customer Support & Operations Assistant

SmartCart AI is an intelligent e-commerce customer support application that combines Advanced Retrieval-Augmented Generation (RAG), Model Context Protocol (MCP), and LangGraph-based AI agents to automate common customer support and operational tasks.

The application helps customers retrieve policy information, track orders, check product availability, and submit refund requests through a conversational interface.

## Key Features

- **Advanced RAG:** Retrieves relevant information from e-commerce policy documents.
- **Hybrid Search:** Combines ChromaDB vector search and BM25 keyword search.
- **Reciprocal Rank Fusion:** Combines results from multiple retrieval methods.
- **Reranking:** Uses FlashRank to improve retrieval relevance.
- **LLM Integration:** Uses Groq API with the `openai/gpt-oss-120b` model.
- **MCP Integration:** Connects AI agents to structured e-commerce tools.
- **Multi-Agent Workflow:** Uses LangGraph to route customer requests.
- **Order Tracking:** Retrieves order information and status.
- **Product Availability:** Checks product prices and inventory.
- **Human-in-the-Loop:** Requires explicit approval before processing simulated refunds.
- **Streamlit Interface:** Provides a conversational customer support interface.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| User Interface | Streamlit |
| Agent Framework | LangGraph |
| Tool Integration | MCP |
| Vector Database | ChromaDB |
| Keyword Retrieval | BM25 |
| Reranking | FlashRank |
| Embeddings | BAAI/bge-small-en-v1.5 |
| LLM | Groq API |
| Database | SQLite |
| Environment | GitHub Codespaces |

## Project Architecture

```text
                  Customer
                     |
                     v
              Streamlit UI
                     |
                     v
              LangGraph Router
                     |
          +----------+----------+
          |          |          |
          v          v          v
       Policy      Order      Stock
       Agent       Agent      Agent
          |          |          |
          v          +-----+----+
       Advanced           |
          RAG              v
          |           MCP Server
          |               |
          v          SQLite Database
   Policy Documents         |
          |                 v
          v          E-commerce Tools
   Hybrid Retrieval
          |
     +----+----+
     |         |
  ChromaDB   BM25
     |         |
     +----+----+
          |
          v
    Rank Fusion
          |
          v
      FlashRank
          |
          v
       Groq LLM
          |
          v
    Customer Answer


    Refund Workflow:
    Refund Agent
         |
         v
    Order Verification
         |
         v
    Eligibility Check
         |
         v
    Human Approval
         |
         v
    MCP Refund Tool
         |
         v
    SQLite Refund Record
```

## Project Structure

```text
smartcart-mcp-rag/
│
├── data/
│   ├── policies.txt
│   ├── ecommerce.db
│   └── chroma_db/
│
├── src/
│   ├── __init__.py
│   ├── setup_db.py
│   ├── mcp_server.py
│   ├── rag_pipeline.py
│   ├── agent.py
│   └── test_mcp.py
│
├── app.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Naiha234/smartcart-mcp-rag.git
cd smartcart-mcp-rag
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

Replace the placeholder with your own Groq API key.

Never publish your API key or commit your `.env` file.

### 4. Run the Application

```bash
streamlit run app.py
```

Open the Streamlit application in your browser.

## Demo Data

The project includes sample e-commerce customers, products, and orders for testing.

Example customer IDs:

- CUST001
- CUST002
- CUST003

Example product IDs:

- PROD001
- PROD002
- PROD003
- PROD004

Example order IDs:

- ORD1001
- ORD1002
- ORD1003
- ORD1004

These are demonstration records, not real customer transactions.

## Refund Workflow

The refund workflow follows these steps:

1. Receive a customer refund request.
2. Verify the order and customer ownership.
3. Check the order status.
4. Allow only eligible delivered orders to proceed.
5. Pause the LangGraph workflow for explicit human approval.
6. Execute the simulated refund through the MCP tool after approval.
7. Store the refund record and update the order status in SQLite.

**Important:** Refund processing is simulated. The application does not transfer actual money or connect to a payment gateway.

## Testing

The following application components have been tested:

- MCP order status retrieval.
- MCP product stock retrieval.
- Hybrid RAG policy retrieval.
- Order tracking through Streamlit.
- Product availability through Streamlit.
- Refund eligibility validation.
- Refund rejection without processing.
- Refund approval and simulated processing.
- SQLite refund record verification.

## Security Notes

- Keep API keys in environment variables.
- Do not commit `.env` to GitHub.
- Use authenticated customer ownership checks before retrieving order information.
- Require explicit approval before executing refund operations.
- Use synthetic data for demonstrations.

## Future Improvements

- LLM-based intent classification.
- Persistent LangGraph checkpointing.
- User authentication and authorization.
- More comprehensive automated testing.
- Production database integration.
- Payment gateway integration.
- Improved monitoring and logging.

## Author

**Naiha234**

GitHub: https://github.com/Naiha234

## Disclaimer

SmartCart AI is an educational demonstration project. Its policies, customer records, inventory, and refund operations are simulated and should not be treated as a production e-commerce service.
