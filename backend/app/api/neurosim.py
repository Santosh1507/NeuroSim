"""
NeuroSim API Blueprint
Endpoints for video upload, neural scoring, stage-gate evaluation, and A/B testing.
"""

import json
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path

from flask import jsonify, request
from werkzeug.utils import secure_filename

from . import neurosim_bp
from ..config import Config
from ..services.ab_experiment import ABExperiment
from ..services.bridge import NeuroSocialBridge
from ..services.heuristic_scorer import HeuristicScorer
from ..services.stage_gate import StageGate
from ..services.video_processor import VideoProcessor
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.neurosim')

video_processor = VideoProcessor()
heuristic_scorer = HeuristicScorer()
stage_gate = StageGate()
neuro_bridge = NeuroSocialBridge()
ab_experiment = ABExperiment()

NEUROSIM_DIR = Path(Config.UPLOAD_FOLDER) / 'neurosim'
UPLOAD_DIR = NEUROSIM_DIR / 'uploads'
VIDEO_JOB_DIR = NEUROSIM_DIR / 'video_jobs'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_JOB_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm'}


def _allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


def _utc_now() -> str:
    return datetime.utcnow().isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _video_job_path(video_id: str) -> Path:
    return VIDEO_JOB_DIR / f"{video_id}.json"


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix('.tmp')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def _read_json(path: Path):
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_video_job(video_id: str, data: dict) -> None:
    data['updated_at'] = _utc_now()
    _write_json(_video_job_path(video_id), data)


def _load_video_job(video_id: str):
    return _read_json(_video_job_path(video_id))


def _start_background_thread(target, *args) -> None:
    thread = threading.Thread(target=target, args=args, daemon=True)
    thread.start()


def _process_video_file(video_id: str, video_path: str) -> dict:
    processed = video_processor.process_video(video_path)
    roi_scores = heuristic_scorer.score_content(
        transcript=processed['transcript'],
        frame_count=processed['frame_count'],
        duration_seconds=processed['duration_seconds'],
    )
    gate_result = stage_gate.evaluate(roi_scores)
    bridge_params = neuro_bridge.map_to_simulation_params(roi_scores)
    personas = neuro_bridge.generate_persona_weights(roi_scores)

    return {
        'video_id': video_id,
        'frame_count': processed['frame_count'],
        'duration_seconds': processed['duration_seconds'],
        'transcript': processed['transcript'][:1000],
        'roi_scores': roi_scores,
        'stage_gate': gate_result,
        'bridge_params': bridge_params,
        'personas': personas,
    }


def _process_video_job(video_id: str, save_path: str) -> None:
    job = _load_video_job(video_id) or {'video_id': video_id}
    try:
        result = _process_video_file(video_id, save_path)
        job.update(result)
        job['status'] = 'complete'
        _save_video_job(video_id, job)
        logger.info("Video processing complete: %s", video_id)
    except Exception as e:
        logger.error("Video processing failed for %s: %s", video_id, e)
        job['status'] = 'error'
        job['error'] = str(e)
        _save_video_job(video_id, job)


def _save_upload(file_storage, prefix: str) -> tuple[str, str]:
    video_id = _new_id(prefix)
    filename = secure_filename(file_storage.filename or f"{video_id}.mp4")
    save_path = UPLOAD_DIR / f"{video_id}_{filename}"
    file_storage.save(str(save_path))
    return video_id, str(save_path)


@neurosim_bp.route('/upload', methods=['POST'])
def upload_video():
    """
    Upload a video file and start background processing.

    Returns immediately:
        {"video_id": "video_xxx", "status": "processing"}
    Poll GET /api/neurosim/video/<video_id>/status for final scores.
    """
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({'error': 'No video file selected'}), 400

    if not _allowed_file(video_file.filename):
        return jsonify({'error': f'Unsupported file type. Allowed: {sorted(ALLOWED_VIDEO_EXTENSIONS)}'}), 400

    context = request.form.get('context', '')
    video_id, save_path = _save_upload(video_file, 'video')

    job = {
        'video_id': video_id,
        'status': 'processing',
        'filename': os.path.basename(save_path),
        'path': save_path,
        'context': context,
        'created_at': _utc_now(),
    }
    _save_video_job(video_id, job)
    logger.info("Video uploaded: %s (%s bytes)", job['filename'], os.path.getsize(save_path))

    _start_background_thread(_process_video_job, video_id, save_path)
    return jsonify({'video_id': video_id, 'status': 'processing'})


