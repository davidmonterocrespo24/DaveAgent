"""
Cron system data types.

Defines the core data structures for the cron scheduling system,
inspired by Nanobot's implementation.
"""

from dataclasses import dataclass, field
from typing import Literal
from datetime import datetime


@dataclass
class CronSchedule:
    """
    Schedule configuration for cron jobs.

    Supports 3 schedule types:
    1. at: One-time execution at specific timestamp
       - at_ms: Unix timestamp in milliseconds

    2. every: Periodic execution at interval
       - every_ms: Interval in milliseconds

    3. cron: Cron expression-based scheduling
       - expr: Standard cron expression (e.g., "0 9 * * *")
       - tz: Timezone for evaluation (e.g., "America/New_York")
    """
    kind: Literal["at", "every", "cron"]
    at_ms: int | None = None        # Unix timestamp in ms for "at"
    every_ms: int | None = None     # Interval in ms for "every"
    expr: str | None = None         # Cron expression for "cron"
    tz: str | None = None          # Timezone for cron expressions

    def __post_init__(self):
        """Validate schedule configuration."""
        if self.kind == "at":
            if self.at_ms is None:
                raise ValueError("at_ms is required for 'at' schedule")
        elif self.kind == "every":
            if self.every_ms is None:
                raise ValueError("every_ms is required for 'every' schedule")
            if self.every_ms <= 0:
                raise ValueError("every_ms must be positive")
        elif self.kind == "cron":
            if self.expr is None:
                raise ValueError("expr is required for 'cron' schedule")
        else:
            raise ValueError(f"Invalid schedule kind: {self.kind}")


@dataclass
class CronJobState:
    """
    Runtime state of a cron job.

    Tracks execution status, timing, and error information.
    """
    next_run_at_ms: int | None = None  # Next scheduled run time
    last_run_at_ms: int | None = None  # Last execution time
    last_status: str = "idle"          # "idle", "ok", "error"
    last_error: str | None = None      # Last error message if any
    run_count: int = 0                 # Total number of executions


@dataclass
class CronJob:
    """
    Cron job definition.

    Represents a scheduled task with its configuration and state.
    """
    id: str                           # Unique job identifier
    name: str                         # Human-readable name
    enabled: bool                     # Whether job is active
    schedule: CronSchedule            # Schedule configuration
    task: str                         # Task description to execute
    priority: str = "NORMAL"          # "LOW", "NORMAL", "HIGH"
    state: CronJobState = field(default_factory=CronJobState)
    created_at_ms: int = field(
        default_factory=lambda: int(datetime.now().timestamp() * 1000)
    )
    delete_after_run: bool = False    # Auto-delete after one-time execution

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "enabled": self.enabled,
            "schedule": {
                "kind": self.schedule.kind,
                "at_ms": self.schedule.at_ms,
                "every_ms": self.schedule.every_ms,
                "expr": self.schedule.expr,
                "tz": self.schedule.tz,
            },
            "task": self.task,
            "priority": self.priority,
            "state": {
                "next_run_at_ms": self.state.next_run_at_ms,
                "last_run_at_ms": self.state.last_run_at_ms,
                "last_status": self.state.last_status,
                "last_error": self.state.last_error,
                "run_count": self.state.run_count,
            },
            "created_at_ms": self.created_at_ms,
            "delete_after_run": self.delete_after_run,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CronJob":
        """Create from dictionary (JSON deserialization)."""
        schedule_data = data["schedule"]
        schedule = CronSchedule(
            kind=schedule_data["kind"],
            at_ms=schedule_data.get("at_ms"),
            every_ms=schedule_data.get("every_ms"),
            expr=schedule_data.get("expr"),
            tz=schedule_data.get("tz"),
        )

        state_data = data["state"]
        state = CronJobState(
            next_run_at_ms=state_data.get("next_run_at_ms"),
            last_run_at_ms=state_data.get("last_run_at_ms"),
            last_status=state_data.get("last_status", "idle"),
            last_error=state_data.get("last_error"),
            run_count=state_data.get("run_count", 0),
        )

        return cls(
            id=data["id"],
            name=data["name"],
            enabled=data["enabled"],
            schedule=schedule,
            task=data["task"],
            priority=data.get("priority", "NORMAL"),
            state=state,
            created_at_ms=data.get("created_at_ms", int(datetime.now().timestamp() * 1000)),
            delete_after_run=data.get("delete_after_run", False),
        )
