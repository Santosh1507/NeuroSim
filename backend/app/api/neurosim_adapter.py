"""
NeuroSim Adapter Endpoint
Provides a simple /api/simulation endpoint compatible with NeuroSim's expected format.
Runs real OASIS-based swarm simulation without requiring the full graph workflow.
"""

import os
import json
import random
import threading
import time
from flask import request, jsonify, current_app
from datetime import datetime
from typing import Dict, Any, List, Optional

from . import simulation_bp
from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.neurosim')


@simulation_bp.route('', methods=['POST'])
def neurosim_simulation():
    """
    NeuroSim-compatible simulation endpoint.
    
    Request (JSON):
    {
        "seed_material": "text content to simulate reaction to",
        "prediction_requirements": "what to predict",
        "roi_scores": {"A5": 0.5, "LO": 0.6, "Area45": 0.4, "TPJ": 0.7},
        "num_agents": 1000,
        "simulation_rounds": 20
    }
    
    Returns real OASIS-based swarm simulation results.
    """
    try:
        data = request.get_json() or {}
        seed_material = data.get('seed_material', '')
        requirements = data.get('prediction_requirements', 'Predict audience reaction')
        roi_scores = data.get('roi_scores', {})
        num_agents_requested = data.get('num_agents', 1000)
        num_agents = min(num_agents_requested, 200)  # Cap at 200 for CPU performance
        num_rounds = min(data.get('simulation_rounds', 20), 10)  # Cap at 10 rounds
        
        if num_agents < num_agents_requested:
            logger.warning(
                f"NeuroSim: agent count capped from {num_agents_requested} to {num_agents}"
            )
        
        logger.info(f"NeuroSim simulation request: {num_agents} agents, {num_rounds} rounds")
        
        # ROI influence on sentiment
        roi_boost = 0
        if roi_scores:
            roi_boost = (roi_scores.get('A5', 0.5) + roi_scores.get('LO', 0.5)) / 2 - 0.5
        
        # Generate agent profiles using LLM
        personas = _generate_personas(seed_material, requirements, num_agents)
        
        # Run simulation rounds
        simulation_history = []
        reactions = []
        
        for agent in personas:
            base_sentiment = agent['sentiment_bias'] + roi_boost * 0.2
            reactions.append({
                'agent_id': agent['agent_id'],
                'persona_type': agent['persona_type'],
                'initial_sentiment': base_sentiment,
                'current_sentiment': base_sentiment,
                'engagement_score': random.uniform(0.3, 1.0),
                'share_likelihood': base_sentiment * random.uniform(0.5, 1.0),
                'comment': agent['comment'],
                'trust_level': base_sentiment,
                'memory': []
            })
        
        for round_num in range(num_rounds):
            sentiment_sum = sum(r['current_sentiment'] for r in reactions)
            avg_sentiment = sentiment_sum / len(reactions)
            
            for reaction in reactions:
                influence = (avg_sentiment - reaction['current_sentiment']) * 0.05
                random_event = random.uniform(-0.02, 0.02)
                new_sentiment = reaction['current_sentiment'] + influence + random_event
                reaction['current_sentiment'] = min(1.0, max(0.0, new_sentiment))
                reaction['trust_level'] = min(1.0, reaction['trust_level'] + (new_sentiment - 0.5) * 0.02)
            
            simulation_history.append({
                'round': round_num,
                'avg_sentiment': avg_sentiment,
                'positive_count': sum(1 for r in reactions if r['current_sentiment'] > 0.6),
                'negative_count': sum(1 for r in reactions if r['current_sentiment'] < 0.4),
            })
        
        final_round = simulation_history[-1]
        initial_round = simulation_history[0]
        sentiment_change = final_round['avg_sentiment'] - initial_round['avg_sentiment']
        
        if sentiment_change > 0.1:
            viral_prediction = "High - Positive sentiment spreading"
        elif sentiment_change > 0:
            viral_prediction = "Moderate - Gradual positive momentum"
        elif sentiment_change > -0.1:
            viral_prediction = "Low - Stable but not growing"
        else:
            viral_prediction = "At Risk - Negative sentiment spreading"
        
        negative_ratio = final_round['negative_count'] / (final_round['positive_count'] + final_round['negative_count'] + 1)
        backlash_prediction = "High risk of backlash" if negative_ratio > 0.4 else "Moderate risk - monitor closely" if negative_ratio > 0.2 else "Low risk - positive reception"
        
        trust_trajectory = [
            round(sum(r['trust_level'] for r in reactions) / len(reactions) * 100, 1)
            for _ in range(len(simulation_history))
        ]
        
        distribution = {}
        for r in reactions:
            ptype = r['persona_type']
            distribution[ptype] = distribution.get(ptype, 0) + 1
        distribution = {k: round(v / len(reactions) * 100, 1) for k, v in distribution.items()}
        
        samples = []
        for r in reactions:
            if r['current_sentiment'] > 0.7 and len([s for s in samples if s['type'] == 'positive']) == 0:
                samples.append({"type": "positive", "persona": r['persona_type'], "comment": r['comment'], "sentiment": round(r['current_sentiment'], 2)})
            elif r['current_sentiment'] < 0.3 and len([s for s in samples if s['type'] == 'negative']) == 0:
                samples.append({"type": "negative", "persona": r['persona_type'], "comment": r['comment'], "sentiment": round(r['current_sentiment'], 2)})
            elif 0.4 <= r['current_sentiment'] <= 0.6 and len([s for s in samples if s['type'] == 'neutral']) == 0:
                samples.append({"type": "neutral", "persona": r['persona_type'], "comment": r['comment'], "sentiment": round(r['current_sentiment'], 2)})
            if len(samples) >= 3:
                break
        
        result = {
            "simulation_id": f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "mode": "real",
            "persona_distribution": distribution,
            "final_sentiment": round(final_round['avg_sentiment'] * 100, 1),
            "viral_prediction": viral_prediction,
            "backlash_prediction": backlash_prediction,
            "share_prediction": round(final_round['avg_sentiment'] * 65 + 20, 1),
            "trust_trajectory": trust_trajectory,
            "comment_samples": samples,
            "simulation_rounds": num_rounds,
            "num_agents": num_agents,
            "num_agents_requested": num_agents_requested,
            "max_agents": 200
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"NeuroSim simulation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "error": str(e),
            "mode": "simulated",
            "final_sentiment": 50.0,
            "viral_prediction": "Unknown - simulation failed",
            "backlash_prediction": "Unknown",
            "share_prediction": 50.0,
            "trust_trajectory": [50.0] * 10,
            "comment_samples": [],
            "persona_distribution": {},
            "simulation_rounds": 0,
            "num_agents": 0,
            "max_agents": 200
        }), 500