@neurosim_bp.route('/analyze', methods=['POST'])
def analyze_video():
    """
    Synchronous full-pipeline analysis.

    Accepts 'file' or 'video' form field.
    Returns complete NeuroSim-compatible result with all scores.
    """
    video_file = request.files.get('file') or request.files.get('video')
    if not video_file:
        return jsonify({'error': 'No video file provided (use field name "file" or "video")'}), 400
    if video_file.filename == '':
        return jsonify({'error': 'No video file selected'}), 400
    if not _allowed_file(video_file.filename):
        return jsonify({'error': f'Unsupported file type. Allowed: {sorted(ALLOWED_VIDEO_EXTENSIONS)}'}), 400

    video_id, save_path = _save_upload(video_file, 'video')
    logger.info("Analyze: processing %s synchronously", video_file.filename)

    try:
        result = _process_video_file(video_id, save_path)
    except Exception as e:
        logger.error("Analyze failed for %s: %s", video_id, e)
        return jsonify({'error': f'Processing failed: {e}'}), 500

    roi = result.get('roi_scores', {})
    a5 = roi.get('A5', 0.5)
    lo = roi.get('LO', 0.5)
    area45 = roi.get('Area45', 0.5)
    tpj = roi.get('TPJ', 0.5)

    gate = result.get('stage_gate', {})
    bridge = result.get('bridge_params', {})
    w_attn = bridge.get('attention_weight', (a5 + lo) / 2)

    hook_score = round((lo * 0.6 + a5 * 0.4) * 100, 1)
    authenticity_score = round((tpj * 0.5 + (1 - area45) * 0.5) * 100, 1)
    viral_potential = round(bridge.get('viral_propensity', area45 * 1.2) * 30, 1)
    success_probability = round((lo * 0.3 + a5 * 0.2 + area45 * 0.3 + tpj * 0.2) * 100, 1)
    p_share = min(area45 * 1.2, 1.0)
    final_sentiment = round((a5 + lo + tpj) / 3 * 100, 1)
    risk_score = round((1 - tpj) * 50 + final_sentiment * 0.2, 1)

    # Build simulated MiroFish swarm result
    import random
    persona_dist = {p['type']: round(p.get('weight', p['base_weight']) * 100, 1)
                    for p in result.get('personas', [])}
    sentiment_change = (w_attn - 0.5) * 0.2
    if sentiment_change > 0.05:
        viral_prediction = "High - Positive sentiment spreading"
    elif sentiment_change > 0:
        viral_prediction = "Moderate - Gradual positive momentum"
    else:
        viral_prediction = "Low - Stable but not growing"
    backlash_risk = "Low risk" if tpj > 0.5 else "Moderate risk" if tpj > 0.3 else "High risk"

    return jsonify({
        'video_id': video_id,
        'filename': video_file.filename,
        'status': 'analyzed',
        'hook_score': hook_score,
        'hook_details': {
            'strength': 'Strong' if lo > 0.6 else 'Moderate' if lo > 0.4 else 'Weak',
            'curiosity_gap_detected': tpj > 0.5,
            'question_detected': a5 > 0.4,
        },
        'authenticity_score': authenticity_score,
        'authenticity_details': {
            'authenticity_level': 'High' if authenticity_score > 70 else 'Moderate' if authenticity_score > 50 else 'Low',
            'brand_intrusion': 'Low' if area45 < 0.6 else 'High',
        },
        'viral_potential': viral_potential,
        'success_probability': success_probability,
        'risk_score': risk_score,
        'sentiment_forecast': {
            'positive_sentiment_pct': round(final_sentiment * 0.7, 1),
            'negative_sentiment_pct': round(100 - final_sentiment * 0.7 - 20, 1),
            'neutral_sentiment_pct': 20.0,
            'backlash_risk': backlash_risk,
            'shareability_index': round(p_share * 100, 1),
        },
        'mirofish_simulation': {
            'simulation_id': f'sim_{video_id}',
            'mode': 'simulated',
            'num_agents': 1000,
            'simulation_rounds': 20,
            'final_sentiment': final_sentiment,
            'viral_prediction': viral_prediction,
            'backlash_prediction': backlash_risk,
            'share_prediction': round(final_sentiment * 0.65 + 20, 1),
            'persona_distribution': persona_dist,
        },
        'tribev2_brain_response': {
            'cortical_response': {
                'visual_cortex': round(lo * 100, 1),
                'auditory_cortex': round(a5 * 100, 1),
                'language_center': round(tpj * 80, 1),
                'amygdala': round(tpj * 90, 1),
                'prefrontal_cortex': round(area45 * 95, 1),
                'reward_center': round(area45 * 100, 1),
                'social_cognition': round(tpj * 85, 1),
                'memory_formation': round((lo + a5) / 2 * 90, 1),
                'overall_response_strength': round((lo + a5 + area45 + tpj) / 4 * 100, 1),
            },
            'mode': 'simulated',
        },
        'stage_gate': {
            'passed': gate.get('passed', w_attn >= 0.4),
            'message': gate.get('message', ''),
            'W_attn': round(w_attn, 4),
            'threshold': gate.get('threshold', 0.4),
        },
        'recommendations': [
            'Add more visual contrast or motion in the first 3 seconds' if lo < 0.5 else 'Strong visual engagement — maintain current style',
            'Consider audio dynamic change or voice modulation' if a5 < 0.5 else 'Audio engagement is solid',
            'Strengthen value proposition or add social proof' if area45 < 0.5 else 'Good perceived value activation',
            f'Viral coefficient: {round(p_share * 2.8, 2)} — {"high potential" if p_share > 0.7 else "moderate spread"}',
        ],
        'created_at': _utc_now(),
    })


