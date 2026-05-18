"""
Simulation Queue Service
In-memory FIFO queue for serializing LLM calls in Phase 1.
Handles job submission, status tracking, and queue depth monitoring.
"""

import threading
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, Callable

from ..utils.logger import get_logger

logger = get_logger('mirofish.simulation_queue')


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class SimulationJob:
    """Represents a single simulation job in the queue."""

    def __init__(self, simulation_id: str, user_id: str, document: str, document_type: str):
        self.simulation_id = simulation_id
        self.user_id = user_id
        self.document = document
        self.document_type = document_type
        self.status = JobStatus.QUEUED
        self.progress = 0.0
        self.stage = "queued"
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.created_at = datetime.now(timezone.utc)
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.reactions_count = 0
        self.total_personas = 50

    def to_dict(self) -> Dict[str, Any]:
        return {
            'simulation_id': self.simulation_id,
            'status': self.status.value,
            'progress': round(self.progress, 2),
            'stage': self.stage,
            'reactions_count': self.reactions_count,
            'total_personas': self.total_personas,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error': self.error,
        }


class SimulationQueue:
    """
    In-memory FIFO queue for serializing simulation execution.
    Thread-safe singleton pattern.
    """

    _instance: Optional['SimulationQueue'] = None
    _lock = threading.Lock()

    def __init__(self):
        self._queue: deque = deque()
        self._jobs: Dict[str, SimulationJob] = {}
        self._processing = False
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._queue_lock = threading.Lock()
        self._processor: Optional[Callable] = None

    @classmethod
    def get_instance(cls) -> 'SimulationQueue':
        """Get or create the singleton queue instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def set_processor(self, processor: Callable):
        """Set the function that processes a simulation job."""
        self._processor = processor

    def submit(self, user_id: str, document: str, document_type: str) -> str:
        """
        Submit a new simulation job to the queue.
        Returns the simulation_id.
        """
        simulation_id = str(uuid.uuid4())
        job = SimulationJob(simulation_id, user_id, document, document_type)

        with self._queue_lock:
            self._jobs[simulation_id] = job
            self._queue.append(simulation_id)

        logger.info(f"Job submitted: {simulation_id}, queue depth: {self.depth}")

        if not self._processing:
            self._start_worker()

        return simulation_id

    def get_job(self, simulation_id: str) -> Optional[SimulationJob]:
        """Get job by ID."""
        return self._jobs.get(simulation_id)

    def get_job_status(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Get job status dict for API response."""
        job = self._jobs.get(simulation_id)
        if not job:
            return None
        return job.to_dict()

    @property
    def depth(self) -> int:
        """Current queue depth (queued jobs only)."""
        with self._queue_lock:
            return sum(1 for sid in self._queue if self._jobs.get(sid) and self._jobs.get(sid).status == JobStatus.QUEUED)

    def get_queue_position(self, simulation_id: str) -> int:
        """Get position in queue (0 if not queued or currently running)."""
        with self._queue_lock:
            position = 0
            for sid in self._queue:
                job = self._jobs.get(sid)
                if not job or job.status != JobStatus.QUEUED:
                    continue
                if sid == simulation_id:
                    return position
                position += 1
            return -1

    def get_estimated_wait(self, simulation_id: str) -> int:
        """Get estimated wait time in seconds."""
        position = self.get_queue_position(simulation_id)
        if position < 0:
            return 0
        # ~20 seconds per sim with batching (5 personas/call, 10 calls at 30 RPM)
        return position * 20

    def _start_worker(self):
        """Start the background worker thread."""
        if self._worker_thread and self._worker_thread.is_alive():
            return

        self._processing = True
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()
        logger.info("Queue worker started")

    def _process_queue(self):
        """Background worker that processes jobs sequentially."""
        while not self._stop_event.is_set():
            job = None

            with self._queue_lock:
                while self._queue:
                    sid = self._queue[0]
                    candidate = self._jobs.get(sid)
                    if candidate and candidate.status == JobStatus.QUEUED:
                        job = candidate
                        break
                    self._queue.popleft()

            if not job:
                time.sleep(0.5)
                continue

            self._execute_job(job)

        self._processing = False
        logger.info("Queue worker stopped")

    def _execute_job(self, job: SimulationJob):
        """Execute a single job using the registered processor."""
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        job.stage = "initializing"
        logger.info(f"Executing job: {job.simulation_id}")

        try:
            if not self._processor:
                raise RuntimeError("No processor registered for simulation queue")

            result = self._processor(job)

            if result.get('partial', False):
                job.status = JobStatus.PARTIAL
                job.stage = "completed_partial"
            else:
                job.status = JobStatus.COMPLETED
                job.stage = "completed"

            job.result = result
            job.progress = 1.0
            job.completed_at = datetime.now(timezone.utc)
            logger.info(f"Job completed: {job.simulation_id}, status={job.status.value}")

        except Exception as e:
            job.status = JobStatus.FAILED
            job.stage = "failed"
            job.error = str(e)
            job.completed_at = datetime.now(timezone.utc)
            logger.error(f"Job failed: {job.simulation_id}, error={e}")

        with self._queue_lock:
            if self._queue and self._queue[0] == job.simulation_id:
                self._queue.popleft()

    def stop(self):
        """Stop the queue worker."""
        self._stop_event.set()
        if self._worker_thread:
            self._worker_thread.join(timeout=5)

    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Remove completed/failed jobs older than max_age_hours."""
        cutoff = datetime.now(timezone.utc)
        to_remove = []

        with self._queue_lock:
            for sid, job in self._jobs.items():
                if job.completed_at and (cutoff - job.completed_at).total_seconds() > max_age_hours * 3600:
                    to_remove.append(sid)

            for sid in to_remove:
                del self._jobs[sid]

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old jobs")

    def cleanup_neo4j_simulations(self, neo4j_storage, max_age_days: int = 30):
        """
        Delete Simulation nodes and connected Persona/Reaction nodes older than max_age_days.
        Called by daily cleanup job (GitHub Actions cron or Render scheduled task).

        Args:
            neo4j_storage: Neo4jStorage instance.
            max_age_days: Delete simulations older than this many days.
        """
        try:
            cutoff_date = (datetime.now(timezone.utc)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - max_age_days)

            # Delete connected nodes first (Personas, Reactions)
            neo4j_storage.execute_query("""
                MATCH (s:Simulation {status: 'completed'})
                WHERE s.created_at < $cutoff
                WITH s LIMIT 100
                MATCH (s)-[:HAS_PERSONA]->(p:Persona)-[:GENERATED]->(r:Reaction)
                DELETE r, p, s
            """, {'cutoff': cutoff_date.isoformat()})

            logger.info(f"Neo4j cleanup: deleted simulations older than {max_age_days} days")

        except Exception as e:
            logger.error(f"Neo4j cleanup failed: {e}")
