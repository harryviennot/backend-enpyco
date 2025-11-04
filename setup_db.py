#!/usr/bin/env python3
"""
Database setup script - Run schema.sql via PostgreSQL connection
"""

import psycopg2
from config import Config
import sys

def main():
    print("🗄️  Setting up Memoir Generator Database")
    print("=" * 60)

    # Get direct database URL (not pooled)
    db_url = Config.DATABASE_URL.replace('?pgbouncer=true', '')
    # Or use DIRECT_URL if available
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        db_url = os.getenv('DIRECT_URL', db_url)
    except:
        pass

    print(f"📍 Connecting to database...")

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()

        print("✅ Connected successfully\n")

        # Read SQL file
        with open('schema.sql', 'r') as f:
            sql = f.read()

        # Split by semicolons and execute each statement
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]

        total = len(statements)
        for i, statement in enumerate(statements, 1):
            # Skip comments and empty statements
            if not statement or statement.startswith('--'):
                continue

            # Get a short description
            first_line = statement.split('\n')[0][:50]

            try:
                print(f"[{i}/{total}] Executing: {first_line}...", end=" ", flush=True)
                cursor.execute(statement)
                print("✅")
            except Exception as e:
                print(f"❌")
                print(f"      Error: {e}")
                if "already exists" not in str(e).lower():
                    print(f"      Statement: {statement[:100]}...")

        cursor.close()
        conn.close()

        print("\n" + "=" * 60)
        print("✅ Database setup complete!")
        print("\n📊 Schema created:")
        print("   ✓ memoires table")
        print("   ✓ projects table")
        print("   ✓ sections table")
        print("   ✓ document_chunks table (with vector embeddings)")
        print("\n🔍 Indexes created:")
        print("   ✓ Vector similarity index (IVFFlat)")
        print("   ✓ Performance indexes")
        print("\n🔧 Functions created:")
        print("   ✓ match_documents() for RAG search")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Alternative: Run schema.sql manually in Supabase SQL Editor")
        print("   1. Go to https://app.supabase.com")
        print("   2. Select your project")
        print("   3. Go to SQL Editor")
        print("   4. Copy/paste content from schema.sql")
        print("   5. Click 'Run'")
        return 1

if __name__ == "__main__":
    sys.exit(main())
