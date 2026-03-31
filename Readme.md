# 🍽️ Restaurant Agent

An AI-powered customer support agent for restaurants. Customers chat naturally, ask about the menu, and place orders — the agent handles everything automatically.

Built with **FastAPI**, **LangGraph**, **Deepseek**, and **pgvector**.

---

## Features

- 💬 **Conversational AI** — customers chat naturally, the agent remembers context across the whole conversation
- 🔍 **RAG-powered answers** — menu, prices, hours, delivery zones, and payment info retrieved from a vector knowledge base
- 🛒 **Automatic order placement** — agent collects name, phone, address, and items, then writes the order to the database
- 🧠 **Structured item parsing** — plain language like "2x burger and a coke" gets parsed into clean JSON before hitting the DB
- 💰 **Automatic price calculation** — total price computed from the knowledge base at order time
- 📦 **Orders dashboard** — REST endpoint for the restaurant owner to view all incoming orders
- 🐳 **Fully Dockerized** — one command to run everything

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI |
| Agent | LangGraph 1.x |
| LLM | Deepseek (`deepseek-chat`) |
| Embeddings | Ollama `nomic-embed-text` (local) |
| Vector DB | PostgreSQL + pgvector |
| ORM | SQLAlchemy |
| Messaging | Twilio WhatsApp *(coming soon)* |

---

## Architecture

```
Customer message (HTTP or WhatsApp)
         │
         ▼
   POST /api/chat
         │
         ├── Load conversation history from DB
         │
         ▼
   LangGraph Agent Loop
         │
    ┌────┴─────┐
    │  agent   │  ← Deepseek LLM decides what to do
    └────┬─────┘
         │
   tool needed?
    yes  │   no
         │    └──→ final response
         ▼
    ┌────┴─────┐
    │  tools   │
    └────┬─────┘
         │
    ├── search_menu()     → pgvector similarity search → context
    └── place_order()     → parse items → calculate price → write to DB
         │
         ▼
   back to agent → final response
         │
         ▼
   Save updated history to DB
   Return response to customer
```

---

## Project Structure

```
restaurant-agent/
├── app/
│   ├── main.py                        # FastAPI app, lifespan startup
│   ├── database.py                    # SQLAlchemy engine, session, pgvector setup
│   ├── models/
│   │   ├── order.py                   # Order table
│   │   ├── conversation.py            # Conversation history table
│   │   └── knowledge_chunk.py        # pgvector embeddings table
│   ├── api/
│   │   ├── chat.py                    # POST /api/chat
│   │   └── orders.py                  # GET /api/orders
│   ├── agent/
│   │   ├── graph.py                   # LangGraph agent graph
│   │   └── tools.py                   # search_menu + place_order tools
│   ├── services/
│   │   ├── embedding_service.py       # Ollama nomic-embed-text wrapper
│   │   └── rag_service.py             # Text chunking, ingestion, similarity search
│   └── data/
│       └── restaurant_info.txt        # Restaurant knowledge base source
├── .env
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose
- [Ollama](https://ollama.com/download) running locally with `nomic-embed-text` pulled
- A [Deepseek API key](https://platform.deepseek.com/)

Pull the embedding model if you haven't already:

```bash
ollama pull nomic-embed-text
```

### 1. Configure environment

Copy the example and fill in your values:

```bash
cp .env.example .env
```

```env
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

OLLAMA_BASE_URL=http://host.docker.internal:11434
EMBEDDING_MODEL=nomic-embed-text

DATABASE_URL=postgresql://postgres:postgres@db:5432/restaurant_db
```

### 2. Configure Ollama to accept external connections (Linux only)

By default, Ollama on Linux only listens on `127.0.0.1`. Docker containers can't reach it without this change:

```bash
sudo systemctl edit ollama
```

Add:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0"
```

Then restart:

```bash
sudo systemctl restart ollama
```

> **Mac/Windows**: skip this step — Docker Desktop handles it automatically.

### 3. Run

```bash
docker compose up --build
```

On first startup the app will:
1. Create all database tables
2. Chunk and embed `restaurant_info.txt` into pgvector (skipped on subsequent runs)

Then open **http://localhost:8000/docs** to access the Swagger UI.

---

## API

### `POST /api/chat`

Send a message to the agent.

```json
{
  "session_id": "user-123",
  "message": "What's on the menu?"
}
```

```json
{
  "session_id": "user-123",
  "response": "Here's what we have on the menu today: ..."
}
```

`session_id` identifies the conversation. Use any unique string — a UUID for Swagger testing, or a phone number for WhatsApp integration.

---

### `GET /api/orders`

Returns all orders for the restaurant owner, sorted newest first.

```json
[
  {
    "id": 1,
    "customer_name": "Yassine",
    "customer_phone": "+216 XX XXX XXX",
    "customer_address": "12 Rue de la République, Tunis",
    "items": [
      { "name": "Chicken Crispy Burger", "quantity": 1 },
      { "name": "Coke", "quantity": 1 }
    ],
    "total_price": 14.5,
    "status": "pending",
    "created_at": "2026-03-31T14:22:00"
  }
]
```

---

## Customizing the Restaurant

Edit `app/data/restaurant_info.txt` to match your restaurant — menu items, prices, opening hours, delivery zones, and payment methods. On next startup the knowledge base will be re-embedded automatically if the table is empty.

Example format:

```
Menu & Prices:
- Chicken Crispy Burger: 12.500 TND
- Coke: 2.500 TND
- Fresh Orange Juice: 4.000 TND

Opening Hours:
Monday - Saturday: 11:00 - 23:00
Sunday: 12:00 - 22:00

Delivery Zones:
- Tunis Centre, La Marsa, Carthage, Sidi Bou Said
- Minimum order: 15 TND
- Delivery fee: 3 TND
```

---

## Running Without Docker

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Make sure Ollama is running and PostgreSQL is up
uvicorn app.main:app --reload
```

---

## Roadmap

- [x] RAG knowledge base (menu, hours, delivery info)
- [x] Conversational order placement
- [x] Structured item parsing
- [x] Automatic price calculation
- [x] Docker support
- [ ] WhatsApp integration via Twilio
- [ ] Order status updates
- [ ] Multi-restaurant support