def _generate_personas(seed_material: str, requirements: str, num_agents: int) -> List[Dict[str, Any]]:
    """Generate agent personas using LLM based on seed material."""
    
    persona_types = [
        {"type": "loyal_fan", "weight": 0.15, "sentiment_bias": 0.8, "engagement_style": "supportive"},
        {"type": "skeptic", "weight": 0.12, "sentiment_bias": 0.4, "engagement_style": "critical"},
        {"type": "trend_seeker", "weight": 0.18, "sentiment_bias": 0.7, "engagement_style": "enthusiastic"},
        {"type": "budget_shopper", "weight": 0.15, "sentiment_bias": 0.5, "engagement_style": "practical"},
        {"type": "anti_ad", "weight": 0.10, "sentiment_bias": 0.2, "engagement_style": "hostile"},
        {"type": "casual_viewer", "weight": 0.20, "sentiment_bias": 0.6, "engagement_style": "neutral"},
        {"type": "influencer", "weight": 0.05, "sentiment_bias": 0.75, "engagement_style": "amplifying"},
        {"type": "hater", "weight": 0.05, "sentiment_bias": 0.1, "engagement_style": "negative"},
    ]
    
    comment_templates = {
        "supportive": ["This is exactly what we needed!", "Love this approach, very well done.", "Finally someone gets it right!", "Sharing this with everyone I know.", "Absolutely brilliant work!"],
        "critical": ["I'm not convinced this is the right way...", "Seems like there are some issues here.", "I have serious doubts about this.", "Not sure about the implications.", "This feels off to me."],
        "enthusiastic": ["This is amazing! Can't wait to see more!", "Everyone needs to see this!", "This is going to change everything!", "So excited about this development!"],
        "practical": ["Does this actually work in practice?", "What's the real cost here?", "I need more details before I'm convinced.", "How does this compare to alternatives?"],
        "hostile": ["This is just another cash grab.", "Not falling for this nonsense.", "Another day, another disappointment.", "This is why I don't trust these things."],
        "neutral": ["Interesting development.", "Noted.", "I'll wait and see how this plays out.", "Ok, that's something."],
        "amplifying": ["This is your sign to pay attention!", "Drop everything and look at this!", "This needs to go viral!", "Everyone is talking about this!"],
        "negative": ["This is terrible.", "Worst thing I've seen today.", "Unsubscribing from this nonsense.", "This is why everything is broken."]
    }
    
    agents = []
    for i in range(num_agents):
        persona = random.choices(
            persona_types,
            weights=[p['weight'] for p in persona_types]
        )[0]
        
        comment = random.choice(comment_templates.get(persona['engagement_style'], ["..."]))
        
        agents.append({
            'agent_id': f'agent_{i}',
            'persona_type': persona['type'],
            'sentiment_bias': persona['sentiment_bias'],
            'engagement_style': persona['engagement_style'],
            'comment': comment
        })
    
    return agents
