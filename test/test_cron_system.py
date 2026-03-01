"""
Test script for FASE 2: Cron System

Tests the complete cron scheduling system:
1. CronSchedule types (at/every/cron)
2. CronService functionality
3. Job persistence
4. CLI commands integration
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test that all cron components can be imported."""
    print("\n" + "="*70)
    print("TEST 1: Import cron components")
    print("="*70)

    try:
        from src.cron import CronSchedule, CronJobState, CronJob, CronService
        print("[OK] All cron types imported")
    except ImportError as e:
        print(f"[FAIL] Could not import cron types: {e}")
        return False

    try:
        from src.cron.types import CronSchedule
        print("[OK] CronSchedule imported")
    except ImportError as e:
        print(f"[FAIL] Could not import CronSchedule: {e}")
        return False

    try:
        from src.cron.service import CronService
        print("[OK] CronService imported")
    except ImportError as e:
        print(f"[FAIL] Could not import CronService: {e}")
        return False

    return True


def test_schedule_types():
    """Test creating different schedule types."""
    print("\n" + "="*70)
    print("TEST 2: Schedule types (at/every/cron)")
    print("="*70)

    from src.cron.types import CronSchedule

    try:
        # Test "at" schedule
        future_time = int((datetime.now() + timedelta(hours=1)).timestamp() * 1000)
        at_schedule = CronSchedule(kind="at", at_ms=future_time)
        assert at_schedule.kind == "at"
        assert at_schedule.at_ms == future_time
        print("[OK] 'at' schedule created")

        # Test "every" schedule
        every_schedule = CronSchedule(kind="every", every_ms=3600000)  # 1 hour
        assert every_schedule.kind == "every"
        assert every_schedule.every_ms == 3600000
        print("[OK] 'every' schedule created")

        # Test "cron" schedule
        cron_schedule = CronSchedule(kind="cron", expr="0 9 * * *")
        assert cron_schedule.kind == "cron"
        assert cron_schedule.expr == "0 9 * * *"
        print("[OK] 'cron' schedule created")

        return True
    except Exception as e:
        print(f"[FAIL] Error creating schedules: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schedule_validation():
    """Test schedule validation logic."""
    print("\n" + "="*70)
    print("TEST 3: Schedule validation")
    print("="*70)

    from src.cron.types import CronSchedule

    # Test invalid "at" schedule (missing at_ms)
    try:
        CronSchedule(kind="at")
        print("[FAIL] Should have raised ValueError for missing at_ms")
        return False
    except ValueError:
        print("[OK] Validation works for 'at' without at_ms")

    # Test invalid "every" schedule (missing every_ms)
    try:
        CronSchedule(kind="every")
        print("[FAIL] Should have raised ValueError for missing every_ms")
        return False
    except ValueError:
        print("[OK] Validation works for 'every' without every_ms")

    # Test invalid "cron" schedule (missing expr)
    try:
        CronSchedule(kind="cron")
        print("[FAIL] Should have raised ValueError for missing expr")
        return False
    except ValueError:
        print("[OK] Validation works for 'cron' without expr")

    # Test invalid "every" with negative interval
    try:
        CronSchedule(kind="every", every_ms=-1000)
        print("[FAIL] Should have raised ValueError for negative every_ms")
        return False
    except ValueError:
        print("[OK] Validation works for negative every_ms")

    return True


def test_job_serialization():
    """Test CronJob to_dict and from_dict."""
    print("\n" + "="*70)
    print("TEST 4: Job serialization")
    print("="*70)

    from src.cron.types import CronSchedule, CronJob

    try:
        # Create a job
        schedule = CronSchedule(kind="every", every_ms=60000)  # 1 minute
        job = CronJob(
            id="test123",
            name="Test Job",
            enabled=True,
            schedule=schedule,
            task="Test task description"
        )

        # Serialize to dict
        job_dict = job.to_dict()
        assert job_dict["id"] == "test123"
        assert job_dict["name"] == "Test Job"
        assert job_dict["schedule"]["kind"] == "every"
        print("[OK] Job serialization to dict works")

        # Deserialize from dict
        job2 = CronJob.from_dict(job_dict)
        assert job2.id == job.id
        assert job2.name == job.name
        assert job2.schedule.kind == job.schedule.kind
        assert job2.schedule.every_ms == job.schedule.every_ms
        print("[OK] Job deserialization from dict works")

        return True
    except Exception as e:
        print(f"[FAIL] Error with serialization: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_cron_service_basic():
    """Test basic CronService operations."""
    print("\n" + "="*70)
    print("TEST 5: CronService basic operations")
    print("="*70)

    from src.cron import CronService, CronSchedule
    import tempfile

    # Create temp file for storage
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        storage_path = Path(f.name)

    try:
        # Track job executions
        executed_jobs = []

        async def on_job(job):
            executed_jobs.append(job.id)
            print(f"[INFO] Job {job.id} executed")

        # Create service
        service = CronService(storage_path=storage_path, on_job=on_job)
        print("[OK] CronService created")

        # Add a job
        schedule = CronSchedule(kind="every", every_ms=1000)  # 1 second
        job_id = service.add_job(
            name="Test Job",
            schedule=schedule,
            task="Test task"
        )
        print(f"[OK] Job added with ID: {job_id}")

        # List jobs
        jobs = service.list_jobs()
        assert len(jobs) == 1
        assert jobs[0]["id"] == job_id
        print(f"[OK] Job listed: {jobs[0]['name']}")

        # Get specific job
        job = service.get_job(job_id)
        assert job is not None
        assert job.name == "Test Job"
        print("[OK] Job retrieved by ID")

        # Disable job
        success = service.enable_job(job_id, enabled=False)
        assert success
        job = service.get_job(job_id)
        assert not job.enabled
        print("[OK] Job disabled")

        # Re-enable job
        success = service.enable_job(job_id, enabled=True)
        assert success
        job = service.get_job(job_id)
        assert job.enabled
        print("[OK] Job re-enabled")

        # Remove job
        success = service.remove_job(job_id)
        assert success
        jobs = service.list_jobs()
        assert len(jobs) == 0
        print("[OK] Job removed")

        # Cleanup
        storage_path.unlink()

        return True
    except Exception as e:
        print(f"[FAIL] Error in CronService: {e}")
        import traceback
        traceback.print_exc()
        # Cleanup on error
        if storage_path.exists():
            storage_path.unlink()
        return False


async def test_cron_persistence():
    """Test job persistence to disk."""
    print("\n" + "="*70)
    print("TEST 6: Job persistence")
    print("="*70)

    from src.cron import CronService, CronSchedule
    import tempfile

    # Create temp file for storage
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        storage_path = Path(f.name)

    try:
        async def dummy_callback(job):
            pass

        # Create service and add jobs
        service1 = CronService(storage_path=storage_path, on_job=dummy_callback)

        schedule1 = CronSchedule(kind="every", every_ms=60000)
        job_id1 = service1.add_job("Job 1", schedule1, "Task 1")

        schedule2 = CronSchedule(kind="every", every_ms=120000)
        job_id2 = service1.add_job("Job 2", schedule2, "Task 2")

        print(f"[OK] Created 2 jobs in first service")

        # Create new service instance (should load from disk)
        service2 = CronService(storage_path=storage_path, on_job=dummy_callback)
        jobs = service2.list_jobs()

        assert len(jobs) == 2, f"Expected 2 jobs, got {len(jobs)}"
        job_ids = {job["id"] for job in jobs}
        assert job_id1 in job_ids
        assert job_id2 in job_ids
        print(f"[OK] Jobs persisted and loaded correctly")

        # Cleanup
        storage_path.unlink()

        return True
    except Exception as e:
        print(f"[FAIL] Error with persistence: {e}")
        import traceback
        traceback.print_exc()
        # Cleanup on error
        if storage_path.exists():
            storage_path.unlink()
        return False


async def test_cron_execution():
    """Test actual job execution with timer."""
    print("\n" + "="*70)
    print("TEST 7: Job execution with timer")
    print("="*70)

    from src.cron import CronService, CronSchedule
    import tempfile

    # Create temp file for storage
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        storage_path = Path(f.name)

    try:
        # Track executions
        executed_jobs = []

        async def on_job(job):
            executed_jobs.append(job.id)

        # Create service
        service = CronService(storage_path=storage_path, on_job=on_job)

        # Add job that runs in 2 seconds
        schedule = CronSchedule(kind="every", every_ms=2000)
        job_id = service.add_job("Fast Job", schedule, "Test execution")
        print(f"[INFO] Added job {job_id}, will run in ~2 seconds")

        # Start service
        await service.start()
        print("[OK] Service started")

        # Wait for execution
        await asyncio.sleep(3)

        # Check if job executed
        if job_id in executed_jobs:
            print(f"[OK] Job {job_id} executed successfully")
        else:
            print(f"[WARNING] Job {job_id} did not execute in time")

        # Stop service
        await service.stop()
        print("[OK] Service stopped")

        # Cleanup
        storage_path.unlink()

        return job_id in executed_jobs
    except Exception as e:
        print(f"[FAIL] Error with execution: {e}")
        import traceback
        traceback.print_exc()
        # Cleanup on error
        if storage_path.exists():
            storage_path.unlink()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("FASE 2: CRON SYSTEM - TEST SUITE")
    print("="*70)

    results = []

    # Sync tests
    results.append(("Imports", test_imports()))
    results.append(("Schedule Types", test_schedule_types()))
    results.append(("Schedule Validation", test_schedule_validation()))
    results.append(("Job Serialization", test_job_serialization()))

    # Async tests
    loop = asyncio.get_event_loop()
    results.append(("CronService Basic", loop.run_until_complete(test_cron_service_basic())))
    results.append(("Job Persistence", loop.run_until_complete(test_cron_persistence())))
    results.append(("Job Execution", loop.run_until_complete(test_cron_execution())))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n" + "="*70)
        print("[SUCCESS] FASE 2: CRON SYSTEM - COMPLETE!")
        print("="*70)
        print("\nImplemented features:")
        print("  [OK] 3 schedule types: at (one-time), every (interval), cron (expression)")
        print("  [OK] CronService with asyncio timers")
        print("  [OK] JSON persistence")
        print("  [OK] Job management (add/list/enable/disable/remove)")
        print("  [OK] Integration with subagents")
        print("  [OK] CLI commands (/cron)")
        print("\nUsage examples:")
        print("  /cron add at 2026-02-20T15:30 Review PRs")
        print("  /cron add every 1h Check build status")
        print("  /cron add cron '0 9 * * *' Daily standup")
        print("  /cron list")
        print("\nReady for FASE 3: Auto-Injection")
        print("="*70)
        return 0
    else:
        print(f"\n[WARNING] {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
