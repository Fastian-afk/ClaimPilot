"""
ClaimPilot — Structured Logging
Provides consistent, structured logging across all agents.
"""

import logging
import sys
from datetime import datetime

import structlog


def setup_logger(agent_name: str, log_level: str = "INFO") -> structlog.BoundLogger:
    """
    Set up a structured logger for a ClaimPilot agent.

    Args:
        agent_name: Name of the agent (e.g., "fraud_detection", "intake")
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        A configured structlog logger instance.
    """
    # Configure structlog processors
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Create and return a bound logger with the agent name
    logger = structlog.get_logger()
    return logger.bind(
        agent=agent_name,
        service="claimpilot",
    )


def log_case_event(
    logger: structlog.BoundLogger,
    case_id: str,
    event: str,
    **kwargs,
) -> None:
    """
    Log a case-specific event with consistent structure.

    Args:
        logger: The structlog logger instance.
        case_id: The Maestro case ID.
        event: Description of the event.
        **kwargs: Additional context fields.
    """
    logger.info(
        event,
        case_id=case_id,
        timestamp=datetime.utcnow().isoformat(),
        **kwargs,
    )


def log_agent_action(
    logger: structlog.BoundLogger,
    case_id: str,
    action: str,
    result: str,
    duration_ms: float = 0,
    **kwargs,
) -> None:
    """
    Log an agent action with performance metrics.

    Args:
        logger: The structlog logger instance.
        case_id: The Maestro case ID.
        action: What the agent did.
        result: Outcome of the action.
        duration_ms: How long the action took in milliseconds.
        **kwargs: Additional context fields.
    """
    logger.info(
        "agent_action",
        case_id=case_id,
        action=action,
        result=result,
        duration_ms=round(duration_ms, 2),
        **kwargs,
    )
