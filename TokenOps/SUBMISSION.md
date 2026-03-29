# TokenTamer (TokenOps) — Autonomous AI Cost Intelligence Agent

## Problem Statement
The proliferation of Large Language Models (LLMs) has led to skyrocketing API costs for developers and enterprises. Unpredictable user behavior, expensive high-tier models being used for simple tasks, and repeated queries draining tokens all contribute to "bill shock." There is a critical need for an intelligent middleware that can manage, route, and reduce LLM traffic costs without compromising the quality of the applications relying on these models.

## Solution Overview
TokenTamer (code-named TokenOps) is a drop-in proxy and intelligent router for LLM traffic. By sitting between the client application and the LLM providers, TokenTamer automatically analyzes every prompt, queries an in-memory semantic cache, and dynamically routes the request to the most cost-effective model suited for the task's complexity. It completely secures your wallet through strict organizational policies, rate limiting, and daily budget caps, ultimately delivering significant cost savings on autopilot.

## System Architecture

The architecture is built for ultra-fast, single-process execution (via FastAPI and SQLite), making it easily deployable and highly performant.

```text
+-------------------+       +-----------------------+       +-------------------+
|      Client       | ----> |   TokenTamer API      | ----> |   LLM Providers   |
| (Frontend/App)    |       |   (FastAPI Proxy)     |       |  (Google, Groq)   |
+-------------------+       +-----------------------+       +-------------------+
                                       |
                            +--------------------+
                            |   Policy Engine    | <-- Budget, Rate, Token Limits
                            |   Routing Engine   | <-- Cost vs Quality Decisions
                            |   Semantic Cache   | <-- Local SHA-256 Caching
                            +--------------------+
                                       |
                            +--------------------+
                            |  SQLite Database   | <-- Logs, Analytics, Costs
                            +--------------------+
```

## Core Features
| Feature | Description |
|---|---|
| **Intelligent Routing** | Automatically routes prompts to simple or advanced models based on heuristic analysis. |
| **Strict Policy Engine** | Configurable daily budgets, token limits, and rate limits updated at runtime. |
| **Semantic Caching** | Predictable SHA-256 local caching to answer repeated queries instantly at $0 cost. |
| **Cost Estimator** | Pre-calculates potential costs before dispatching queries to avoid exceeding caps. |
| **Comprehensive Audit Logging**| Stores all requests, latencies, and token counts in a local SQLite database. |
| **Dashboard API** | A rich set of APIs to visualize usage, cost savings, and budget thresholds. |
| **Mock Mode** | 100% free offline development mode using simulated model responses. |

## Technical Implementation

### 1. Analyzer (`analyzer.py`)
Classifies prompts before routing decisions are made using lightweight heuristics instead of external LLM calls. The analyzer estimates the token count and identifies keywords (e.g., "code", "debug", "explain") to determine the task's complexity (`simple`, `medium`, `complex`) and type (`coding`, `explanation`, `creative`, `general`).

### 2. Router (`router.py`)
The decision-making core. It consumes the output of the Analyzer, current budget data from the Database, and Policy Rules to select the ideal model for the payload on a continuous spectrum of "Cheapest Viable" to "Premium Quality". 

### 3. Policy Engine (`policy_engine.py`)
A config and database-driven defense mechanism. It sequentially checks:
- **Token Limits:** Pre-rejects excessively large prompts.
- **Rate Limits:** Throttles excessive RPM volume.
- **Allowed Models:** Stops unauthorized model requests.
- **Budget Cap:** Instant transactional block if the predicted cost will push today's spend over the daily limit.

### 4. Semantic Cache (`cache.py`)
An ultra-fast, in-memory SHA-256 semantic cache. It strips whitespace and creates a deterministic hash of the prompt and model name. Cache hits return instantly with a resulting 100% cost saving for the transaction. It leverages TTL and `max_size` eviction strategies.

### 5. LLM Service (`llm_service.py`)
A modular registry pattern that abstracts the provider logic. A `BaseLLMProvider` interface is implemented by `GeminiProvider` and `GroqProvider`. New providers (like OpenAI or Anthropic) can be added securely by implementing `call()` and `is_available()`.

