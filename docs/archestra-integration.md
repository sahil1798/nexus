# Archestra Integration Guide

NEXUS is designed to work with [Archestra](https://archestra.ai) — the enterprise-grade MCP platform for secure AI agent orchestration. While NEXUS handles intelligent pipeline discovery and execution, Archestra provides the production-ready infrastructure for running MCP servers securely at scale.

## Architecture

```
┌────────────────────────────────────────────────┐
│                  NEXUS Core                     │
│  ┌──────────┐  ┌───────────┐  ┌─────────────┐ │
│  │ Registry │  │ Capability│  │  Pipeline    │ │
│  │          │  │   Graph   │  │   Engine     │ │
│  └────┬─────┘  └─────┬─────┘  └──────┬──────┘ │
│       │              │               │         │
│       └──────────────┼───────────────┘         │
│                      │                         │
└──────────────────────┼─────────────────────────┘
                       │
              ┌────────▼────────┐
              │  Archestra MCP  │
              │    Gateway      │
              └────────┬────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼───┐    ┌────▼───┐    ┌────▼───┐
   │  MCP   │    │  MCP   │    │  MCP   │
   │Server 1│    │Server 2│    │Server 3│
   └────────┘    └────────┘    └────────┘
   (Archestra Private Registry)
```

## Quick Start

### 1. Start Archestra + NEXUS

```bash
# Clone the repo
git clone https://github.com/sahil1798/nexus.git
cd nexus

# Set your API keys
cp .env.example .env
# Edit .env with your GEMINI_API_KEY, OPENAI_API_KEY, SLACK_BOT_TOKEN

# Start both services
docker compose -f docker-compose.archestra.yml up -d
```

### 2. Access the Platforms

| Service | URL | Purpose |
|---------|-----|---------|
| Archestra UI | http://localhost:3000 | MCP Registry, Gateway, Security |
| NEXUS API | http://localhost:8000 | Intelligent MCP Broker API |

### 3. Register MCP Servers in Archestra

1. Open Archestra UI at `http://localhost:3000`
2. Go to **MCP Registry** → **Add New**
3. Register each NEXUS MCP server as a **Local MCP Server**:

| Server | Docker Image | Description |
|--------|-------------|-------------|
| `web-fetcher` | Use NEXUS container | Fetches and extracts web page content |
| `summarizer` | Use NEXUS container | AI-powered text summarization |
| `translator` | Use NEXUS container | Multi-language text translation |
| `sentiment-analyzer` | Use NEXUS container | Sentiment analysis with explanations |
| `slack-sender` | Use NEXUS container | Posts formatted messages to Slack |

### 4. Create an MCP Gateway

1. In Archestra UI, go to **MCP Gateways** → **Create New**
2. Assign all 5 NEXUS MCP server tools to the gateway
3. Copy the gateway endpoint URL and auth token
4. NEXUS can now route requests through Archestra's secure gateway

### 5. Configure NEXUS to Use Archestra Gateway

Set the `ARCHESTRA_URL` environment variable:

```bash
ARCHESTRA_URL=http://localhost:9000
```

## What Archestra Adds to NEXUS

| Feature | Without Archestra | With Archestra |
|---------|-------------------|----------------|
| **Security** | Direct stdio connections | Sandboxed execution, prompt injection prevention |
| **Observability** | Console logs | Prometheus metrics, OpenTelemetry traces, Grafana dashboards |
| **Cost Control** | No tracking | Per-agent cost monitoring, budget limits, dynamic model optimization |
| **Access Control** | Open access | OAuth 2.1, Bearer tokens, RBAC |
| **Scalability** | Single machine | Kubernetes-native orchestration |
| **Registry** | JSON state file | Private MCP registry with governance and version control |

## Why NEXUS + Archestra?

NEXUS solves the **intelligence problem** — automatically discovering how MCP servers can work together and orchestrating multi-step pipelines from natural language.

Archestra solves the **infrastructure problem** — providing secure, observable, and scalable runtime for MCP servers in production.

Together, they create a complete MCP orchestration stack:
- **NEXUS** = the brain (semantic discovery, capability graph, pipeline execution)
- **Archestra** = the body (security, observability, scaling, governance)
