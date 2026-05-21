import asyncio
import hashlib
import logging
import random as _random
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from config import settings

logger = logging.getLogger(__name__)


class MiroFishEngine:
    """
    MiroFish Swarm Intelligence Integration

    Real mode: Calls MiroFish API at localhost:5001
    Simulated mode: Runs local swarm simulation with 1000 agents
    """

    def __init__(self):
        self.is_real = settings.mirofish_use_real
        self.api_url = settings.mirofish_api_url

        self.personas = [
            {
                "type": "loyal_fan",
                "weight": 0.15,
                "sentiment_bias": 0.8,
                "engagement_style": "supportive",
            },
            {
                "type": "skeptic",
                "weight": 0.12,
                "sentiment_bias": 0.4,
                "engagement_style": "critical",
            },
            {
                "type": "trend_seeker",
                "weight": 0.18,
                "sentiment_bias": 0.7,
                "engagement_style": "enthusiastic",
            },
            {
                "type": "budget_shopper",
                "weight": 0.15,
                "sentiment_bias": 0.5,
                "engagement_style": "practical",
            },
            {
                "type": "anti_ad",
                "weight": 0.10,
                "sentiment_bias": 0.2,
                "engagement_style": "hostile",
            },
            {
                "type": "casual_viewer",
                "weight": 0.20,
                "sentiment_bias": 0.6,
                "engagement_style": "neutral",
            },
            {
                "type": "influencer",
                "weight": 0.05,
                "sentiment_bias": 0.75,
                "engagement_style": "amplifying",
            },
            {
                "type": "hater",
                "weight": 0.05,
                "sentiment_bias": 0.1,
                "engagement_style": "negative",
            },
        ]

    async def run_simulation(
        self,
        content: Dict[str, Any],
        roi_scores: Optional[Dict[str, float]] = None,
        num_agents: int = 1000,
        simulation_rounds: int = 20,
    ) -> Dict[str, Any]:
        if self.is_real:
            return await self._real_simulation(content, roi_scores)
        return await self._simulated_simulation(content, roi_scores, num_agents, simulation_rounds)

    async def _real_simulation(
        self, content: Dict[str, Any], roi_scores: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "seed_material": content.get("transcript", ""),
                    "prediction_requirements": content.get(
                        "requirements", "Predict audience reaction"
                    ),
                    "roi_scores": roi_scores or {},
                    "num_agents": 1000,
                    "simulation_rounds": 20,
                }

                response = await client.post(f"{self.api_url}/api/simulation", json=payload)

                if response.status_code == 200:
                    result = response.json()
                    result["mode"] = "real"
                    return result

                raise Exception(f"MiroFish API returned {response.status_code}")
        except Exception as e:
            logger.warning(f"MiroFish real API failed: {e}. Falling back to simulated mode.")
            return await self._simulated_simulation(content, roi_scores)

    @staticmethod
    def _derive_seed(content: Dict[str, Any], roi_scores: Optional[Dict[str, float]] = None) -> int:
        """Derive a deterministic seed from content features and ROI scores.

        Different inputs produce different seeds, so different outputs.
        Same inputs produce the same seed, so consistent results.
        """
        text = content.get("transcript", "")
        # Hash transcript length, word count, and content into a single seed
        seed_material = str(len(text)) + "::" + str(len(text.split())) + "::" + text[:500]
        if roi_scores:
            roi_str = "|".join(f"{k}={v}" for k, v in sorted(roi_scores.items()))
            seed_material += "::roi:" + roi_str
        # Take first 8 hex chars of SHA-256
        digest = hashlib.sha256(seed_material.encode()).hexdigest()[:8]
        return int(digest, 16)

    async def _simulated_simulation(
        self,
        content: Dict[str, Any],
        roi_scores: Optional[Dict[str, float]] = None,
        num_agents: int = 1000,
        simulation_rounds: int = 20,
    ) -> Dict[str, Any]:
        # Simulated mode: no artificial delay. The simulation is instant.
        # Previously slept 0.8s to "feel real" — that was misleading.
        # Derive a deterministic seed so same input = same output
        seed = self._derive_seed(content, roi_scores)
        rng = _random.Random(seed)

        roi_boost = 0
        if roi_scores:
            roi_boost = (roi_scores.get("A5", 0.5) + roi_scores.get("LO", 0.5)) / 2 - 0.5

        reactions = []
        for i in range(num_agents):
            persona = rng.choices(self.personas, weights=[p["weight"] for p in self.personas])[0]

            base_sentiment = persona["sentiment_bias"] + roi_boost * 0.2
            sentiment = min(1.0, max(0.0, base_sentiment + rng.uniform(-0.1, 0.1)))

            comment_types = {
                "supportive": ["omg love this!", "finally someone said it", "this is everything"],
                "critical": ["not convinced...", "this feels off"],
                "enthusiastic": ["sharing this!", "everyone needs to see this"],
                "practical": ["honest review: worth it?", "does this actually work?"],
                "hostile": ["another ad...", "not falling for this"],
                "neutral": ["interesting", "ok cool", "noted"],
                "amplifying": ["this is your sign", "drop everything and watch"],
                "negative": ["unsubscribing", "this is why i hate sponsored content"],
            }

            reactions.append(
                {
                    "agent_id": f"agent_{i}",
                    "persona_type": persona["type"],
                    "initial_sentiment": sentiment,
                    "current_sentiment": sentiment,
                    "engagement_score": rng.uniform(0.3, 1.0),
                    "share_likelihood": sentiment * rng.uniform(0.5, 1.0),
                    "comment": rng.choice(
                        comment_types.get(persona["engagement_style"], ["..."])
                    ),
                    "trust_level": sentiment,
                    "memory": [],
                }
            )

        simulation_history = []
        for round_num in range(simulation_rounds):
            sentiment_sum = sum(r["current_sentiment"] for r in reactions)
            avg_sentiment = sentiment_sum / len(reactions)

            for reaction in reactions:
                influence = (avg_sentiment - reaction["current_sentiment"]) * 0.05
                random_event = rng.uniform(-0.02, 0.02)
                new_sentiment = reaction["current_sentiment"] + influence + random_event
                reaction["current_sentiment"] = min(1.0, max(0.0, new_sentiment))
                reaction["trust_level"] = min(
                    1.0, reaction["trust_level"] + (new_sentiment - 0.5) * 0.02
                )

            simulation_history.append(
                {
                    "round": round_num,
                    "avg_sentiment": avg_sentiment,
                    "positive_count": sum(1 for r in reactions if r["current_sentiment"] > 0.6),
                    "negative_count": sum(1 for r in reactions if r["current_sentiment"] < 0.4),
                }
            )

        final_round = simulation_history[-1]
        initial_round = simulation_history[0]
        sentiment_change = final_round["avg_sentiment"] - initial_round["avg_sentiment"]

        if sentiment_change > 0.1:
            viral_prediction = "High - Positive sentiment spreading"
        elif sentiment_change > 0:
            viral_prediction = "Moderate - Gradual positive momentum"
        elif sentiment_change > -0.1:
            viral_prediction = "Low - Stable but not growing"
        else:
            viral_prediction = "At Risk - Negative sentiment spreading"

        negative_ratio = final_round["negative_count"] / (
            final_round["positive_count"] + final_round["negative_count"] + 1
        )
        backlash_prediction = (
            "High risk of backlash"
            if negative_ratio > 0.4
            else "Moderate risk - monitor closely"
            if negative_ratio > 0.2
            else "Low risk - positive reception"
        )

        trust_trajectory = [
            round(sum(r["trust_level"] for r in reactions) / len(reactions) * 100, 1)
            for _ in range(len(simulation_history))
        ]

        distribution = {}
        for r in reactions:
            ptype = r["persona_type"]
            distribution[ptype] = distribution.get(ptype, 0) + 1
        distribution = {k: round(v / len(reactions) * 100, 1) for k, v in distribution.items()}

        samples = []
        for r in reactions:
            if (
                r["current_sentiment"] > 0.7
                and len([s for s in samples if s["type"] == "positive"]) == 0
            ):
                samples.append(
                    {
                        "type": "positive",
                        "persona": r["persona_type"],
                        "comment": r["comment"],
                        "sentiment": round(r["current_sentiment"], 2),
                    }
                )
            elif (
                r["current_sentiment"] < 0.3
                and len([s for s in samples if s["type"] == "negative"]) == 0
            ):
                samples.append(
                    {
                        "type": "negative",
                        "persona": r["persona_type"],
                        "comment": r["comment"],
                        "sentiment": round(r["current_sentiment"], 2),
                    }
                )
            elif (
                0.4 <= r["current_sentiment"] <= 0.6
                and len([s for s in samples if s["type"] == "neutral"]) == 0
            ):
                samples.append(
                    {
                        "type": "neutral",
                        "persona": r["persona_type"],
                        "comment": r["comment"],
                        "sentiment": round(r["current_sentiment"], 2),
                    }
                )
            if len(samples) >= 3:
                break

        return {
            "simulation_id": f"sim_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "mode": "simulated",
            "is_early_estimate": True,
            "confidence_note": "Swarm simulation — predicted audience reactions based on statistical modeling. Scores are directional estimates, not guarantees.",
            "persona_distribution": distribution,
            "final_sentiment": round(final_round["avg_sentiment"] * 100, 1),
            "viral_prediction": viral_prediction,
            "backlash_prediction": backlash_prediction,
            "share_prediction": round(final_round["avg_sentiment"] * 65 + 20, 1),
            "trust_trajectory": trust_trajectory,
            "comment_samples": samples,
            "simulation_rounds": simulation_rounds,
            "num_agents": num_agents,
        }

    async def run_what_if(
        self, base_simulation: Dict[str, Any], modifications: Dict[str, Any]
    ) -> Dict[str, Any]:
        if self.is_real:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{self.api_url}/api/what-if",
                        json={"base_simulation": base_simulation, "modifications": modifications},
                    )
                    if response.status_code == 200:
                        return response.json()
            except Exception:
                pass

        # Simulated mode: no artificial delay.
        effects = []
        if modifications.get("earlier_product_mention"):
            effects.append(
                {
                    "effect": "negative",
                    "magnitude": 0.15,
                    "description": "Earlier product mention reduces authenticity",
                }
            )
        if modifications.get("price_decrease"):
            effects.append(
                {
                    "effect": "positive",
                    "magnitude": modifications["price_decrease"] / 100 * 0.3,
                    "description": f"Price decrease of {modifications['price_decrease']}% increases purchase intent",
                }
            )
        if modifications.get("aggressive_cta"):
            effects.append(
                {
                    "effect": "negative",
                    "magnitude": 0.1,
                    "description": "Aggressive CTA triggers ad-skip behavior",
                }
            )
        if modifications.get("emotional_tone"):
            effects.append(
                {
                    "effect": "positive",
                    "magnitude": 0.08,
                    "description": "Emotional tone increases engagement",
                }
            )

        positive_sum = sum(m["magnitude"] for m in effects if m["effect"] == "positive")
        negative_sum = sum(m["magnitude"] for m in effects if m["effect"] == "negative")

        return {
            "modifications": effects,
            "predicted_outcome": {
                "sentiment_adjustment": round(positive_sum - negative_sum, 3),
                "risk_change": "increased"
                if any(m["effect"] == "negative" for m in effects)
                else "reduced",
                "viral_potential_change": "improved" if positive_sum > negative_sum else "reduced",
            },
            "comparison": {
                "original_sentiment": base_simulation.get("final_sentiment", 50),
                "modified_sentiment": round(
                    base_simulation.get("final_sentiment", 50)
                    + (positive_sum - negative_sum) * 100,
                    1,
                ),
            },
        }


mirofish_engine = MiroFishEngine()
