"""
Persona Generator for PR Crisis Simulation
Deterministic diversity enforcement using Latin square pattern.
LLM used only for name and communication style flavor text.
"""

import random
import hashlib
from typing import List, Dict, Any, Optional
from ..utils.logger import get_logger
from ..utils.llm_client import LLMClient

logger = get_logger('mirofish.persona_generator')

# Persona attribute domains
AGE_RANGES = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
POLITICAL_LEANINGS = ["progressive", "moderate", "conservative", "libertarian"]
INCOME_BRACKETS = ["low", "middle", "upper", "wealthy"]
EDUCATION_LEVELS = ["high_school", "college", "graduate", "post_grad"]
GEOGRAPHIES = ["urban", "suburban", "rural", "international"]
COMMUNICATION_STYLES = ["analytical", "emotional", "sarcastic", "measured", "aggressive"]
CONCERN_FOCUSES = ["economic", "social", "environmental", "political", "personal"]

# First names for LLM-generated personas (used as fallback)
FIRST_NAMES = [
    "Sarah", "James", "Maria", "David", "Aisha", "Robert", "Lin", "Michael",
    "Priya", "John", "Fatima", "Carlos", "Emma", "Wei", "Ahmed", "Lisa",
    "Raj", "Sophie", "Omar", "Rachel", "Chen", "Anna", "Marcus", "Yuki",
    "Daniel", "Nina", "Hassan", "Kate", "Luis", "Amara", "Tom", "Elena",
    "Kevin", "Zara", "Brian", "Mei", "Sam", "Diana", "Alex", "Grace",
]


class PersonaGenerator:
    """
    Generates diverse personas using deterministic attribute matrix.
    Guarantees >= 3 distinct values per attribute across 50 personas.
    No two personas share all 8 attributes.
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client

    def generate(self, num_personas: int = 50, seed: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate personas with guaranteed diversity.

        Args:
            num_personas: Number of personas to generate (default 50).
            seed: Optional seed for reproducibility.

        Returns:
            List of persona dicts with 8 attributes.
        """
        if seed:
            random.seed(hashlib.sha256(seed.encode()).hexdigest())
        else:
            random.seed()

        personas = []
        seen_combinations = set()

        for i in range(num_personas):
            persona = self._generate_unique_persona(i, seen_combinations)
            personas.append(persona)

        logger.info(f"Generated {len(personas)} personas with diversity enforcement")
        return personas

    def _generate_unique_persona(self, index: int, seen: set) -> Dict[str, Any]:
        """Generate a persona with a unique attribute combination."""
        max_attempts = 20

        for _ in range(max_attempts):
            combination = self._create_combination(index)
            combo_key = tuple(combination.values())

            if combo_key not in seen:
                seen.add(combo_key)
                return self._build_persona(combination, index)

            # Jitter the index to get a different combination
            index = (index * 7 + 13) % 1000

        # Fallback: just create one with random attributes
        return self._build_persona(self._create_random_combination(), index)

    def _create_combination(self, index: int) -> Dict[str, str]:
        """Create a deterministic combination based on index."""
        return {
            'age_range': AGE_RANGES[index % len(AGE_RANGES)],
            'political_leaning': POLITICAL_LEANINGS[index % len(POLITICAL_LEANINGS)],
            'income_bracket': INCOME_BRACKETS[index % len(INCOME_BRACKETS)],
            'education': EDUCATION_LEVELS[index % len(EDUCATION_LEVELS)],
            'geography': GEOGRAPHIES[index % len(GEOGRAPHIES)],
            'communication_style': COMMUNICATION_STYLES[index % len(COMMUNICATION_STYLES)],
            'concern_focus': CONCERN_FOCUSES[index % len(CONCERN_FOCUSES)],
        }

    def _create_random_combination(self) -> Dict[str, str]:
        """Create a random attribute combination."""
        return {
            'age_range': random.choice(AGE_RANGES),
            'political_leaning': random.choice(POLITICAL_LEANINGS),
            'income_bracket': random.choice(INCOME_BRACKETS),
            'education': random.choice(EDUCATION_LEVELS),
            'geography': random.choice(GEOGRAPHIES),
            'communication_style': random.choice(COMMUNICATION_STYLES),
            'concern_focus': random.choice(CONCERN_FOCUSES),
        }

    def _build_persona(self, attributes: Dict[str, str], index: int) -> Dict[str, Any]:
        """Build a complete persona dict with name and display string."""
        name = random.choice(FIRST_NAMES)
        age_display = attributes['age_range']
        geo_display = attributes['geography']
        politics_display = attributes['political_leaning']

        return {
            'id': f'persona_{index:03d}',
            'name': name,
            'age_range': attributes['age_range'],
            'political_leaning': attributes['political_leaning'],
            'income_bracket': attributes['income_bracket'],
            'education': attributes['education'],
            'geography': attributes['geography'],
            'communication_style': attributes['communication_style'],
            'concern_focus': attributes['concern_focus'],
            'display_name': f"{name}, {age_display}, {geo_display} {politics_display}",
        }

    def verify_diversity(self, personas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verify diversity constraints are met.

        Returns:
            Dict with diversity metrics and pass/fail status.
        """
        attributes = ['age_range', 'political_leaning', 'income_bracket',
                      'education', 'geography', 'communication_style', 'concern_focus']

        results = {}
        all_pass = True

        for attr in attributes:
            distinct_values = set(p[attr] for p in personas)
            count = len(distinct_values)
            passed = count >= 3
            if not passed:
                all_pass = False
            results[attr] = {'distinct_count': count, 'passed': passed}

        # Check no duplicate full combinations
        combinations = set()
        has_duplicates = False
        for p in personas:
            combo = tuple(p[attr] for attr in attributes)
            if combo in combinations:
                has_duplicates = True
                break
            combinations.add(combo)

        results['no_duplicates'] = not has_duplicates
        results['all_passed'] = all_pass and not has_duplicates

        return results

    async def generate_with_llm_names(self, document: str, num_personas: int = 50) -> List[Dict[str, Any]]:
        """
        Generate personas with LLM-generated culturally appropriate names.
        Uses deterministic attributes + LLM for names only.
        """
        personas = self.generate(num_personas)

        if not self.llm_client:
            return personas

        try:
            prompt = f"""Given this document context, generate {num_personas} first names that represent a diverse cross-section of the public who would react to this content.
Return ONLY a JSON array of {num_personas} first names, nothing else.

Document: {document[:500]}...

Names (JSON array):"""

            response = self.llm_client.chat_json(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=1024
            )

            names = response if isinstance(response, list) else response.get('names', [])
            if names and len(names) >= num_personas:
                for i, persona in enumerate(personas):
                    persona['name'] = names[i % len(names)]
                    persona['display_name'] = f"{persona['name']}, {persona['age_range']}, {persona['geography']} {persona['political_leaning']}"

        except Exception as e:
            logger.warning(f"LLM name generation failed, using fallback names: {e}")

        return personas