@neurosim_bp.route('/video/<video_id>/status', methods=['GET'])
def get_video_status(video_id: str):
    """Get background video processing status and scores when complete."""
    job = _load_video_job(video_id)
    if not job:
        return jsonify({'error': 'Video job not found'}), 404
    response = {k: v for k, v in job.items() if k != 'path'}
    return jsonify(response)


@neurosim_bp.route('/evaluate', methods=['POST'])
def evaluate_content():
    """Evaluate text-only content without video upload."""
    data = request.get_json() or {}
    transcript = data.get('transcript', '')

    if not transcript or len(transcript.strip()) < 10:
        return jsonify({'error': 'Transcript too short (minimum 10 characters)'}), 400

    roi_scores = heuristic_scorer.score_content(transcript=transcript)
    gate_result = stage_gate.evaluate(roi_scores)
    bridge_params = neuro_bridge.map_to_simulation_params(roi_scores)
    personas = neuro_bridge.generate_persona_weights(roi_scores)

    return jsonify({
        'roi_scores': roi_scores,
        'stage_gate': gate_result,
        'bridge_params': bridge_params,
        'personas': personas,
    })


@neurosim_bp.route('/ab-test', methods=['POST'])
def create_ab_test():
    """
    Create an A/B test experiment.

    Multipart requests return an experiment ID immediately, then process videos and
    run the A/B simulation in the background.
    """
    if request.content_type and 'multipart' in request.content_type:
        if 'video_a' not in request.files or 'video_b' not in request.files:
            return jsonify({'error': 'Both video_a and video_b files required'}), 400

        video_a = request.files['video_a']
        video_b = request.files['video_b']
        context = request.form.get('context', '')
        num_agents = request.form.get('num_agents', 100, type=int)
        num_rounds = request.form.get('num_rounds', 10, type=int)

        if not _allowed_file(video_a.filename) or not _allowed_file(video_b.filename):
            return jsonify({'error': f'Unsupported file type. Allowed: {sorted(ALLOWED_VIDEO_EXTENSIONS)}'}), 400

        video_id_a, save_path_a = _save_upload(video_a, 'video')
        video_id_b, save_path_b = _save_upload(video_b, 'video')
        exp_id = ab_experiment.create_pending_experiment(
            variant_a={'video_id': video_id_a},
            variant_b={'video_id': video_id_b},
            simulation_requirements=context,
            num_agents=num_agents,
            num_rounds=num_rounds,
        )

        def _process_and_run():
            try:
                processed_a = _process_video_file(video_id_a, save_path_a)
                processed_b = _process_video_file(video_id_b, save_path_b)
                ab_experiment.update_experiment_variants(exp_id, processed_a, processed_b)
                ab_experiment.run_simulation_async(exp_id)
            except Exception as e:
                logger.error("A/B test creation failed for %s: %s", exp_id, e)
                ab_experiment.fail_experiment(exp_id, str(e))

        _start_background_thread(_process_and_run)
        return jsonify({'experiment_id': exp_id, 'status': 'processing'})

    data = request.get_json() or {}
    variant_a = data.get('variant_a', {})
    variant_b = data.get('variant_b', {})
    context = data.get('simulation_requirements', '')
    num_agents = data.get('num_agents', 100)
    num_rounds = data.get('num_rounds', 10)

    if not variant_a.get('transcript') or not variant_b.get('transcript'):
        return jsonify({'error': 'Both variants require transcript field'}), 400

    roi_a = heuristic_scorer.score_content(transcript=variant_a['transcript'])
    roi_b = heuristic_scorer.score_content(transcript=variant_b['transcript'])
    variant_a['roi_scores'] = roi_a
    variant_b['roi_scores'] = roi_b

    exp_id = ab_experiment.create_experiment(
        variant_a=variant_a,
        variant_b=variant_b,
        simulation_requirements=context,
        num_agents=num_agents,
        num_rounds=num_rounds,
    )
    ab_experiment.run_simulation_async(exp_id)

    return jsonify({'experiment_id': exp_id, 'status': 'running'})


