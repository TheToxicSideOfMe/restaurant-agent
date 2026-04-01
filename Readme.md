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
- 📱 **Telegram bot** — customers chat directly via Telegram, no app or browser needed
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
| Messaging | Telegram Bot API |

---

## Architecture

```
Customer message (Telegram or HTTP)
         │
         ▼
   Telegram Bot / POST /api/chat
         │
         ├── Load conversation history from DB (keyed by chat_id or session_id)
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
│   ├── main.py                        # FastAPI app, lifespan startup, Telegram polling
│   ├── database.py                    # SQLAlchemy engine, session, pgvector setup
│   ├── models/
│   │   ├── order.py                   # Order table
│   │   ├── conversation.py            # Conversation history table
│   │   └── knowledge_chunk.py        # pgvector embeddings table
│   ├── api/
│   │   ├── chat.py                    # POST /api/chat
│   │   ├── orders.py                  # GET /api/orders
│   │   └── telegram.py               # Telegram bot handler
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
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

Pull the embedding model if you haven't already:

```bash
ollama pull nomic-embed-text
```

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. Copy the API token BotFather gives you — it's free and instant

### 2. Configure environment

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

TELEGRAM_BOT_TOKEN=your_telegram_token_here
```

### 3. Configure Ollama to accept external connections (Linux only)

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

### 4. Run

```bash
docker compose up --build
```

On first startup the app will:
1. Create all database tables
2. Chunk and embed `restaurant_info.txt` into pgvector (skipped on subsequent runs)
3. Start the Telegram bot polling in the background

Open **http://localhost:8000/docs** to test via Swagger, or message your bot directly on Telegram.

---

## API

### `POST /api/chat`

Send a message to the agent programmatically.

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

`session_id` identifies the conversation. Use any unique string for Swagger testing. The Telegram bot uses each user's `chat_id` automatically.

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

## Telegram Bot

The Telegram bot runs automatically when the server starts — no separate process needed. Each user's Telegram `chat_id` is used as their `session_id`, so conversation memory is persistent per user across multiple messages.

The bot shares the exact same agent, RAG pipeline, and order logic as the HTTP API — zero duplicate code.

To test: find your bot on Telegram by the username you chose in BotFather and send it a message.

---

## Customizing for Your Business

Two files control the entire behavior of the agent:

**1. `app/data/restaurant_info.txt`** — the knowledge base. Replace this with your restaurant's actual menu, prices, hours, delivery zones, and payment methods. The agent answers all customer questions from this file.

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

**2. `SYSTEM_PROMPT` in `app/agent/graph.py`** — controls the agent's personality, language, and behavior rules. Change this to match your brand tone or switch the response language entirely.

After editing `restaurant_info.txt`, clear the `knowledge_chunks` table and restart — the data will be re-embedded automatically.

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
- [x] Telegram bot integration
- [x] Docker support
- [ ] Order status updates sent to customer via Telegram
- [ ] Admin dashboard UI
- [ ] Multi-restaurant support