-- ============================================================================
-- Migration: Add Agricultural Bill Classification
-- ============================================================================
-- Adds JSONB field for storing agricultural/farm worker bill classifications
-- Run this in Supabase SQL Editor

-- Add agricultural_tags column to bills table
ALTER TABLE bills ADD COLUMN IF NOT EXISTS agricultural_tags JSONB;

-- Create GIN index for fast JSONB queries
CREATE INDEX IF NOT EXISTS idx_bills_agricultural_tags ON bills USING GIN (agricultural_tags);

-- Create index specifically for is_agricultural flag (most common query)
CREATE INDEX IF NOT EXISTS idx_bills_is_agricultural ON bills ((agricultural_tags->>'is_agricultural'));

-- Create index for category searches
CREATE INDEX IF NOT EXISTS idx_bills_ag_categories ON bills USING GIN ((agricultural_tags->'categories'));

-- Example agricultural_tags structure:
COMMENT ON COLUMN bills.agricultural_tags IS
'JSONB field storing agricultural classification:
{
  "is_agricultural": true,
  "categories": ["farm_worker_rights", "safety"],
  "priority": "high",
  "manually_curated": false,
  "notes": "Landmark heat illness prevention bill",
  "auto_detected_keywords": ["farm worker", "heat illness"],
  "classification_date": "2025-01-11T12:00:00Z"
}

Categories: farm_worker_rights, safety, union_organizing, wages, immigration, working_conditions
Priority: high, medium, low';

-- Done!
-- Next steps:
-- 1. Run: python bulk_classify_agricultural_bills.py (classify all existing bills)
-- 2. Browse: Visit /Agricultural_Tracker on the website
-- 3. Curate: Use tag_agricultural_bills.py for manual tagging
