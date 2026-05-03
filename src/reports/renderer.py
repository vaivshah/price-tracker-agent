"""
Report renderer — builds HTML from Jinja2 templates and data.

Single Responsibility: only concerned with template rendering, not serving or DB.
"""
import os
import logging

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

_env = Environment(
    loader=FileSystemLoader(_TEMPLATE_DIR),
    autoescape=select_autoescape(["html"]),
)


def render(template_name: str, context: dict) -> str:
    """
    Render an HTML template with the given context.

    Args:
        template_name: filename inside reports/templates/ (e.g. 'research.html')
        context: dict of variables to inject into the template

    Returns:
        Rendered HTML string.
    """
    template = _env.get_template(template_name)
    html = template.render(**context)
    logger.info("Rendered template '%s'", template_name)
    return html
