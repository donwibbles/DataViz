-- ============================================================================
-- Migration: Add committee support to legislators table
-- ============================================================================
-- Run this in Supabase SQL Editor to add is_committee field

-- Add is_committee column to legislators table
ALTER TABLE legislators ADD COLUMN IF NOT EXISTS is_committee BOOLEAN DEFAULT false;

-- Create index for is_committee (useful for filtering out committees in UI)
CREATE INDEX IF NOT EXISTS idx_legislators_is_committee ON legislators(is_committee);

-- Done!
-- Now re-run: python import_legiscan_data_v2.py
-- This will import committees alongside legislators and fix foreign key errors
