import logging
import logging_loki
from .config import config

def setup_logging():
    """Configure global logging settings for the application."""
    # Configure logging with both console and Loki handlers
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)

    loki_handler = logging_loki.LokiHandler(
        url=config.LOKI_URL,
        tags={"application": "price_tracker_agent"},
        version="1",
    )

    # Use force=True to override any existing configuration
    logging.basicConfig(level=logging.INFO, handlers=[console_handler, loki_handler], force=True)