@neurosim_bp.route('/ab-test/<experiment_id>', methods=['GET'])
def get_ab_test(experiment_id: str):
    """Get A/B experiment status and results."""
    exp = ab_experiment.get_experiment(experiment_id)
    if not exp:
        return jsonify({'error': 'Experiment not found'}), 404
    return jsonify(exp)


@neurosim_bp.route('/ab-test/<experiment_id>/results', methods=['GET'])
def get_ab_test_results(experiment_id: str):
    """Get A/B experiment results."""
    exp = ab_experiment.get_experiment(experiment_id)
    if not exp:
        return jsonify({'error': 'Experiment not found'}), 404

    status = exp.get('status')
    if status != 'completed':
        message_by_status = {
            'processing': 'Video processing still running',
            'created': 'Simulation is queued',
            'running': 'Simulation still running',
            'failed': exp.get('error', 'Experiment failed'),
        }
        return jsonify({
            'experiment_id': experiment_id,
            'status': status,
            'message': message_by_status.get(status, 'Experiment is not complete'),
        })

    return jsonify({
        'experiment_id': experiment_id,
        'id': experiment_id,
        'status': status,
        'variant_a': {
            'roi_scores': exp['variant_a']['roi_scores'],
            'stage_gate': exp['variant_a']['stage_gate'],
            'result': exp['variant_a']['result'],
        },
        'variant_b': {
            'roi_scores': exp['variant_b']['roi_scores'],
            'stage_gate': exp['variant_b']['stage_gate'],
            'result': exp['variant_b']['result'],
        },
        'comparison': exp['comparison'],
    })


@neurosim_bp.route('/experiments', methods=['GET'])
def list_experiments():
    """List all A/B experiments."""
    experiments = ab_experiment.list_experiments()
    return jsonify({'experiments': experiments})


@neurosim_bp.route('/bridge', methods=['POST'])
def calculate_bridge():
    """Calculate bridge parameters from ROI scores."""
    data = request.get_json() or {}
    roi_scores = data.get('roi_scores', {})

    if not roi_scores:
        return jsonify({'error': 'roi_scores required'}), 400

    bridge_params = neuro_bridge.map_to_simulation_params(roi_scores)
    personas = neuro_bridge.generate_persona_weights(roi_scores)

    return jsonify({
        'bridge_params': bridge_params,
        'personas': personas,
    })
