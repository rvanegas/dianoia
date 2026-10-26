"""The coordinator's worker threads wait for work instead of spinning.

Until 2026-10-26 seven workers polled an empty list with nothing to block on
and held a full core of the commons box at idle.
"""

import threading
import time
from unittest.mock import Mock, patch

from services.agent_coordinator import AgentCoordinator


def _input():
    agent_input = Mock()
    agent_input.conversation_id = "c1"
    agent_input.snapshot_id = "1"
    return agent_input


def test_idle_workers_use_no_cpu():
    coordinator = AgentCoordinator()
    try:
        time.sleep(0.2)  # let the workers reach their wait
        before = time.process_time()
        time.sleep(1.0)
        used = time.process_time() - before
        # Spinning, seven workers burned about a full second here.
        assert used < 0.2, f"idle process used {used:.2f}s of CPU in 1s"
    finally:
        coordinator.stop()


def test_queued_task_is_taken_without_waiting_out_the_idle_timeout():
    coordinator = AgentCoordinator()
    taken = threading.Event()
    try:
        with patch.object(coordinator, "_process_task", side_effect=lambda task: taken.set()):
            time.sleep(0.2)
            start = time.monotonic()
            coordinator.queue_task("name_generator", _input())
            assert taken.wait(timeout=2.0)
            assert time.monotonic() - start < AgentCoordinator.IDLE_WAIT_SECONDS / 2
    finally:
        coordinator.stop()


def test_task_goes_to_its_own_agent_type_only():
    coordinator = AgentCoordinator()
    seen = []
    done = threading.Event()

    def record(task):
        seen.append((threading.current_thread().name, task.agent_type))
        done.set()

    try:
        with patch.object(coordinator, "_process_task", side_effect=record):
            coordinator.queue_task("phrasing_evaluator", _input())
            assert done.wait(timeout=2.0)
            assert seen == [("agent_worker_phrasing_evaluator", "phrasing_evaluator")]
    finally:
        coordinator.stop()


def test_stop_ends_the_workers():
    coordinator = AgentCoordinator()
    coordinator.stop()
    for worker in coordinator.workers:
        worker.join(timeout=2 * AgentCoordinator.IDLE_WAIT_SECONDS)
        assert not worker.is_alive(), worker.name
