#!/usr/bin/env python3
"""
Complete database and storage setup script
Runs both schema.sql and setup_storage.sql
"""

import psycopg2
import os
import sys
from dotenv import load_dotenv
from supabase import create_client
from config import Config

def main():
    print("=" * 70)
    print("🚀 MEMOIR GENERATOR - COMPLETE SETUP")
    print("=" * 70)
    print()

    # Load environment
    load_dotenv()
    db_url = os.getenv('DIRECT_URL')

    if not db_url:
        print("❌ DIRECT_URL not found in .env file")
        return 1

    # Step 1: Database Schema
    print("📊 Step 1: Setting up database schema...")
    print("-" * 70)

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()

        with open('schema.sql', 'r') as f:
            schema_sql = f.read()

        cursor.execute(schema_sql)
        cursor.close()
        conn.close()

        print("✅ Database schema created successfully")
        print("   - 4 tables created")
        print("   - pgvector extension enabled")
        print("   - Indexes created")
        print("   - match_documents() function created")
        print()

    except Exception as e:
        print(f"❌ Error creating schema: {e}")
        return 1

    # Step 2: Storage Bucket
    print("📦 Step 2: Setting up storage bucket...")
    print("-" * 70)

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()

        with open('setup_storage.sql', 'r') as f:
            storage_sql = f.read()

        cursor.execute(storage_sql)
        cursor.close()
        conn.close()

        print("✅ Storage bucket created successfully")
        print("   - Bucket 'memoires' created")
        print("   - Storage policies configured")
        print()

    except Exception as e:
        if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
            print("✅ Storage bucket already exists")
            print()
        else:
            print(f"⚠️  Warning: {e}")
            print()

    # Step 3: Verification
    print("🔍 Step 3: Verifying setup...")
    print("-" * 70)

    try:
        client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

        # Test tables
        tables = ['memoires', 'projects', 'sections', 'document_chunks']
        for table in tables:
            result = client.table(table).select('*').limit(1).execute()
            print(f"✅ Table '{table}' - accessible")

        # Test function
        test_embedding = [0.0] * 1536
        result = client.rpc('match_documents', {
            'query_embedding': test_embedding,
            'match_count': 5
        }).execute()
        print(f"✅ Function 'match_documents()' - working")

        # Test storage
        test_data = b'Test file'
        client.storage.from_('memoires').upload(
            'test/test.txt',
            test_data,
            {'content-type': 'text/plain'}
        )
        client.storage.from_('memoires').remove(['test/test.txt'])
        print(f"✅ Storage bucket 'memoires' - operational")

        print()
        print("=" * 70)
        print("🎉 SETUP COMPLETE!")
        print("=" * 70)
        print()
        print("✅ Database schema ready")
        print("✅ Storage bucket ready")
        print("✅ All systems operational")
        print()
        print("Next step: Run the FastAPI server")
        print("  $ source venv/bin/activate")
        print("  $ python main.py")
        print()

        return 0

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
