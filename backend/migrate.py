"""Run Supabase migrations in order via direct Postgres connection."""
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def run_migrations():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")
        if not supabase_url or not supabase_key:
            logger.error("Set DATABASE_URL or both SUPABASE_URL and SUPABASE_SERVICE_KEY")
            sys.exit(1)
        project_ref = supabase_url.replace("https://", "").replace(".supabase.co", "")
        db_url = f"postgresql://postgres.{project_ref}:{supabase_key}@aws-0-{supabase_url.split('-')[2] if '-' in supabase_url else 'us-east-1'}.pooler.supabase.com:6543/postgres"
        logger.warning("Constructed DATABASE_URL from Supabase creds — verify it matches your project")

    try:
        import psycopg2
    except ImportError:
        logger.error("psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)

    migrations_dir = Path(__file__).parent / "migrations"
    if not migrations_dir.exists():
        logger.error(f"Migrations directory not found: {migrations_dir}")
        sys.exit(1)

    sql_files = sorted(migrations_dir.glob("*.sql"))
    if not sql_files:
        logger.warning("No migration files found")
        sys.exit(0)

    logger.info("Connecting to database...")
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        sys.exit(1)

    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("SELECT version FROM schema_migrations ORDER BY version")
        applied = {row[0] for row in cur.fetchall()}
    except Exception as e:
        logger.error(f"Failed to check migration state: {e}")
        sys.exit(1)

    for migration in sql_files:
        version = migration.stem
        if version in applied:
            logger.info(f"  SKIP {migration.name} (already applied)")
            continue

        logger.info(f"Applying {migration.name}...")
        sql = migration.read_text()
        try:
            cur.execute(sql)
            cur.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (version,))
            logger.info(f"  OK {migration.name}")
        except Exception as e:
            logger.error(f"  FAIL {migration.name}: {e}")
            conn.rollback()
            sys.exit(1)

    cur.close()
    conn.close()
    logger.info("All migrations applied successfully")


if __name__ == "__main__":
    run_migrations()
