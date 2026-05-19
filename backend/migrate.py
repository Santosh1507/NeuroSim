"""Run Supabase migrations in order."""
import os
import sys
from pathlib import Path


def run_migrations():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")

    if not url or not key:
        print("SUPABASE_URL and SUPABASE_SERVICE_KEY required")
        sys.exit(1)

    try:
        from supabase import create_client
    except ImportError:
        print("supabase package not installed")
        sys.exit(1)

    supabase = create_client(url, key)
    migrations_dir = Path(__file__).parent / "migrations"

    for migration in sorted(migrations_dir.glob("*.sql")):
        print(f"Applying {migration.name}...")
        sql = migration.read_text()
        try:
            supabase.rpc("exec_sql", {"sql": sql}).execute()
            print(f"  OK {migration.name}")
        except Exception as e:
            print(f"  FAIL {migration.name}: {e}")
            sys.exit(1)

    print("All migrations applied successfully")


if __name__ == "__main__":
    run_migrations()
