"""
Abstract base for agent capability services.

Each service encapsulates a single user-facing capability (Single Responsibility).
New capabilities are added by creating a new subclass (Open/Closed).

SOLID Principles:
- Interface Segregation: services only expose `execute`.
- Dependency Inversion: callers depend on this abstraction, not concrete services.
"""
from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

from src.channels.base import IncomingMessage


class BaseService(ABC):
    """
    Contract that every agent capability must fulfill.

    Implementations must:
    - Log start/end of execution
    - Record telemetry via core.telemetry counters
    - Wrap DB writes in try/except with rollback (ACID)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique service identifier used in logging and telemetry."""
        ...

    @abstractmethod
    async def execute(self, message: IncomingMessage, user_id: int, db: Session) -> str:
        """Process a user request and return a human-readable response."""
        ...
