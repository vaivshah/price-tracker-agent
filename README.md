# Price Tracker Agent

A Python-based autonomous shopping assistant powered by **NemoClaw/OpenClaw** agent architecture. Users interact via WhatsApp (with Telegram, Email, and Web planned) to check prices, set up tracking, research products, and discover budget-friendly alternatives.

## Features

- **Multi-Channel Input** (Strategy Pattern): WhatsApp today, Telegram/Email/Web tomorrow — each channel is a plug-in adapter.
- **Price Check**: Send a product link and the agent scrapes the current price.
- **Price Tracking**: Monitor a product's price periodically (6h–14d) with configurable alerts.
- **Product Research**: Aggregated reviews and opinions from across the web, delivered as an HTML report.
- **Alternative Suggestions**: Budget-aware product alternatives with comparison reports.
- **Job Management**: Review, cancel, or extend your active tracking jobs.
- **Report Serving**: Beautiful, time-limited HTML reports served via unique links (24h default expiry).

## Architecture

| Component | Technology |
|---|---|
| App Framework | FastAPI (app factory pattern) |
| Database | PostgreSQL + SQLAlchemy ORM |
| Agent Orchestration | NemoClaw/OpenClaw (OOTB Web Scraping) |
| Background Jobs | APScheduler |
| Telemetry | Prometheus (custom + auto-instrumented) |
| Logging | Loki (direct HTTP push) |
| Dashboards | Grafana (pre-configured datasources) |
| Deployment | Docker Compose |

## Getting Started

### Prerequisites
- Docker & Docker Compose
- `ngrok` (for local webhook testing)
- Python 3.11+ (if running without Docker)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/vaivshah/price-tracker-agent.git
   cd price-tracker-agent
   ```

2. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   ```
   Fill in: `DATABASE_URL`, `WHATSAPP_TOKEN`, `NEMOCLAW_API_KEY`, `LOKI_URL`.

3. **Start the Services:**
   ```bash
   docker compose up -d --build
   ```
   This starts the web app, PostgreSQL, Prometheus, Loki, and Grafana.

### Connecting to WhatsApp (Local Testing)
1. Expose port 8000 via ngrok:
   ```bash
   ngrok http 8000
   ```
2. Set your WhatsApp provider's webhook URL to:
   `https://<ngrok-url>/webhook/whatsapp`

## Monitoring & Telemetry

The project ships with a full observability stack in `docker-compose.yml`:

| Service | Port | Purpose |
|---|---|---|
| **Prometheus** | `9090` | Scrapes HTTP + custom business metrics |
| **Loki** | `3100` | Log aggregation (direct push from Python) |
| **Grafana** | `3000` | Dashboards for logs and metrics |

### Custom Business Metrics (Prometheus)

| Metric | Type | Labels | Description |
|---|---|---|---|
| `messages_received_total` | Counter | `channel` | Inbound messages by channel |
| `messages_sent_total` | Counter | `channel` | Outbound messages by channel |
| `intents_classified_total` | Counter | `intent` | How often each intent is detected |
| `service_executions_total` | Counter | `service`, `status` | Service calls (success/error) |
| `service_duration_seconds` | Histogram | `service` | Wall-clock time per service |
| `active_tracking_jobs` | Gauge | — | Current active tracking jobs |
| `reports_generated_total` | Counter | `report_type` | Reports created by type |

### How to View

