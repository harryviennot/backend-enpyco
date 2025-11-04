-- =====================================================
-- Memoir Generator Database Schema
-- =====================================================
-- Run this in Supabase SQL Editor
-- Dashboard → SQL Editor → New Query → Paste & Run
-- =====================================================

-- 1. Drop existing tables (if any)
-- =====================================================
DROP TABLE IF EXISTS document_chunks CASCADE;
DROP TABLE IF EXISTS sections CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS memoires CASCADE;
DROP TABLE IF EXISTS reference_memoires CASCADE;
DROP FUNCTION IF EXISTS match_documents CASCADE;

-- 2. Enable pgvector extension
-- =====================================================
CREATE EXTENSION IF NOT EXISTS vector;

-- 3. Create memoires table (reference documents)
-- =====================================================
CREATE TABLE memoires (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,  -- Path in Supabase Storage
    client VARCHAR(255),
    year INTEGER,
    indexed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Create projects table
-- =====================================================
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    rc_storage_path VARCHAR(500),
    rc_context TEXT,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Create sections table (generated content)
-- =====================================================
CREATE TABLE sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    section_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    order_num INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Create document_chunks table (RAG embeddings)
-- =====================================================
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memoire_id UUID NOT NULL REFERENCES memoires(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI text-embedding-3-small dimension
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Create performance indexes
-- =====================================================
CREATE INDEX idx_chunks_memoire ON document_chunks(memoire_id);
CREATE INDEX idx_sections_project ON sections(project_id, order_num);

-- 8. Create vector similarity index (IVFFlat)
-- =====================================================
-- This index speeds up vector similarity search
CREATE INDEX ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 9. Create match_documents function for RAG
-- =====================================================
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_count int DEFAULT 10,
    memoire_ids uuid[] DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    content text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        document_chunks.id,
        document_chunks.content,
        document_chunks.metadata,
        1 - (document_chunks.embedding <=> query_embedding) as similarity
    FROM document_chunks
    WHERE
        CASE
            WHEN memoire_ids IS NOT NULL THEN memoire_id = ANY(memoire_ids)
            ELSE true
        END
    ORDER BY document_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- =====================================================
-- Setup Complete!
-- =====================================================
-- Tables created:
--   ✓ memoires - Store reference documents metadata
--   ✓ projects - Memoir projects being generated
--   ✓ sections - Generated content sections
--   ✓ document_chunks - Text chunks with embeddings
--
-- Indexes created:
--   ✓ Vector similarity index (IVFFlat)
--   ✓ Foreign key indexes for performance
--
-- Functions created:
--   ✓ match_documents() - Semantic search function
-- =====================================================
