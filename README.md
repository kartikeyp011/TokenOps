# TokenOps 🚀

![TokenOps Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-00a393)
![License](https://img.shields.io/badge/license-MIT-green)

TokenOps is an **Autonomous AI Cost Intelligence Agent**. It acts as a drop-in proxy and router for your LLM traffic, analyzing, routing, caching, and optimizing every request automatically to minimize spending without significantly compromising response quality.

---

## 🏗 Project Overview

TokenOps provides a seamless wrapper around providers like Google (Gemini) and Groq (LLaMA/Mixtral). Its core objective is to reduce your LLM bill by dynamically routing requests to the cheapest viable model, heavily caching repetitive queries, and enforcing strict organizational policies (e.g., rate limits and hard daily budgets).

## 📐 Architecture Diagram

```text
+-------------------+       +-----------------------+       +-------------------+
|      Client       | ----> |      TokenOps API     | ----> |   LLM Providers   |
| (Frontend/App)    |       |   (FastAPI Router)    |       |  (Google, Groq)   |
+-------------------+       +-----------------------+       +-------------------+
                                       |
                            +--------------------+
                            |   Policy Engine    | <-- Budget & Rate Limits
                            |   Routing Engine   | <-- Cost vs Quality Decisions
                            |   Semantic Cache   | <-- SHA256 Local Response Caching
                            +--------------------+
                                       |
                            +--------------------+
                            |  SQLite Database   |
                            | (Logs, Analytics)  |
                            +--------------------+
```

## 📁 Folder Structure

```text
TokenOps/
│
├── backend/                  # Fast API Backend System
│   ├── app/
│   │   ├── api/              # Route controllers (Dashboard, Usage, Policies, etc.)
│   │   ├── core/             # Core engines: Analyzer, Cache, Router, Policy, Estimator
│   │   ├── db/               # SQLite database setup & connection
│   │   ├── models/           # SQLAlchemy DB models definition
│   │   ├── services/         # External integrations (e.g., Modular LLM Service)
│   │   ├── utils/            # Helper functions and database seeders
│   │   ├── config.py         # Global App Configurations using pydantic
│   │   ├── dependencies.py   # FastAPI Dependencies (e.g. Auth)
│   │   └── main.py           # Application Entry Point
│   ├── run_server.py         # Server startup script
│   └── requirements.txt      # Python dependencies
│
├── frontend/                 # Static Vanilla Web Dashboard
│   ├── assets/               # CSS & JS logic for the dashboard
│   ├── components/           # Reusable HTML snippets (handled purely in JS)
│   └── *.html                # Prebuilt interface pages
│
└── .gitignore                # Ignored files definition
```

---

## 💻 Tech Stack

- **Backend:** Python 3.10+, FastAPI, SQLAlchemy, Uvicorn, Pydantic
- **Frontend:** Vanilla JavaScript, HTML5, CSS3/Tailwind-like utility classes
- **Database:** SQLite (Default, extremely fast & scalable for single-process architectures)
- **AI Integrations:** `google-generativeai`, `groq` SDKs

---

## 🛠 Setup & Installation (Windows CMD)

1. **Clone the repository:**
   ```cmd
   git clone https://github.com/your-username/TokenOps.git
   cd TokenOps\backend
   ```

2. **Create and activate a virtual environment:**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```cmd
   pip install -r requirements.txt
   ```

4. **Environment Setup:**
   Create a `.env` file in the `backend/` directory from the template:
   ```cmd
   copy .env.example .env
   ```

   Fill in the `.env` configuration (see Environment Variables).

---

## 🔐 Environment Variables

TokensOps relies on `.env` configuration variables under `backend/.env`.

```ini
# --- API Keys ---
GEMINI_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here
TOKENTAMER_API_KEY=tokentamer-secret-key-change-me

# --- Database ---
DATABASE_URL=sqlite:///./tokentamer.db

# --- Server Configuration ---
HOST=127.0.0.1
PORT=8000
DEBUG=True

# --- Policy Defaults ---
MAX_TOKENS_PER_REQUEST=4096
DAILY_BUDGET_CAP_USD=5.0
RATE_LIMIT_RPM=50
ROUTING_STRATEGY=hybrid

# --- Cache ---
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE=500
```

---

## 🚀 How to Run

### Backend
Start the FastAPI server:
```cmd
cd TokenOps\backend
venv\Scripts\activate
python run_server.py
```
*The server will start on `http://127.0.0.1:8000`. Swagger API documentation is available at `http://127.0.0.1:8000/docs`.*

### Frontend Dashboard
Simply open `TokenOps/frontend/index.html` in your web browser. No compilation required.

---

## 🌐 API Endpoints

All endpoints require the `X-API-Key` header with your `TOKENTAMER_API_KEY` value.

### 1. The Proxy Endpoint
Drop-in replacement for OpenAI-compatible tools.

**`POST /v1/chat/completions`**

**Request:**
```json
{
    "model": "llama3-8b-8192", // Optional: The router will override this if deemed excessive
    "messages": [
        {"role": "user", "content": "What is the capital of France?"}
    ],
    "max_tokens": 1024
}
```

**Response (Success):**
```json
{
    "content": "The capital of France is Paris.",
    "model": "llama3-8b-8192",
    "provider": "groq",
    "prompt_tokens": 8,
    "completion_tokens": 8,
    "mock": false,
    "latency_ms": 250
}
```

### 2. Dashboard KPIs
**`GET /api/dashboard`**
Returns aggregations of requests, costs, and current budget limits for your UI.

### 3. Usage Analytics
**`GET /api/usage/cost_by_model`**
**`GET /api/usage/daily`**
Monitor the costs tracked separately across various models dynamically.

### 4. Fetch / Update Policies
**`GET /api/policies`**
**`PUT /api/policies/{name}`**
Updates the live configuration rules for TokenOps without requiring a server reboot!

**Request (PUT):**
```json
{
    "value": "10.0"
}
```
*Modifies constraints like DB variables in runtime.*

---

## 🧠 Core Systems

### Routing Engine (`router.py`)
TokenOps applies a "Smart Hybrid Routing Strategy":
1. **Pass-Through:** If the client requests an allowed model, we honor the request.
2. **Budget Fallback:** If today's spend achieves >= 80% of the daily budget cap, TokenOps reroutes all traffic to standard/cheapest models (e.g., LLaMA 3 8B).
3. **Quality Recognition:** Analyzes prompts for complexity (e.g. coding queries). Complex tasks are safely routed to higher-tier models (e.g., Gemini 1.5 Pro).
4. **Efficiency Defaults:** Standard, simple conversational requests route entirely to the most cost-effective tier seamlessly.

### Cost Estimation Logic (`cost_estimator.py`)
Relies strictly on an internal dynamic pricing table. Cost prediction calculates using `prompt_tokens` and a conservative `completion_tokens` estimator ratio before execution to preemptively flag potentially expensive queries.

### Policy Engine Rules (`policy_engine.py`)
Config-driven rules to secure your wallet:
- **Token Limits:** Pre-rejects prompts that exceed `MAX_TOKENS_PER_REQUEST`.
- **Global Rate Limits:** Throttles requests if volume breaches `RATE_LIMIT_RPM` over a 60-second slice.
- **Allowed Models List:** Halts unregistered model attempts immediately.
- **Daily Budget Limit:** Fails the transaction instantly if the query cost prediction exceeds `DAILY_BUDGET_CAP_USD`.

### Semantic Cache (`cache.py`)
A fast, in-memory SHA256 semantic caching construct (ideal for Uvicorn single processes). 
TokenOps strips empty whitespace and maps exact matching user prompts/models into its cache dictionary.
Saves absolute 100% of LLM cost if a hit matches (Evicts eldest entries routinely per `CACHE_MAX_SIZE`).

### 🤖 Mock vs. Real LLM Mode
You do NOT need API keys to develop or test this repository! Built-in Mock Mode:
The `LLM_Service` dynamically detects API availability `is_available()`. If you leave your `.env` empty or omit the exact service API key, TokenOps will gracefully respond with "Mock Responses", logging simulated latencies, fake API outputs, and synthetic token utilizations to the local database, allowing you to test traffic at 0 cost!

---

## 🤝 Contribution Guide

Contributions are always welcome.

1. **Fork the repository** tracking `main`.
2. **Create a branch** for your feature (`git checkout -b feat/my-new-feature`).
3. **Write Python 3.10+ typed code.** Please keep functions inside `backend/app` compartmentalized. Don't bleed responsibilities (`core` files should not depend on `api` routes directly).
4. **Commit the changes** with clear descriptions (`git commit -m "feat: Add Anthropic LLM support module"`).
5. **Open a Pull Request**! Ensure there are no lingering testing or log prints in production files.

*Let's conquer LLM pricing together!*
