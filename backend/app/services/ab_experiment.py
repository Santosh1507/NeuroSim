"""
A/B Experiment Service
Manages A/B experiments: creates experiments, runs dual simulations, stores results.
"""

import json
import uuid
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..config import Config
from ..utils.logger import get_logger
from .bridge import NeuroSocialBridge
from .stage_gate import StageGate

logger = get_logger('mirofish.ab_experiment')

# Storage directory for experiment data
EXPERIMENT_DIR = Path(Config.UPLOAD_FOLDER) / 'experiments'
EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)


class ABExperiment:
    """Manages A/B content experiments with dual simulation orchestration."""

    def __init__(self):
        self.bridge = NeuroSocialBridge()
        self.stage_gate = StageGate()
        self._experiments: Dict[str, Dict[str, Any]] = {}
        self._load_experiments()

    def create_experiment(
        self,
        variant_a: Dict[str, Any],
        variant_b: Dict[str, Any],
        simulation_requirements: str = "",
        num_agents: int = 100,
        num_rounds: int = 10,
    ) -> str:
        """
        Create a new A/B experiment.

        Args:
            variant_a: Dict with video_id, transcript, roi_scores, etc.
            variant_b: Dict with video_id, transcript, roi_scores, etc.
            simulation_requirements: What to simulate/predict.
            num_agents: Number of agents per simulation.
            num_rounds: Number of simulation rounds.

        Returns:
            Experiment ID string.
        """
        experiment_id = f"ab_{uuid.uuid4().hex[:12]}"

        # Evaluate stage-gate for both variants
        gate_a = self.stage_gate.evaluate(variant_a.get('roi_scores', {}))
        gate_b = self.stage_gate.evaluate(variant_b.get('roi_scores', {}))

        # Generate bridge params for both
        bridge_a = self.bridge.map_to_simulation_params(variant_a.get('roi_scores', {}))
        bridge_b = self.bridge.map_to_simulation_params(variant_b.get('roi_scores', {}))

        # Generate persona weights
        personas_a = self.bridge.generate_persona_weights(variant_a.get('roi_scores', {}))
        personas_b = self.bridge.generate_persona_weights(variant_b.get('roi_scores', {}))

        experiment = {
            'id': experiment_id,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'created',
            'simulation_requirements': simulation_requirements,
            'num_agents': num_agents,
            'num_rounds': num_rounds,
            'variant_a': {
                'video_id': variant_a.get('video_id', ''),
                'transcript': variant_a.get('transcript', '')[:500],
                'roi_scores': variant_a.get('roi_scores', {}),
                'stage_gate': gate_a,
                'bridge_params': bridge_a,
                'personas': personas_a,
                'result': None,
            },
            'variant_b': {
                'video_id': variant_b.get('video_id', ''),
                'transcript': variant_b.get('transcript', '')[:500],
                'roi_scores': variant_b.get('roi_scores', {}),
                'stage_gate': gate_b,
                'bridge_params': bridge_b,
                'personas': personas_b,
                'result': None,
            },
            'comparison': None,
        }

        self._experiments[experiment_id] = experiment
        self._save_experiment(experiment_id, experiment)

        logger.info(f"Created A/B experiment: {experiment_id}")
        return experiment_id

    def create_pending_experiment(
        self,
        variant_a: Dict[str, Any],
        variant_b: Dict[str, Any],
        simulation_requirements: str = "",
        num_agents: int = 100,
        num_rounds: int = 10,
    ) -> str:
        """Create an experiment before expensive video processing completes."""
        experiment_id = f"ab_{uuid.uuid4().hex[:12]}"
        experiment = {
            'id': experiment_id,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'processing',
            'simulation_requirements': simulation_requirements,
            'num_agents': num_agents,
            'num_rounds': num_rounds,
            'variant_a': self._empty_variant(variant_a),
            'variant_b': self._empty_variant(variant_b),
            'comparison': None,
        }
        self._experiments[experiment_id] = experiment
        self._save_experiment(experiment_id, experiment)
        logger.info(f"Created pending A/B experiment: {experiment_id}")
        return experiment_id

    def update_experiment_variants(
        self,
        experiment_id: str,
        variant_a: Dict[str, Any],
        variant_b: Dict[str, Any],
    ) -> bool:
        """Attach processed variant data to a pending experiment."""
        exp = self._experiments.get(experiment_id)
        if not exp:
            return False

        exp['variant_a'] = self._build_variant(variant_a)
        exp['variant_b'] = self._build_variant(variant_b)
        exp['status'] = 'created'
        self._save_experiment(experiment_id, exp)
        return True

    def fail_experiment(self, experiment_id: str, error: str) -> bool:
        """Mark an experiment as failed and persist the error."""
        exp = self._experiments.get(experiment_id)
        if not exp:
            return False
        exp['status'] = 'failed'
        exp['error'] = error
        self._save_experiment(experiment_id, exp)
        return True

    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment by ID."""
        return self._experiments.get(experiment_id)

    def list_experiments(self) -> List[Dict[str, Any]]:
        """List all experiments (summary only)."""
        return [
            {
                'id': exp['id'],
                'created_at': exp['created_at'],
                'status': exp['status'],
                'variant_a_gate': (exp['variant_a'].get('stage_gate') or {}).get('gate_score'),
                'variant_b_gate': (exp['variant_b'].get('stage_gate') or {}).get('gate_score'),
            }
            for exp in self._experiments.values()
        ]

    def run_simulation_async(
        self,
        experiment_id: str,
        simulation_runner=None,
    ) -> Dict[str, Any]:
        """
        Start dual simulation in background thread.

        Args:
            experiment_id: The experiment to run.
            simulation_runner: Optional SimulationRunner instance for real OASIS simulation.

        Returns:
            Experiment status dict.
        """
        exp = self._experiments.get(experiment_id)
        if not exp:
            return {'error': 'Experiment not found'}

        exp['status'] = 'running'
        self._save_experiment(experiment_id, exp)

        def _run():
            try:
                # Run simulation for variant A
                result_a = self._run_single_simulation(
                    exp['variant_a'],
                    exp['num_agents'],
                    exp['num_rounds'],
                    simulation_runner,
                )
                exp['variant_a']['result'] = result_a

                # Run simulation for variant B
                result_b = self._run_single_simulation(
                    exp['variant_b'],
                    exp['num_agents'],
                    exp['num_rounds'],
                    simulation_runner,
                )
                exp['variant_b']['result'] = result_b

                # Compare results
                exp['comparison'] = self._compare_results(result_a, result_b)
                exp['status'] = 'completed'

                self._save_experiment(experiment_id, exp)
                logger.info(f"Experiment {experiment_id} completed")

            except Exception as e:
                logger.error(f"Experiment {experiment_id} failed: {e}")
                exp['status'] = 'failed'
                exp['error'] = str(e)
                self._save_experiment(experiment_id, exp)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        return {'id': experiment_id, 'status': 'running'}

    def _empty_variant(self, variant: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'video_id': variant.get('video_id', ''),
            'transcript': variant.get('transcript', ''),
            'roi_scores': {},
            'stage_gate': None,
            'bridge_params': None,
            'personas': None,
            'result': None,
        }

    def _build_variant(self, variant: Dict[str, Any]) -> Dict[str, Any]:
        roi_scores = variant.get('roi_scores', {})
        return {
            'video_id': variant.get('video_id', ''),
            'transcript': variant.get('transcript', '')[:500],
            'roi_scores': roi_scores,
            'stage_gate': self.stage_gate.evaluate(roi_scores),
            'bridge_params': self.bridge.map_to_simulation_params(roi_scores),
            'personas': self.bridge.generate_persona_weights(roi_scores),
            'result': variant.get('result'),
        }

    def _run_single_simulation(
        self,
        variant: Dict[str, Any],
        num_agents: int,
        num_rounds: int,
        simulation_runner=None,
    ) -> Dict[str, Any]:
        """
        Run a single simulation for one variant.

        If simulation_runner is provided, uses real OASIS simulation.
        Otherwise, uses heuristic simulation.
        """
        bridge_params = variant['bridge_params']
        personas = variant['personas']
        roi_scores = variant['roi_scores']

        if simulation_runner:
            # TODO: Integrate with real OASIS simulation
            # For now, use heuristic simulation
            pass

        # Heuristic simulation
        import random

        attention = bridge_params['attention_weight']
        viral = bridge_params['viral_propensity']
        social = bridge_params['social_engagement']

        # Simulate rounds
        history = []
        sentiment = 0.5  # Starting sentiment

        for round_num in range(num_rounds):
            # Sentiment drift based on viral propensity and attention
            drift = (viral - 1.0) * 0.05 + (attention - 0.5) * 0.03
            noise = random.uniform(-0.02, 0.02)
            sentiment = max(0.0, min(1.0, sentiment + drift + noise))

            positive = int(num_agents * sentiment * 0.8)
            negative = int(num_agents * (1 - sentiment) * 0.6)
            neutral = num_agents - positive - negative

            history.append({
                'round': round_num,
                'avg_sentiment': round(sentiment, 3),
                'positive_count': positive,
                'negative_count': negative,
                'neutral_count': max(0, neutral),
            })

        final_sentiment = history[-1]['avg_sentiment'] if history else 0.5

        # Predict outcomes
        if final_sentiment > 0.65:
            viral_prediction = "High - Strong positive momentum"
        elif final_sentiment > 0.5:
            viral_prediction = "Moderate - Gradual positive trend"
        elif final_sentiment > 0.4:
            viral_prediction = "Low - Stable but not growing"
        else:
            viral_prediction = "At Risk - Negative sentiment spreading"

        negative_ratio = history[-1]['negative_count'] / max(num_agents, 1)
        if negative_ratio > 0.4:
            backlash_prediction = "High risk of backlash"
        elif negative_ratio > 0.2:
            backlash_prediction = "Moderate risk - monitor closely"
        else:
            backlash_prediction = "Low risk - positive reception"

        return {
            'final_sentiment': round(final_sentiment * 100, 1),
            'viral_prediction': viral_prediction,
            'backlash_prediction': backlash_prediction,
            'share_likelihood': round(attention * viral * 70 + 15, 1),
            'engagement_score': round(social * 80 + 10, 1),
            'history': history,
            'roi_scores': roi_scores,
            'num_agents': num_agents,
            'num_rounds': num_rounds,
        }

    def _compare_results(
        self,
        result_a: Dict[str, Any],
        result_b: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compare two simulation results and determine winner."""
        sentiment_a = result_a['final_sentiment']
        sentiment_b = result_b['final_sentiment']

        sentiment_diff = sentiment_a - sentiment_b

        if abs(sentiment_diff) < 5:
            winner = "tie"
            confidence = "low"
        elif sentiment_diff > 0:
            winner = "A"
            confidence = "high" if sentiment_diff > 15 else "moderate"
        else:
            winner = "B"
            confidence = "high" if abs(sentiment_diff) > 15 else "moderate"

        return {
            'winner': winner,
            'confidence': confidence,
            'sentiment_diff': round(sentiment_diff, 1),
            'variant_a_sentiment': sentiment_a,
            'variant_b_sentiment': sentiment_b,
            'variant_a_viral': result_a['viral_prediction'],
            'variant_b_viral': result_b['viral_prediction'],
            'variant_a_backlash': result_a['backlash_prediction'],
            'variant_b_backlash': result_b['backlash_prediction'],
            'recommendation': self._generate_recommendation(winner, confidence, sentiment_diff),
        }

    def _generate_recommendation(self, winner: str, confidence: str, diff: float) -> str:
        """Generate human-readable recommendation."""
        if winner == "tie":
            return "Both variants perform similarly. Consider testing with different audience segments or revising both versions."
        elif winner == "A":
            strength = "significantly" if confidence == "high" else "slightly"
            return f"Variant A performs {strength} better (sentiment +{diff:.1f}%). Recommend proceeding with Variant A."
        else:
            strength = "significantly" if confidence == "high" else "slightly"
            return f"Variant B performs {strength} better (sentiment +{abs(diff):.1f}%). Recommend proceeding with Variant B."

    def _save_experiment(self, experiment_id: str, experiment: Dict[str, Any]):
        """Save experiment to disk."""
        try:
            # Truncate transcript for storage
            exp_copy = json.loads(json.dumps(experiment))
            for v in ['variant_a', 'variant_b']:
                if exp_copy.get(v, {}).get('transcript'):
                    exp_copy[v]['transcript'] = exp_copy[v]['transcript'][:200]

            file_path = EXPERIMENT_DIR / f"{experiment_id}.json"
            with open(file_path, 'w') as f:
                json.dump(exp_copy, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save experiment {experiment_id}: {e}")

    def _load_experiments(self):
        """Load experiments from disk."""
        try:
            for file_path in EXPERIMENT_DIR.glob('ab_*.json'):
                with open(file_path) as f:
                    exp = json.load(f)
                    self._experiments[exp['id']] = exp
            logger.info(f"Loaded {len(self._experiments)} experiments from disk")
        except Exception as e:
            logger.warning(f"Failed to load experiments: {e}")
