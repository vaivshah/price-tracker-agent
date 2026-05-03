"""
Abstract base for all input channels (Strategy Pattern).

Every communication channel (WhatsApp, Telegram, Email, Web, etc.) must
implement this interface so the rest of the system remains channel-agnostic.

SOLID Principles:
- Single Responsibility: defines only the channel contract.
- Open/Closed: new channels extend, never modify this file.
- Liskov Substitution: any subclass is a drop-in replacement.
- Interface Segregation: minimal surface — parse + respond.
- Dependency Inversion: callers depend on this abstraction.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class IncomingMessage:
    """Channel-agnostic representation of a user message."""

    user_identifier: str          # phone number, email, chat_id, etc.
    channel: str                  # "whatsapp", "telegram", "email", "web"
    text: str
    raw_payload: dict = field(default_factory=dict, repr=False)
    message_id: Optional[str] = None  # For webhook idempotency / deduplication


class Channel(ABC):
    """
    Strategy interface for input channels.

    Subclasses must implement `parse_request` (inbound) and
    `send_response` (outbound).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique channel identifier (e.g. 'whatsapp', 'telegram')."""
        ...

    @abstractmethod
    async def parse_request(self, request) -> IncomingMessage:
        """Parse a channel-specific HTTP request into a normalised message."""
        ...

    @abstractmethod
    async def send_response(self, user_identifier: str, message: str) -> None:
        """Send a response back through this channel."""
        ...
