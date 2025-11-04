-- =====================================================
-- Storage Bucket Setup
-- =====================================================
-- Run this in Supabase SQL Editor after schema.sql
-- =====================================================

-- 1. Create the 'memoires' bucket
-- =====================================================
INSERT INTO storage.buckets (id, name, public)
VALUES ('memoires', 'memoires', false)
ON CONFLICT (id) DO NOTHING;

-- 2. Set up storage policies for authenticated access
-- =====================================================

-- Allow service_role to do everything (for backend)
CREATE POLICY "Service role can do everything"
ON storage.objects
FOR ALL
TO service_role
USING (bucket_id = 'memoires');

-- Allow authenticated users to upload
CREATE POLICY "Authenticated users can upload"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'memoires');

-- Allow authenticated users to read their own files
CREATE POLICY "Authenticated users can read"
ON storage.objects
FOR SELECT
TO authenticated
USING (bucket_id = 'memoires');

-- Allow authenticated users to update their own files
CREATE POLICY "Authenticated users can update"
ON storage.objects
FOR UPDATE
TO authenticated
USING (bucket_id = 'memoires');

-- Allow authenticated users to delete their own files
CREATE POLICY "Authenticated users can delete"
ON storage.objects
FOR DELETE
TO authenticated
USING (bucket_id = 'memoires');

-- =====================================================
-- Storage Setup Complete!
-- =====================================================
