"""
TRIBE v2 Integration - Brain Response Prediction
Predicts fMRI brain responses to video, audio, and text stimuli.
"""

import os
import json
import traceback
import threading
from pathlib import Path
from flask import request, jsonify, current_app

from . import tribev2_bp
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.tribev2')

_TRIBE_MODEL = None
_MODEL_LOADING = False
_MODEL_ERROR = None
_LOADING_LOCK = threading.Lock()

_ALLOWED_BASE_DIRS = [
    Path(os.environ.get('TRIBE_MEDIA_DIR', './media')).resolve(),
    Path(os.environ.get('TRIBE_CACHE_DIR', './cache')).resolve(),
]


def _validate_path(path_str: str) -> tuple:
    """
    Validate that a file path is within an allowed base directory.
    Returns (resolved_path, error_info) where error_info is (message, status) or None.
    """
    try:
        resolved = Path(path_str).resolve()
    except Exception:
        return None, (f'Invalid path: {path_str}', 400)

    for base in _ALLOWED_BASE_DIRS:
        if resolved.is_relative_to(base):
            return resolved, None

    return None, (f'Path not within allowed directories: {path_str}', 403)

_TRIBE_MODEL = None
_MODEL_LOADING = False
_MODEL_ERROR = None
_LOADING_LOCK = threading.Lock()


def get_tribe_model():
    """
    Returns (model, error_response) tuple.
    - (model, None) if loaded successfully
    - (None, (response, status)) if loading or failed
    """
    global _TRIBE_MODEL, _MODEL_LOADING, _MODEL_ERROR

    if _TRIBE_MODEL is not None:
        return _TRIBE_MODEL, None

    if _MODEL_ERROR is not None:
        return None, (
            jsonify({
                'success': False,
                'error': f'TribeV2 model failed to load: {_MODEL_ERROR}'
            }),
            500
        )

    if _MODEL_LOADING:
        return None, (
            jsonify({
                'success': False,
                'error': 'TribeV2 model is loading, please try again in a moment',
                'retry_after': 10
            }),
            503
        )

    return None, (
        jsonify({
            'success': False,
            'error': 'TribeV2 model not loaded. Call /api/tribev2/preload first.',
        }),
        503
    )


def load_tribe_model_async():
    """Load the TribeV2 model in a background thread."""
    global _TRIBE_MODEL, _MODEL_LOADING, _MODEL_ERROR

    with _LOADING_LOCK:
        if _TRIBE_MODEL is not None or _MODEL_LOADING:
            return
        _MODEL_LOADING = True

    try:
        logger.info("TribeV2: starting model download and load...")
        from tribev2 import TribeModel
        cache = os.environ.get('TRIBE_CACHE_DIR', './cache/tribev2')
        _TRIBE_MODEL = TribeModel.from_pretrained("facebook/tribev2", cache_folder=cache)
        logger.info("TribeV2 model loaded successfully")
    except Exception as e:
        logger.error(f"TribeV2 model failed to load: {e}")
        _MODEL_ERROR = str(e)
    finally:
        _MODEL_LOADING = False


@tribev2_bp.route('/preload', methods=['POST'])
def preload():
    """Trigger async model loading. Returns immediately."""
    global _MODEL_LOADING
    if _TRIBE_MODEL is not None:
        return jsonify({
            "success": True,
            "data": {"status": "already_loaded", "model": "facebook/tribev2"}
        })
    if _MODEL_LOADING:
        return jsonify({
            "success": True,
            "data": {"status": "loading_in_progress", "model": "facebook/tribev2"}
        })
    threading.Thread(target=load_tribe_model_async, daemon=True).start()
    return jsonify({
        "success": True,
        "data": {"status": "loading_started", "model": "facebook/tribev2"}
    })


@tribev2_bp.route('/status', methods=['GET'])
def status():
    return jsonify({
        "success": True,
        "data": {
            "model": "facebook/tribev2",
            "loaded": _TRIBE_MODEL is not None,
            "loading": _MODEL_LOADING,
            "error": _MODEL_ERROR,
            "description": "Multimodal brain response prediction (fMRI) from video/audio/text"
        }
    })


@tribev2_bp.route('/predict', methods=['POST'])
def predict():
    """
    Predict brain responses from media file.

    Request (multipart/form-data or JSON):
      - file: media file upload and server_path: path on server or
      - video_path / audio_path / text_path: path to local file

    Returns:
      Prediction results with cortical vertex responses
    """
    try:
        data = request.get_json(silent=True) or {}
        video_path = data.get('video_path') or request.form.get('video_path')
        audio_path = data.get('audio_path') or request.form.get('audio_path')
        text_path = data.get('text_path') or request.form.get('text_path')

        # Validate the provided path
        raw_path = video_path or audio_path or text_path
        if not raw_path:
            return jsonify({
                "success": False,
                "error": "Provide video_path, audio_path, or text_path"
            }), 400

        resolved, err = _validate_path(raw_path)
        if err is not None:
            message, status = err
            return jsonify({'success': False, 'error': message}), status

        model, err = get_tribe_model()
        if err is not None:
            return err

        if video_path:
            logger.info(f"TribeV2: predicting from video: {resolved}")
            df = model.get_events_dataframe(video_path=str(resolved))
        elif audio_path:
            logger.info(f"TribeV2: predicting from audio: {resolved}")
            df = model.get_events_dataframe(audio_path=str(resolved))
        elif text_path:
            logger.info(f"TribeV2: predicting from text: {resolved}")
            df = model.get_events_dataframe(text_path=str(resolved))

        preds, segments = model.predict(events=df)

        return jsonify({
            "success": True,
            "data": {
                "shape": list(preds.shape),
                "n_timesteps": preds.shape[0],
                "n_vertices": preds.shape[1],
                "segments": segments,
                "predictions_sample": preds[:5, :5].tolist()
            }
        })

    except Exception as e:
        logger.error(f"TribeV2 prediction failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500
