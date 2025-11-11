-- ============================================================================
-- Migration: Add session tracking and new LegiScan tables
-- ============================================================================
-- Run this in Supabase SQL Editor to add new fields and tables

-- Add session_name to bills table
ALTER TABLE bills ADD COLUMN IF NOT EXISTS session_name TEXT;

-- Add index for session_name
CREATE INDEX IF NOT EXISTS idx_bills_session_name ON bills(session_name);

-- Create rollcalls table (vote summaries)
CREATE TABLE IF NOT EXISTS rollcalls (
    id TEXT PRIMARY KEY, -- roll_call_id from LegiScan
    bill_id TEXT REFERENCES bills(id) ON DELETE CASCADE,
    vote_date DATE NOT NULL,
    chamber TEXT, -- 'Assembly' or 'Senate'
    description TEXT, -- What was voted on
    yea INTEGER DEFAULT 0,
    nay INTEGER DEFAULT 0,
    nv INTEGER DEFAULT 0, -- Not voting / abstain
    absent INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create bill_history table (action timeline)
CREATE TABLE IF NOT EXISTS bill_history (
    id SERIAL PRIMARY KEY,
    bill_id TEXT REFERENCES bills(id) ON DELETE CASCADE,
    action_date DATE NOT NULL,
    chamber TEXT,
    sequence INTEGER, -- Order of actions
    action TEXT NOT NULL, -- Description of action
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(bill_id, action_date, sequence)
);

-- Create bill_documents table (texts, amendments, etc.)
CREATE TABLE IF NOT EXISTS bill_documents (
    id TEXT PRIMARY KEY, -- document_id from LegiScan
    bill_id TEXT REFERENCES bills(id) ON DELETE CASCADE,
    document_type TEXT, -- 'text', 'amendment', 'supplement'
    document_size INTEGER,
    document_mime TEXT, -- MIME type
    document_desc TEXT, -- Description
    url TEXT, -- LegiScan URL
    state_link TEXT, -- State URL
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add indexes for new tables
CREATE INDEX IF NOT EXISTS idx_rollcalls_bill ON rollcalls(bill_id);
CREATE INDEX IF NOT EXISTS idx_rollcalls_date ON rollcalls(vote_date);

CREATE INDEX IF NOT EXISTS idx_bill_history_bill ON bill_history(bill_id);
CREATE INDEX IF NOT EXISTS idx_bill_history_date ON bill_history(action_date);

CREATE INDEX IF NOT EXISTS idx_bill_documents_bill ON bill_documents(bill_id);
CREATE INDEX IF NOT EXISTS idx_bill_documents_type ON bill_documents(document_type);

-- Enable RLS on new tables
ALTER TABLE rollcalls ENABLE ROW LEVEL SECURITY;
ALTER TABLE bill_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE bill_documents ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (so we can recreate them)
DROP POLICY IF EXISTS "Anyone can read rollcalls" ON rollcalls;
DROP POLICY IF EXISTS "Anyone can read bill_history" ON bill_history;
DROP POLICY IF EXISTS "Anyone can read bill_documents" ON bill_documents;
DROP POLICY IF EXISTS "Service role can insert rollcalls" ON rollcalls;
DROP POLICY IF EXISTS "Service role can update rollcalls" ON rollcalls;
DROP POLICY IF EXISTS "Service role can insert bill_history" ON bill_history;
DROP POLICY IF EXISTS "Service role can insert bill_documents" ON bill_documents;

-- Public read access policies for new tables
CREATE POLICY "Anyone can read rollcalls"
    ON rollcalls FOR SELECT
    USING (true);

CREATE POLICY "Anyone can read bill_history"
    ON bill_history FOR SELECT
    USING (true);

CREATE POLICY "Anyone can read bill_documents"
    ON bill_documents FOR SELECT
    USING (true);

-- Service role write policies for new tables
CREATE POLICY "Service role can insert rollcalls"
    ON rollcalls FOR INSERT
    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can update rollcalls"
    ON rollcalls FOR UPDATE
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can insert bill_history"
    ON bill_history FOR INSERT
    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can insert bill_documents"
    ON bill_documents FOR INSERT
    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

-- Done!
-- You can now run import_legiscan_data_v2.py to import all data
