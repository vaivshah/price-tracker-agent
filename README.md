# Price Tracker Agent

A Python-based WhatsApp chatbot powered by the **NemoClaw/OpenClaw** autonomous agent architecture. The agent acts as a personal shopping assistant capable of tracking product prices, finding the cheapest options online, and fetching historical pricing data (30, 90, 180 days).

## Features
- **WhatsApp Integration**: Interact seamlessly with the agent via WhatsApp.
- **Product Research**: Send a product link (Amazon, Walmart, eBay) and the agent autonomously checks for the cheapest exact matches across the web.
- **Historical Analysis**: Fetches long-term price graphs to let you know if you are getting a good deal.
- **Future Support (Planned)**: Periodic price tracking subscriptions, in-depth alternative reporting, and secure, dynamically generated HTML/PDF reports.

## Architecture

- **App Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Agent Orchestration**: NemoClaw/OpenClaw (OOTB Web Scraping and WhatsApp handling)
- **Deployment**: Docker Compose

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
   Copy the example environment file and fill in your API keys (WhatsApp token, OpenAI/NemoClaw keys).
   ```bash
   cp .env.example .env
   ```

3. **Start the Services:**
   Run the application and the PostgreSQL database via Docker.
   ```bash
   docker compose up -d --build
   ```

### Connecting to WhatsApp (Local Testing)
1. Expose your local port 8000 using ngrok:
   ```bash
   ngrok http 8000
   ```
2. Copy the generated `https://...ngrok.app` URL.
3. In your WhatsApp provider's webhook settings (e.g., Twilio Sandbox), set the webhook URL to:
   `https://...ngrok.app/webhook/whatsapp`

## Monitoring & Telemetry

The project comes with an out-of-the-box monitoring stack configured in `docker-compose.yml`. When you run `docker compose up`, the following services are started alongside the web app and database:

- **Prometheus** (Port `9090`): Automatically scrapes performance metrics (request rates, latency, errors) from the FastAPI app.
- **Loki** (Port `3100`): A highly efficient log aggregation system. The Python app pushes logs directly to Loki over HTTP.
- **Grafana** (Port `3000`): The visual dashboard that ties it all together.

### How to View Logs and Telemetry

1. Open your browser and navigate to [http://localhost:3000](http://localhost:3000).
2. Log in with the default credentials (`admin` / `admin`).
3. Navigate to **Explore** (compass icon on the left sidebar).
   - **For Logs:** Select `Loki` from the data source dropdown at the top left. Use the Label filters or run the query `{application="price_tracker_agent"}` to view real-time logs.
   - **For Telemetry:** Select `Prometheus` from the data source dropdown. You can query metrics like `http_requests_total` or `http_request_duration_seconds`.

## Project Structure
- `src/main.py`: FastAPI server and webhook entry point.
- `src/agent.py`: NemoClaw agent initialization and behavior logic.
- `src/database.py` & `src/models.py`: PostgreSQL connection and SQLAlchemy schema.
- `src/scheduler.py`: Background job scheduling for periodic price tracking.
- `src/reporting.py` & `src/templates/`: Logic for rendering and serving dynamic HTML reports.
- `src/logger.py` & `monitoring/`: Central logging configuration and Grafana stack config files.
