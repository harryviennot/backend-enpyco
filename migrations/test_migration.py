#!/usr/bin/env python3
"""
Test script for database migration 001
Tests migration execution and validates schema changes
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from config import Config
import traceback


def get_db_client():
    """Get Supabase client for database operations"""
    return create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)


def run_sql_file(client, filepath: str):
    """Execute SQL from a file"""
    print(f"\n{'='*80}")
    print(f"Running: {filepath}")
    print(f"{'='*80}\n")

    with open(filepath, 'r') as f:
        sql = f.read()

    try:
        # Supabase doesn't support multi-statement execution via REST API
        # We need to use the PostgREST or connect directly
        # For now, we'll print the SQL and ask user to run it manually
        print("⚠️  Supabase REST API doesn't support multi-statement SQL execution.")
        print("Please run the migration manually using one of these methods:\n")
        print("1. Using psql (recommended):")
        print(f"   psql $DATABASE_URL -f {filepath}\n")
        print("2. Using Supabase Dashboard:")
        print("   - Go to your Supabase project")
        print("   - Navigate to SQL Editor")
        print("   - Paste the contents of the migration file")
        print("   - Click 'Run'\n")
        return False
    except Exception as e:
        print(f"❌ Error running SQL: {e}")
        traceback.print_exc()
        return False


def check_table_exists(client, table_name: str) -> bool:
    """Check if a table exists by trying to select from it"""
    try:
        result = client.table(table_name).select('*').limit(0).execute()
        return True
    except Exception as e:
        if 'does not exist' in str(e).lower() or 'not found' in str(e).lower():
            return False
        # Other errors might mean table exists but has issues
        print(f"⚠️  Error checking table {table_name}: {e}")
        return False


def validate_schema(client):
    """Validate that all expected tables exist after migration"""
    print(f"\n{'='*80}")
    print("Schema Validation")
    print(f"{'='*80}\n")

    # Expected new tables
    new_tables = [
        'companies',
        'users',
        'content_blocks',
        'files',
        'block_files',
        'past_projects',
        'section_templates',
        'rc_analysis',
        'content_matches',
        'generation_requests',
        'audit_log'
    ]

    # Existing tables that should still be there
    existing_tables = [
        'memoires',
        'projects',
        'sections',
        'document_chunks'
    ]

    all_tables = new_tables + existing_tables
    results = {}

    for table in all_tables:
        exists = check_table_exists(client, table)
        results[table] = exists
        status = "✅" if exists else "❌"
        table_type = "(new)" if table in new_tables else "(existing)"
        print(f"{status} {table} {table_type}")

    # Summary
    print(f"\n{'='*80}")
    new_count = sum(1 for t in new_tables if results.get(t))
    existing_count = sum(1 for t in existing_tables if results.get(t))

    print(f"New tables created: {new_count}/{len(new_tables)}")
    print(f"Existing tables preserved: {existing_count}/{len(existing_tables)}")

    if new_count == len(new_tables) and existing_count == len(existing_tables):
        print("\n🎉 All tables validated successfully!")
        return True
    else:
        print("\n⚠️  Some tables are missing. Migration may not be complete.")
        return False


def test_data_queries(client):
    """Test some basic queries to ensure schema works"""
    print(f"\n{'='*80}")
    print("Testing Data Queries")
    print(f"{'='*80}\n")

    tests_passed = 0
    tests_failed = 0

    # Test 1: Query companies
    try:
        result = client.table('companies').select('*').limit(5).execute()
        print(f"✅ Companies query: {len(result.data)} rows")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Companies query failed: {e}")
        tests_failed += 1

    # Test 2: Query users
    try:
        result = client.table('users').select('*').limit(5).execute()
        print(f"✅ Users query: {len(result.data)} rows")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Users query failed: {e}")
        tests_failed += 1

    # Test 3: Query content_blocks
    try:
        result = client.table('content_blocks').select('*').limit(5).execute()
        print(f"✅ Content blocks query: {len(result.data)} rows")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Content blocks query failed: {e}")
        tests_failed += 1

    # Test 4: Query projects (should have new columns)
    try:
        result = client.table('projects').select('id,name,company_id,created_by,status').limit(5).execute()
        print(f"✅ Projects query (with new columns): {len(result.data)} rows")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Projects query failed: {e}")
        tests_failed += 1

    # Test 5: Query memoires (should have new columns)
    try:
        result = client.table('memoires').select('id,filename,company_id,uploaded_by').limit(5).execute()
        print(f"✅ Memoires query (with new columns): {len(result.data)} rows")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Memoires query failed: {e}")
        tests_failed += 1

    # Test 6: Query document_chunks (should be unchanged)
    try:
        result = client.table('document_chunks').select('id,memoire_id').limit(5).execute()
        print(f"✅ Document chunks query (RAG): {len(result.data)} rows")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Document chunks query failed: {e}")
        tests_failed += 1

    print(f"\n{'='*80}")
    print(f"Query Tests: {tests_passed} passed, {tests_failed} failed")

    return tests_failed == 0


def main():
    print(f"\n{'='*80}")
    print("Database Migration 001 - Test Suite")
    print(f"{'='*80}\n")

    # Check config
    try:
        Config.validate()
        print("✅ Configuration validated")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease ensure your .env file has:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_SERVICE_ROLE_KEY")
        print("  - DATABASE_URL")
        return 1

    # Get database client
    try:
        client = get_db_client()
        print("✅ Database connection established")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return 1

    # Show migration instructions
    migration_file = Path(__file__).parent / "001_multi_tenant_schema.sql"
    seed_file = Path(__file__).parent / "001_seed_data.sql"

    print(f"\n{'='*80}")
    print("Migration Instructions")
    print(f"{'='*80}\n")
    print("To run the migration, use psql:\n")
    print(f"  psql $DATABASE_URL -f {migration_file}")
    print(f"\nTo load seed data (optional):\n")
    print(f"  psql $DATABASE_URL -f {seed_file}")
    print(f"\n{'='*80}\n")

    # Ask user if they want to validate (assuming migration was run)
    response = input("Have you already run the migration? (y/n): ").strip().lower()

    if response != 'y':
        print("\nPlease run the migration first, then re-run this test script.")
        return 0

    # Validate schema
    schema_valid = validate_schema(client)

    if not schema_valid:
        print("\n⚠️  Schema validation failed. Some tables are missing.")
        print("Please check that the migration ran successfully.")
        return 1

    # Test queries
    queries_passed = test_data_queries(client)

    if queries_passed:
        print("\n🎉 All tests passed! Migration successful!")
        return 0
    else:
        print("\n⚠️  Some query tests failed. Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
