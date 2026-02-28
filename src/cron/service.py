"""
Cron service for scheduled task execution.

Supports 3 schedule types inspired by Nanobot:
- at: One-time execution at specific timestamp
- every: Periodic execution at interval
- cron: Cron expression-based scheduling
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Callable, Awaitable

from .types import CronJob, CronSchedule, CronJobState

logger = logging.getLogger(__name__)


class CronService:
    """
    Cron service for scheduled task execution.

    Manages cron jobs with persistence and asyncio-based timers.
    """

    def __init__(
        self,
        storage_path: Path,
        on_job: Callable[[CronJob], Awaitable[None]],  # Async callback when job triggers
    ):
        """
        Initialize cron service.

        Args:
            storage_path: Path to JSON file for job persistence
            on_job: Async callback to execute when a job triggers
        """
        self.storage_path = storage_path
        self.on_job = on_job
        self._jobs: list[CronJob] = []
        self._timer_task: asyncio.Task | None = None
        self._running = False

        # Ensure storage directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing jobs from disk
        self._load_jobs()

    def add_job(
        self,
        name: str,
        schedule: CronSchedule,
        task: str,
        priority: str = "NORMAL"
    ) -> str:
        """
        Add a new cron job.

        Args:
            name: Human-readable job name
            schedule: Schedule configuration
            task: Task description to execute
            priority: Job priority ("LOW", "NORMAL", "HIGH")

        Returns:
            Job ID (8-character UUID)
        """
        import uuid
        job_id = str(uuid.uuid4())[:8]

        now_ms = int(datetime.now().timestamp() * 1000)
        next_run = self._compute_next_run(schedule, now_ms)

        job = CronJob(
            id=job_id,
            name=name,
            enabled=True,
            schedule=schedule,
            task=task,
            priority=priority,
            state=CronJobState(next_run_at_ms=next_run),
            created_at_ms=now_ms,
            delete_after_run=(schedule.kind == "at"),  # Auto-delete "at" jobs after run
        )

        self._jobs.append(job)
        self._save_jobs()

        logger.info(f"Added cron job {job_id}: {name} ({schedule.kind})")

        # Re-arm timer if service is running
        if self._running:
            self._arm_timer()

        return job_id

    def enable_job(self, job_id: str, enabled: bool = True) -> bool:
        """
        Enable or disable a job.

        Args:
            job_id: Job identifier
            enabled: Whether to enable or disable

        Returns:
            True if job was found and updated
        """
        for job in self._jobs:
            if job.id == job_id:
                job.enabled = enabled
                self._save_jobs()
                logger.info(f"Job {job_id} {'enabled' if enabled else 'disabled'}")

                if self._running:
                    self._arm_timer()
                return True
        return False

    def remove_job(self, job_id: str) -> bool:
        """
        Remove a cron job.

        Args:
            job_id: Job identifier

        Returns:
            True if job was found and removed
        """
        before = len(self._jobs)
        self._jobs = [j for j in self._jobs if j.id != job_id]

        if len(self._jobs) < before:
            self._save_jobs()
            logger.info(f"Removed cron job {job_id}")

            if self._running:
                self._arm_timer()
            return True
        return False

    def get_job(self, job_id: str) -> CronJob | None:
        """Get a specific job by ID."""
        for job in self._jobs:
            if job.id == job_id:
                return job
        return None

    def list_jobs(self, enabled_only: bool = False) -> list[dict]:
        """
        List all jobs.

        Args:
            enabled_only: Only return enabled jobs

        Returns:
            List of job dictionaries with formatted information
        """
        jobs = self._jobs if not enabled_only else [j for j in self._jobs if j.enabled]

        return [
            {
                "id": j.id,
                "name": j.name,
                "enabled": j.enabled,
                "schedule": self._format_schedule(j.schedule),
                "task": j.task[:50] + "..." if len(j.task) > 50 else j.task,
                "priority": j.priority,
                "next_run": self._format_timestamp(j.state.next_run_at_ms),
                "last_run": self._format_timestamp(j.state.last_run_at_ms),
                "last_status": j.state.last_status,
                "run_count": j.state.run_count,
            }
            for j in jobs
        ]

    async def start(self):
        """Start the cron service timer."""
        if self._running:
            return

        self._running = True        
        self._arm_timer()

    async def stop(self):
        """Stop the cron service timer."""
        if not self._running:
            return

        self._running = False

        if self._timer_task:
            self._timer_task.cancel()
            try:
                await self._timer_task
            except asyncio.CancelledError:
                pass
            self._timer_task = None

        logger.info("Cron service stopped")

    async def run_job_now(self, job_id: str) -> bool:
        """
        Manually trigger a job immediately.

        Args:
            job_id: Job identifier

        Returns:
            True if job was found and executed
        """
        job = self.get_job(job_id)
        if not job:
            return False

        logger.info(f"Manually running job {job_id}: {job.name}")
        await self._execute_job(job)
        return True

    # -------------------------------------------------------------------------
    # Internal methods
    # -------------------------------------------------------------------------

    def _load_jobs(self):
        """Load jobs from JSON storage."""
        if not self.storage_path.exists():
            logger.debug(f"No cron jobs file at {self.storage_path}")
            return

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self._jobs = [CronJob.from_dict(job_data) for job_data in data.get("jobs", [])]
            logger.info(f"Loaded {len(self._jobs)} cron jobs from {self.storage_path}")
        except Exception as e:
            logger.error(f"Error loading cron jobs: {e}")
            self._jobs = []

    def _save_jobs(self):
        """Save jobs to JSON storage."""
        try:
            data = {
                "jobs": [job.to_dict() for job in self._jobs],
                "updated_at": datetime.now().isoformat(),
            }

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(self._jobs)} cron jobs to {self.storage_path}")
        except Exception as e:
            logger.error(f"Error saving cron jobs: {e}")

    def _compute_next_run(self, schedule: CronSchedule, from_ms: int) -> int | None:
        """
        Compute next run time for a schedule.

        Args:
            schedule: Schedule configuration
            from_ms: Current time in milliseconds

        Returns:
            Next run time in milliseconds, or None if no more runs
        """
        if schedule.kind == "at":
            # One-time execution at specific time
            return schedule.at_ms if schedule.at_ms and schedule.at_ms > from_ms else None

        elif schedule.kind == "every":
            # Periodic execution - next run is current time + interval
            return from_ms + schedule.every_ms

        elif schedule.kind == "cron":
            # Cron expression - use croniter to compute next run
            try:
                from croniter import croniter
                from_dt = datetime.fromtimestamp(from_ms / 1000, tz=timezone.utc)

                # Use specified timezone or UTC
                if schedule.tz:
                    try:
                        import zoneinfo
                        tz = zoneinfo.ZoneInfo(schedule.tz)
                        from_dt = from_dt.astimezone(tz)
                    except Exception:
                        logger.warning(f"Invalid timezone {schedule.tz}, using UTC")

                cron = croniter(schedule.expr, from_dt)
                next_dt = cron.get_next(datetime)
                return int(next_dt.timestamp() * 1000)

            except ImportError:
                logger.error("croniter library not installed - cron schedules won't work")
                return None
            except Exception as e:
                logger.error(f"Error computing cron next run: {e}")
                return None

        return None

    def _arm_timer(self):
        """Arm the timer for the next job."""
        # Cancel existing timer
        if self._timer_task:
            self._timer_task.cancel()
            self._timer_task = None

        # Find next job to run
        now_ms = int(datetime.now().timestamp() * 1000)
        enabled_jobs = [j for j in self._jobs if j.enabled and j.state.next_run_at_ms]

        if not enabled_jobs:
            logger.debug("No enabled jobs to schedule")
            return

        # Sort by next run time
        enabled_jobs.sort(key=lambda j: j.state.next_run_at_ms)
        next_job = enabled_jobs[0]
        next_run_ms = next_job.state.next_run_at_ms

        if next_run_ms <= now_ms:
            # Job should run immediately
            delay_s = 0
        else:
            # Schedule for future
            delay_s = (next_run_ms - now_ms) / 1000

        logger.debug(f"Next job: {next_job.id} in {delay_s:.1f}s")

        # Create timer task
        self._timer_task = asyncio.create_task(self._timer_callback(delay_s))

    async def _timer_callback(self, delay_s: float):
        """Timer callback - wait then execute jobs."""
        try:
            await asyncio.sleep(delay_s)

            # Execute all jobs that are due
            now_ms = int(datetime.now().timestamp() * 1000)
            due_jobs = [
                j for j in self._jobs
                if j.enabled and j.state.next_run_at_ms and j.state.next_run_at_ms <= now_ms
            ]

            for job in due_jobs:
                await self._execute_job(job)

            # Re-arm timer if still running
            if self._running:
                self._arm_timer()

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in timer callback: {e}")

    async def _execute_job(self, job: CronJob):
        """Execute a cron job."""
        now_ms = int(datetime.now().timestamp() * 1000)

        logger.info(f"Executing cron job {job.id}: {job.name}")

        try:
            # Call the callback
            await self.on_job(job)

            # Update state
            job.state.last_run_at_ms = now_ms
            job.state.last_status = "ok"
            job.state.last_error = None
            job.state.run_count += 1

        except Exception as e:
            logger.error(f"Error executing job {job.id}: {e}")
            job.state.last_run_at_ms = now_ms
            job.state.last_status = "error"
            job.state.last_error = str(e)
            job.state.run_count += 1

        # Compute next run time
        job.state.next_run_at_ms = self._compute_next_run(job.schedule, now_ms)

        # Auto-delete "at" jobs after execution
        if job.delete_after_run:
            logger.info(f"Auto-deleting one-time job {job.id}")
            self._jobs = [j for j in self._jobs if j.id != job.id]

        self._save_jobs()

    def _format_schedule(self, schedule: CronSchedule) -> str:
        """Format schedule for display."""
        if schedule.kind == "at":
            return f"at {self._format_timestamp(schedule.at_ms)}"
        elif schedule.kind == "every":
            return f"every {self._format_duration(schedule.every_ms)}"
        elif schedule.kind == "cron":
            tz_str = f" ({schedule.tz})" if schedule.tz else ""
            return f"cron '{schedule.expr}'{tz_str}"
        return "unknown"

    def _format_timestamp(self, ms: int | None) -> str:
        """Format timestamp for display."""
        if ms is None:
            return "never"
        dt = datetime.fromtimestamp(ms / 1000)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def _format_duration(self, ms: int | None) -> str:
        """Format duration for display."""
        if ms is None:
            return "unknown"

        seconds = ms / 1000
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds / 60:.0f}m"
        elif seconds < 86400:
            return f"{seconds / 3600:.1f}h"
        else:
            return f"{seconds / 86400:.1f}d"
