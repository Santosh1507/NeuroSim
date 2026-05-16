"""
Blind Spot Detection Service
Identifies topics that personas are concerned about but the document doesn't address.
Uses LLM topic extraction for both reactions and document, then compares.
"""

from typing import List, Dict, Any, Set
from ..utils.logger import get_logger
from ..utils.llm_client import LLMClient

logger = get_logger('mirofish.blind_spot_detector')

# Blind spot thresholds
MIN_MENTION_RATIO = 0.15  # 15% of personas must mention topic
MIN_SENTIMENT_DIVERGENCE = 0.6  # |positive_ratio - negative_ratio|
MAX_TOPICS = 5


class BlindSpotDetector:
    """
    Detects blind spots in PR documents by comparing persona reaction topics
    against document content topics.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def detect(
        self,
        document: str,
        reactions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect blind spots in the document.

        Args:
            document: The PR document text.
            reactions: List of reaction dicts with 'text' and 'sentiment'.

        Returns:
            List of blind spot dicts: {topic, severity, explanation, persona_count}
        """
        if not reactions:
            return []

        # Extract topics from reactions
        reaction_topics = self._extract_reaction_topics(reactions)

        # Extract topics from document
        document_topics = self._extract_document_topics(document)

        # Find blind spots: topics in reactions but not in document
        blind_spots = []
        total_reactions = len(reactions)

        for topic, topic_data in reaction_topics.items():
            # Skip if document covers this topic
            if self._topic_in_document(topic, document_topics):
                continue

            mention_count = topic_data['count']
            mention_ratio = mention_count / total_reactions

            # Check threshold: >= 15% of personas mentioned it
            if mention_ratio < MIN_MENTION_RATIO:
                continue

            # Calculate sentiment divergence
            positive_ratio = topic_data['positive'] / mention_count
            negative_ratio = topic_data['negative'] / mention_count
            divergence = abs(positive_ratio - negative_ratio)

            # Check divergence threshold
            if divergence < MIN_SENTIMENT_DIVERGENCE:
                continue

            # Determine severity
            severity = self._calculate_severity(mention_ratio, divergence, topic_data)

            blind_spots.append({
                'topic': topic,
                'severity': severity,
                'explanation': f"{mention_count} personas raised concerns about {topic} not addressed in document",
                'persona_count': mention_count,
                'mention_ratio': round(mention_ratio, 2),
                'sentiment_divergence': round(divergence, 2),
                'positive_ratio': round(positive_ratio, 2),
                'negative_ratio': round(negative_ratio, 2),
            })

        # Sort by severity (critical > high > medium)
        severity_order = {'critical': 0, 'high': 1, 'medium': 2}
        blind_spots.sort(key=lambda x: severity_order.get(x['severity'], 3))

        # Limit to max topics
        blind_spots = blind_spots[:MAX_TOPICS]

        logger.info(f"Detected {len(blind_spots)} blind spots")
        return blind_spots

    def _extract_reaction_topics(self, reactions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Extract topics from reactions using LLM.
        Returns: {topic: {'count': N, 'positive': N, 'negative': N, 'neutral': N}}
        """
        # Combine reaction texts for topic extraction
        reaction_texts = "\n".join([f"- {r['text']}" for r in reactions[:30]])  # Limit to 30 for token budget

        try:
            prompt = f"""Analyze these public reactions and identify up to {MAX_TOPICS} main concern topics.
For each topic, note how many reactions mention it and the sentiment breakdown.

REACTIONS:
{reaction_texts}

Return ONLY a JSON object with this structure:
{{
  "topics": [
    {{"topic": "topic name", "count": N, "positive": N, "negative": N, "neutral": N}}
  ]
}}

Topics should be short (2-4 words). Count must sum to total reactions analyzed."""

            response = self.llm_client.chat_json(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1024
            )

            topics = {}
            for t in response.get('topics', []):
                topic_name = t['topic'].lower().strip()
                topics[topic_name] = {
                    'count': t.get('count', 0),
                    'positive': t.get('positive', 0),
                    'negative': t.get('negative', 0),
                    'neutral': t.get('neutral', 0),
                }

            return topics

        except Exception as e:
            logger.warning(f"LLM topic extraction failed, using fallback: {e}")
            return self._fallback_topic_extraction(reactions)

    def _extract_document_topics(self, document: str) -> Set[str]:
        """
        Extract topics from the document using LLM.
        Returns: set of topic strings.
        """
        try:
            prompt = f"""Identify the main topics covered in this document.
Return ONLY a JSON array of topic strings (2-4 words each).

DOCUMENT:
{document[:2000]}

Topics (JSON array):"""

            response = self.llm_client.chat_json(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=512
            )

            return set(t.lower().strip() for t in response if isinstance(t, str))

        except Exception as e:
            logger.warning(f"Document topic extraction failed: {e}")
            return set()

    def _topic_in_document(self, topic: str, document_topics: Set[str]) -> bool:
        """Check if a reaction topic is covered in the document."""
        # Direct match
        if topic in document_topics:
            return True

        # Partial match (topic words in document topics)
        topic_words = set(topic.split())
        for doc_topic in document_topics:
            doc_words = set(doc_topic.split())
            if topic_words & doc_words:  # Any word overlap
                return True

        return False

    def _calculate_severity(
        self,
        mention_ratio: float,
        divergence: float,
        topic_data: Dict[str, Any]
    ) -> str:
        """Calculate blind spot severity."""
        negative_ratio = topic_data['negative'] / max(topic_data['count'], 1)

        if mention_ratio >= 0.3 and divergence >= 0.8:
            return "critical"
        elif mention_ratio >= 0.2 and negative_ratio >= 0.5:
            return "high"
        else:
            return "medium"

    def _fallback_topic_extraction(self, reactions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Fallback topic extraction using keyword matching."""
        keywords = {
            'environmental impact': ['environment', 'climate', 'carbon', 'pollution', 'green', 'sustainability'],
            'economic impact': ['cost', 'price', 'money', 'economy', 'jobs', 'financial', 'budget'],
            'social responsibility': ['community', 'society', 'people', 'fair', 'equal', 'rights'],
            'transparency': ['honest', 'truth', 'hidden', 'cover', 'disclose', 'open'],
            'leadership concern': ['leader', 'ceo', 'management', 'decision', 'responsible'],
        }

        topics = {}
        for topic, words in keywords.items():
            count = 0
            positive = 0
            negative = 0
            neutral = 0

            for r in reactions:
                text = r['text'].lower()
                if any(w in text for w in words):
                    count += 1
                    if r['sentiment'] == 'positive':
                        positive += 1
                    elif r['sentiment'] == 'negative':
                        negative += 1
                    else:
                        neutral += 1

            if count > 0:
                topics[topic] = {
                    'count': count,
                    'positive': positive,
                    'negative': negative,
                    'neutral': neutral,
                }

        return topics