1. Open [http://localhost:3000](http://localhost:3000) (login: `admin` / `admin`).
2. **Logs**: Explore → Loki → `{application="price_tracker_agent"}`
3. **Metrics**: Explore → Prometheus → query any metric above.

## Project Structure

```
src/
├── main.py                    # App factory — wires routers, telemetry, services
├── scheduler.py               # Background crons (price check, report cleanup)
│
├── core/                      # Cross-cutting concerns
│   ├── config.py              # Centralised env config (no hardcoding!)
│   ├── logger.py              # Loki logging setup
│   └── telemetry.py           # Custom Prometheus counters
│
├── channels/                  # Input channel adapters (Strategy Pattern)
│   ├── base.py                # Abstract Channel + IncomingMessage
│   └── whatsapp.py            # WhatsApp webhook + response adapter
│
├── services/                  # Agent capabilities (Service Layer)
│   ├── base.py                # Abstract BaseService
│   ├── orchestrator.py        # Intent classification + service dispatch
│   ├── price_check.py         # One-time price lookup
│   ├── tracking.py            # Periodic price monitoring
│   ├── research.py            # Product research & reviews
│   ├── alternatives.py        # Budget-based alternative suggestions
│   └── review.py              # Manage active tracking jobs
│
├── database/                  # Data layer
│   ├── session.py             # Engine, SessionLocal, get_db
│   ├── models.py              # SQLAlchemy ORM models
│   └── store.py               # All DB operations (ACID compliant)
│
└── reports/                   # Report generation & serving
    ├── renderer.py            # Jinja2 template rendering
    ├── server.py              # Report HTTP routes + link generation
    └── templates/             # HTML templates (price_history, research, etc.)
```

## Design Principles

- **SOLID**: Single Responsibility per module, Open/Closed via Strategy + Service patterns, Liskov-substitutable channels/services, Interface Segregation on abstractions, Dependency Inversion via ABCs.
- **ACID**: Every DB write in `store.py` uses try/except with `db.rollback()`. Race conditions handled with `IntegrityError` catch + re-query.
- **No Hardcoding**: All config via `src/core/config.py` and environment variables.
- **No Mid-File Imports**: All imports at the top of every file.

---

## Roadmap

> Items roughly ordered by priority. Check the box when complete.

### Phase 1 — Core Agent Implementation
- [ ] **Implement NemoClaw/OpenClaw integration** in each service (`price_check.py`, `tracking.py`, `research.py`, `alternatives.py`). Wire up actual web scraping skills for price extraction, review aggregation, and alternative discovery.
- [ ] **LLM-based intent routing** — Replace keyword matching in `orchestrator.py` with an LLM/Agent/CLAW-based classifier that understands natural language intent, context, and multi-step commands.

### Phase 2 — Conversation & Context
- [ ] **Conversation memory** — The `ConversationLog` model exists but isn't used for context yet. Load recent history in the orchestrator before classifying intent so users can say "track *it*" and we know what "it" refers to.
- [ ] **Multi-turn flows** — Some actions (e.g., setting up tracking) require multiple exchanges (URL → interval → duration → confirm). Implement a state machine or agent-managed flow for these.

### Phase 3 — Robustness & Safety
- [ ] **Rate limiting per user** — Cap active tracking jobs (e.g., 10 per user), message frequency (e.g., 1/sec), and report generation. Configurable via `core/config.py`.
- [ ] **Webhook idempotency** — WhatsApp/Telegram can send duplicate events. Deduplicate using `message_id` from `IncomingMessage` before processing.
- [ ] **Notification preferences** — Allow users to choose when they get alerts: `every_check`, `price_drop`, or `target_reached` (fields already exist on `TrackingJob`).

### Phase 4 — Data & Reports
- [ ] **Schema migrations with Alembic** — Replace `Base.metadata.create_all()` with proper versioned migrations for safe production deployments.
- [ ] **Expired report cleanup** — The scheduler cron exists but needs to actually delete orphaned HTML files from disk and mark DB records as expired.
- [ ] **Rich report templates** — Build `price_history.html` (with Chart.js price graphs), `research.html` (pros/cons/ratings), and `alternatives.html` (comparison table).

### Phase 5 — Additional Channels
- [ ] **Telegram adapter** — Create `channels/telegram.py` with Telegram Bot API integration.
- [ ] **Email adapter** — Create `channels/email.py` for inbound email parsing (e.g., via SendGrid Inbound Parse).
- [ ] **Web dashboard** — Create `channels/web.py` as a REST/WebSocket API for a dedicated frontend.

### Phase 6 — Scale & Infrastructure
- [ ] **Async task queue** — Migrate from `BackgroundTasks` to **Celery + Redis** or **ARQ** for heavy operations (research, alternatives) that may take 30+ seconds.
- [ ] **Alerting** — Configure Grafana alerts for error rate spikes, service latency thresholds, and scheduler failures.
- [ ] **CI/CD pipeline** — Automated testing, linting, and Docker image builds on push.
