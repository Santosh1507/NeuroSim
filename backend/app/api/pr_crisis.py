"""
PR Crisis Simulation API Blueprint
POST /api/simulations - Create simulation
GET /api/simulations/:id - Poll status / get results
"""

import threading
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timezone

from ..config import Config
from ..utils.logger import get_logger
from ..utils.llm_client import LLMClient
from ..auth import require_auth
from ..services.stage_gate import DocumentGate
from ..services.simulation_queue import SimulationQueue, JobStatus
from ..services.persona_generator import PersonaGenerator
from ..services.swarm_simulator import SwarmSimulator
from ..services.blind_spot_detector import BlindSpotDetector
from ..services.report_generator import ReportGenerator

logger = get_logger('mirofish.pr_crisis_api')

pr_crisis_bp = Blueprint('pr_crisis', __name__)

# Global instances (initialized on first request)
_document_gate = DocumentGate()
_queue: SimulationQueue = None
_initialized = False
_init_lock = threading.Lock()


def _initialize_services():
    """Initialize services lazily on first request."""
    global _queue, _initialized

    if _initialized:
        return

    with _init_lock:
        if _initialized:
            return

        llm_client = LLMClient()
        _queue = SimulationQueue.get_instance()
        _queue.set_processor(_process_simulation)

        _initialized = True
        logger.info("PR Crisis API services initialized")


def _process_simulation(job) -> dict:
    """
    Process a simulation job. Called by the queue worker.
    This is the main simulation pipeline.
    """
    job.stage = "generating_personas"
    logger.info(f"Starting simulation pipeline for job {job.simulation_id}")

    llm_client = LLMClient()
    persona_gen = PersonaGenerator(llm_client=llm_client)
    simulator = SwarmSimulator(llm_client=llm_client)
    detector = BlindSpotDetector(llm_client=llm_client)
    report_gen = ReportGenerator()

    # Step 1: Generate personas
    job.stage = "generating_personas"
    job.progress = 0.1
    personas = persona_gen.generate(num_personas=50)

    # Verify diversity
    diversity = persona_gen.verify_diversity(personas)
    if not diversity.get('all_passed'):
        logger.warning(f"Persona diversity check failed: {diversity}")

    # Step 2: Run swarm simulation
    job.stage = "simulating_reactions"

    def progress_callback(current, total):
        job.reactions_count = current
        job.progress = 0.1 + (current / total) * 0.7

    reactions, completed_count = simulator.simulate(
        document=job.document,
        personas=personas,
        progress_callback=progress_callback
    )

    partial = completed_count < len(personas)

    # Step 3: Detect blind spots
    job.stage = "analyzing_blind_spots"
    job.progress = 0.85
    blind_spots = detector.detect(job.document, reactions)

    # Step 4: Generate report
    job.stage = "generating_report"
    job.progress = 0.95
    report = report_gen.generate(
        reactions=reactions,
        blind_spots=blind_spots,
        personas=personas,
        document_type=job.document_type,
        partial=partial
    )

    job.progress = 1.0
    result = {
        'report': report,
        'partial': partial,
        'completed_count': completed_count,
        'total_personas': len(personas),
    }

    return result


@pr_crisis_bp.route('', methods=['POST'])
@require_auth
def create_simulation():
    """
    Create a new PR crisis simulation.

    Request JSON:
    {
        "document": "string (press release text, min 100 chars)",
        "document_type": "press_release | statement | blog_post"
    }

    Response (202 Accepted):
    {
        "simulation_id": "uuid",
        "status": "queued",
        "estimated_completion": "ISO timestamp"
    }
    """
    _initialize_services()

    data = request.get_json() or {}
    document = data.get('document', '').strip()
    document_type = data.get('document_type', 'press_release')

    # Validate document type
    valid_types = ('press_release', 'statement', 'blog_post')
    if document_type not in valid_types:
        return jsonify({'error': f"Invalid document_type. Must be one of: {valid_types}"}), 400

    # Stage gate validation
    passed, reason = _document_gate.validate(document)
    if not passed:
        return jsonify({'error': reason}), 400

    # Sanitize document
    sanitized = _document_gate.sanitize(document)
    document_hash = _document_gate.compute_hash(document)

    # Get user ID from auth context
    user_id = getattr(request, 'user_id', 'anonymous')

    # Submit to queue
    simulation_id = _queue.submit(
        user_id=user_id,
        document=sanitized,
        document_type=document_type
    )

    # Store document hash in job for audit
    job = _queue.get_job(simulation_id)
    if job:
        job.document_hash = document_hash

    queue_depth = _queue.depth
    estimated_wait = _queue.get_estimated_wait(simulation_id)
    estimated_completion = datetime.now(timezone.utc).timestamp() + estimated_wait + 120  # + 2 min for sim

    logger.info(f"Simulation created: {simulation_id}, queue_depth={queue_depth}")

    return jsonify({
        'simulation_id': simulation_id,
        'status': 'queued',
        'queue_position': _queue.get_queue_position(simulation_id),
        'estimated_wait_seconds': estimated_wait,
        'estimated_completion': datetime.fromtimestamp(estimated_completion, tz=timezone.utc).isoformat(),
    }), 202


@pr_crisis_bp.route('/<simulation_id>', methods=['GET'])
@require_auth
def get_simulation(simulation_id: str):
    """
    Get simulation status and results.

    Response (200 OK):
    {
        "simulation_id": "uuid",
        "status": "completed | running | failed | queued | partial",
        "progress": 0.6,
        "stage": "simulating_reactions",
        "queue_position": 2,
        "estimated_wait_seconds": 40,
        "result": { ... }  // Only present when completed/partial
    }
    """
    _initialize_services()

    job = _queue.get_job(simulation_id)
    if not job:
        return jsonify({'error': 'Simulation not found'}), 404

    response = job.to_dict()

    # Add queue-specific info
    if job.status == JobStatus.QUEUED:
        response['queue_position'] = _queue.get_queue_position(simulation_id)
        response['estimated_wait_seconds'] = _queue.get_estimated_wait(simulation_id)

    return jsonify(response), 200
