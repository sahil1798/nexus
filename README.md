<div align="center">

# 🔗 NEXUS — The Intelligent MCP Broker

**MCP servers are powerful alone. NEXUS makes them powerful _together_.**

AI-powered orchestration platform that automatically discovers, connects, and chains MCP servers into intelligent pipelines — built for [Archestra](https://archestra.ai).

[![Live Demo](https://img.shields.io/badge/Live%20Demo-nexus--amzw.vercel.app-blue?style=for-the-badge)](https://nexus-amzw.vercel.app/)
[![Built for Archestra](https://img.shields.io/badge/Built%20for-Archestra-purple?style=for-the-badge)](https://archestra.ai)
[![Python](https://img.shields.io/badge/Python-3.12-green?style=for-the-badge)](https://python.org)
[![MCP](https://img.shields.io/badge/Protocol-MCP-orange?style=for-the-badge)](https://modelcontextprotocol.io)

</div>

---

## 🚨 The Problem

MCP servers are powerful independently — but they exist as **isolated islands**. A web-fetcher doesn't know about a summarizer. A translator can't find a sentiment analyzer. Building multi-tool workflows requires manual coding, hard-coded pipelines, and deep knowledge of each server's API.

## ✨ The Solution

NEXUS is an **intelligent broker** that sits between your MCP servers and your requests. It:

1. **Reads server metadata** using AI to build semantic profiles
2. **Discovers connections** between tools via vector embeddings (O(N) complexity)
3. **Plans pipelines** from natural language requests
4. **Executes workflows** with automatic data translation between incompatible schemas

> _"Fetch CNN.com, summarize it, analyze sentiment, and post to #team-updates on Slack"_
>
> → NEXUS discovers the pipeline, chains 4 servers, translates data between them, and executes — all automatically.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      NEXUS Core                          │
│                                                          │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────┐ │
│  │   Registry   │  │  Capability    │  │   Pipeline   │ │
│  │  + Semantic   │  │    Graph       │  │   Engine     │ │
│  │   Profiler   │  │ (Embeddings)   │  │ (Discovery + │ │
│  │              │  │                │  │  Execution)  │ │
│  └──────┬───────┘  └───────┬────────┘  └──────┬───────┘ │
│         │                  │                   │         │
│         └──────────────────┼───────────────────┘         │
│                            │                             │
│                    ┌───────▼───────┐                     │
│                    │  FastAPI REST │                     │
│                    │      API      │                     │
│                    └───────┬───────┘                     │
└────────────────────────────┼─────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Archestra     │
                    │  MCP Gateway    │
                    │  (Security +    │
                    │  Observability) │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐     ┌─────▼─────┐     ┌─────▼─────┐
    │   web-    │     │ summar-   │     │  slack-   │
    │  fetcher  │     │  izer     │     │  sender   │
    └───────────┘     └───────────┘     └───────────┘
    ┌───────────┐     ┌───────────┐
    │translator │     │ sentiment │
    │           │     │ analyzer  │
    └───────────┘     └───────────┘
```

---

## 🔑 Key Features

| Feature | Description |
|---------|-------------|
| **Semantic Discovery** | AI reads server metadata and understands what each tool truly does |
| **Auto-Connection** | Discovers non-obvious tool chains by analyzing input/output schemas via vector embeddings |
| **Schema Translation** | Automatically bridges incompatible data formats between servers |
| **Pipeline Execution** | Runs multi-step workflows with intelligent data aggregation |
| **Persistent Memory** | Capability graph survives restarts, stored in SQLite |
| **REST API** | Clean FastAPI interface with 10+ endpoints |
| **React Dashboard** | 3D graph visualization, pipeline execution, real-time monitoring |

---

## 🏎️ Archestra Integration

NEXUS is built to work with [Archestra](https://archestra.ai) — the enterprise-grade MCP platform. While NEXUS handles the **intelligence layer** (discovery, graphing, pipeline planning), Archestra provides the **infrastructure layer** (security, observability, scaling).

| Feature | NEXUS Only | NEXUS + Archestra |
|---------|-----------|-------------------|
| **Security** | Direct stdio | Sandboxed execution, prompt injection prevention |
| **Observability** | Console logs | Prometheus, OpenTelemetry, Grafana |
| **Cost Control** | No tracking | Per-agent cost monitoring, budget limits |
| **Access Control** | Open | OAuth 2.1, Bearer tokens, RBAC |
| **Scalability** | Single machine | Kubernetes-native orchestration |
| **Registry** | JSON state file | Private MCP registry with governance |

### Quick Start with Archestra

```bash
# Start NEXUS + Archestra together
docker compose -f docker-compose.archestra.yml up -d

# Access:
#   Archestra UI → http://localhost:3000
#   NEXUS API   → http://localhost:8000
```

See the full [Archestra Integration Guide](docs/archestra-integration.md) for step-by-step setup.

---

## 🚀 Quick Start (Standalone)

### Prerequisites
- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- Gemini API key

### Setup

```bash
# Clone
git clone https://github.com/sahil1798/nexus.git
cd nexus

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env: add GEMINI_API_KEY, OPENAI_API_KEY (optional), SLACK_BOT_TOKEN (optional)

# Start the API server
uv run python main.py
```

The API will be available at `http://localhost:8000`.

### Run the Demo

```bash
# Register servers and execute a full pipeline
uv run python demo/full_demo.py
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/` | Health check |
| `GET` | `/api/status` | System statistics |
| `GET` | `/api/servers` | List all registered MCP servers |
| `POST` | `/api/servers/register` | Register a new MCP server |
| `DELETE` | `/api/servers/{name}` | Unregister a server |
| `GET` | `/api/graph` | Get the capability graph |
| `POST` | `/api/graph/rebuild` | Rebuild the graph |
| `POST` | `/api/discover` | Plan a pipeline (no execution) |
| `POST` | `/api/execute` | Discover and execute a pipeline |
| `GET` | `/api/history` | Pipeline execution history |

### Example: Execute a Pipeline

```bash
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{
    "request": "Fetch https://example.com, summarize it, and post to #team-updates",
    "url": "https://example.com",
    "channel": "#team-updates"
  }'
```

---

## 🔧 MCP Servers Included

| Server | Tools | Description |
|--------|-------|-------------|
| **web-fetcher** | `fetch_url` | Fetches and extracts clean text from web pages |
| **summarizer** | `summarize_text` | AI-powered text summarization with key points |
| **translator** | `translate_text` | Multi-language text translation |
| **sentiment-analyzer** | `analyze_sentiment` | Sentiment analysis with confidence and explanation |
| **slack-sender** | `send_slack_message` | Posts formatted messages to Slack channels |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI, Python 3.12, Pydantic |
| **AI/LLM** | Google Gemini 2.0 Flash, OpenAI (embeddings) |
| **MCP** | Model Context Protocol (stdio transport) |
| **Database** | SQLite (persistent capability graph) |
| **Frontend** | React, Framer Motion, Lucide Icons, shadcn/ui |
| **Infrastructure** | Docker, Archestra, Render (backend), Vercel (frontend) |

---

## 📁 Project Structure

```
nexus/
├── nexus_core/           # Core engine
│   ├── api.py            # FastAPI REST endpoints
│   ├── registry.py       # Server registration + profiling
│   ├── graph.py          # Capability graph (embeddings)
│   ├── discovery.py      # Pipeline discovery engine
│   ├── executor.py       # Pipeline execution engine
│   ├── translator.py     # Schema translation
│   ├── embeddings.py     # Vector embedding index
│   ├── database.py       # SQLite persistence
│   ├── models.py         # Pydantic data models
│   ├── config.py         # Gemini client config
│   └── profiler.py       # Semantic profiler
├── servers/              # MCP servers
│   ├── web-fetcher/
│   ├── summarizer/
│   ├── translator/
│   ├── sentiment-analyzer/
│   └── slack-sender/
├── ui/                   # React frontend
│   └── src/
│       ├── pages/        # Landing, Dashboard, Docs
│       └── components/   # Graph3D, PipelinesTab, etc.
├── demo/                 # Demo scripts and tests
├── docs/                 # Documentation
│   └── archestra-integration.md
├── docker-compose.archestra.yml
├── Dockerfile
├── main.py
└── pyproject.toml
```

---

## 🌐 Live Demo

**Frontend:** [nexus-amzw.vercel.app](https://nexus-amzw.vercel.app)

---

## 📄 License

MIT

---

<div align="center">

**Built with ❤️ for the [2 Fast 2 MCP](https://www.wemakedevs.org/hackathons/2fast2mcp) Hackathon**

*NEXUS = the brain 🧠 · Archestra = the body 🏗️*

</div>
