#!/usr/bin/env python
"""
Daily Cleanup Script
Deletes simulation data older than 30 days from Neo4j.
Run via GitHub Actions scheduled workflow or Render cron job.

Usage:
    python -m app.scripts.cleanup_simulations
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config import Config
from app.storage import Neo4jStorage
from app.services.simulation_queue import SimulationQueue
from app.utils.logger import setup_logger

logger = setup_logger('mirofish.cleanup')


def main():
    """Run daily cleanup."""
    logger.info("Starting daily simulation cleanup")

    # Initialize Neo4j
    try:
        neo4j = Neo4jStorage()
        logger.info(f"Connected to Neo4j: {Config.NEO4J_URI}")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        sys.exit(1)

    # Clean up old simulations (30 days)
    queue = SimulationQueue.get_instance()
    queue.cleanup_neo4j_simulations(neo4j, max_age_days=30)

    # Clean up old in-memory jobs (24 hours)
    queue.cleanup_old_jobs(max_age_hours=24)

    logger.info("Daily cleanup complete")


if __name__ == '__main__':
    main()