## Routing Intelligence
TokenTamer utilizes a "Smart Hybrid Routing Strategy" evaluated sequentially:

1. **Pass-Through:** If a valid client explicitly requests an allowed model, the router honors the decision to maintain predictability.
2. **Budget Fallback:** If daily spend exceeds 80% of the daily limit, the router heavily penalizes premium models and forces all traffic to the cheapest available model.
3. **Quality Recognition:** If the Analyzer detects a complex task (e.g., coding, system architecture), the router dynamically overrides the default choice and triggers the highest quality model (e.g., Gemini 1.5 Pro).
4. **Efficiency Defaults:** For simple queries, conversational chit-chat, or basic tasks, the router seamlessly delegates to the cheapest tier (e.g., LLaMA 3 8B).

## Cost Savings Mechanism
Savings are calculated dynamically per request in the `cost_estimator.py` module. 
TokenTamer checks the internal static pricing table ($/1k tokens). It estimates input and output tokens for both the requested tier and the routed tier. 
If an expensive prompt destined for Gemini 1.5 Pro is successfully answered by the Semantic Cache or safely rerouted to LLaMA 3 8b, the exact differential (`Cost_Requested - Cost_Used`) is logged as absolute `Cost Saved`.

## API Reference

### Proxy Endpoint
```http
POST /v1/chat/completions
Header: X-API-Key: <secret>
```
**Payload:**
```json
{
  "model": "llama3-8b-8192",
  "messages": [{"role": "user", "content": "Hello, world!"}],
  "max_tokens": 1024
}
```
**Response:**
```json
{
  "content": "Hello! How can I help you today?",
  "model": "llama3-8b-8192",
  "provider": "groq",
  "prompt_tokens": 14,
  "completion_tokens": 9,
  "mock": false,
  "latency_ms": 311
}
```

### Dashboard & Analytics API
- `GET /api/dashboard` - Returns system KPIs (Total Requests, Savings, Budgets).
- `GET /api/usage/cost_by_model` - Grouped analytics on model expenditure.
- `GET /api/usage/daily` - Time-series data of spend distribution.

### Policy Management
- `GET /api/policies` - View current active limits.
- `PUT /api/policies/{name}` - Update runtime policy config directly (e.g., budget caps).

## Supported LLM Providers
The application natively supports:
- **Google Gemini** (`gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-2.0-flash`)
- **Groq** (`llama3-8b-8192`, `llama3-70b-8192`, `mixtral-8x7b-32768`)

*Extensibility:* The system employs an `LLMServiceRegistry` structural pattern. Developers can integrate arbitrary providers by extending `BaseLLMProvider` and defining a `.call()` async method.

## Mock Mode
Developing AI applications can be expensive. TokenTamer ships with a zero-cost local environment. 
If API keys in the `.env` are excluded or invalid, the `.is_available()` check automatically falls back into **Mock Mode**. 
The system fakes latency, injects synthetic token counts, processes DB metrics, and returns standard mock text strings, completely mirroring a live environment without triggering API limits or expenditures.

## Future Roadmap
- **Redis Cache Backend:** Migrate the in-memory cache to Redis for multi-worker containerized deployments.
- **Provider Load Balancing:** Add multiple API keys per provider to gracefully round-robin requests around hardware rate limits.
- **Automated Fallbacks:** Immediately retry requests on alternative providers if Groq/Gemini returns an outage `HTTP 503`.
- **Advanced Embeddings Cache:** Use vector databases (Pinecone/Milvus) instead of strict SHA-256 to allow fuzzy-matching for semantic caching.

## Setup Instructions

1. **Clone the Repository:**
   ```bash
   git clone <repository_url>
   cd TokenOps/backend
   ```
2. **Environment Activation:**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
3. **Environment Setup:**
   ```bash
   cp .env.example .env
   ```
   *Note: Populate `GEMINI_API_KEY` and `GROQ_API_KEY`. Leave them blank to test Mock Mode.*
4. **Boot the Server:**
   ```bash
   python run_server.py
   ```
5. **Access the Interfaces:**
   - Swagger / API Docs: `http://localhost:8000/docs`
   - Analytics Dashboard: Open `TokenOps/frontend/index.html` in your web browser.
