-- ============================================================================
-- Complete Migration: All tables, fields, and policies for LegiScan data
-- ============================================================================
-- Safe to run on existing database - uses IF NOT EXISTS everywhere
-- Run this in Supabase SQL Editor

-- ============================================================================
-- TABLES
-- ============================================================================

-- Legislators table
CREATE TABLE IF NOT EXISTS legislators (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    party TEXT,
    chamber TEXT,
    district TEXT,
    email TEXT,
    phone TEXT,
    website TEXT,
    image_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bills table
CREATE TABLE IF NOT EXISTS bills (
    id TEXT PRIMARY KEY,
    bill_number TEXT NOT NULL,
    title TEXT NOT NULL,
    session TEXT NOT NULL,
    status TEXT,
    last_action TEXT,
    last_action_date DATE,
    subjects TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add session_name column if it doesn't exist
ALTER TABLE bills ADD COLUMN IF NOT EXISTS session_name TEXT;

-- Bill authors (many-to-many)
CREATE TABLE IF NOT EXISTS bill_authors (
    id SERIAL PRIMARY KEY,
    bill_id TEXT REFERENCES bills(id) ON DELETE CASCADE,
    legislator_id TEXT REFERENCES legislators(id) ON DELETE CASCADE,
    author_type TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(bill_id, legislator_id)
);

-- Votes table
CREATE TABLE IF NOT EXISTS votes (
    id SERIAL PRIMARY KEY,
    bill_id TEXT REFERENCES bills(id) ON DELETE CASCADE,
    legislator_id TEXT REFERENCES legislators(id) ON DELETE CASCADE,
    vote_type TEXT NOT NULL,
    vote_date DATE,
    session TEXT,
    chamber TEXT,
    motion TEXT,
    passed BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(bill_id, legislator_id, vote_date, motion)
);

-- Roll calls table (vote summaries)
CREATE TABLE IF NOT EXISTS rollcalls (
    id TEXT PRIMARY KEY,
    bill_id TEXT REFERENCES bills(id) ON DELETE CASCADE,
    vote_date DATE NOT NULL,
    chamber TEXT,
    description TEXT,
    yea INTEGER DEFAULT 0,
    nay INTEGER DEFAULT 0,
    nv INTEGER DEFAULT 0,
    absent INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bill history table (action timeline)
CREATE TABLE IF NOT EXISTS bill_history (
    id SERIAL PRIMARY KEY,
    bill_id TEXT REFERENCES bills(id) ON DELETE CASCADE,
    action_date DATE NOT NULL,
    chamber TEXT,
    sequence INTEGER,
    action TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(bill_id, action_date, sequence)
);

-- Bill documents table (texts, amendments, etc.)
CREATE TABLE IF NOT EXISTS bill_documents (
    id TEXT PRIMARY KEY,
    bill_id TEXT REFERENCES bills(id) ON DELETE CASCADE,
    document_type TEXT,
    document_size INTEGER,
    document_mime TEXT,
    document_desc TEXT,
    url TEXT,
    state_link TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_legislators_name ON legislators(name);
CREATE INDEX IF NOT EXISTS idx_legislators_chamber ON legislators(chamber);
CREATE INDEX IF NOT EXISTS idx_legislators_party ON legislators(party);

CREATE INDEX IF NOT EXISTS idx_bills_number ON bills(bill_number);
CREATE INDEX IF NOT EXISTS idx_bills_session ON bills(session);
CREATE INDEX IF NOT EXISTS idx_bills_session_name ON bills(session_name);
CREATE INDEX IF NOT EXISTS idx_bills_number_session ON bills(bill_number, session);
CREATE INDEX IF NOT EXISTS idx_bills_subjects ON bills USING GIN(subjects);

CREATE INDEX IF NOT EXISTS idx_bill_authors_bill ON bill_authors(bill_id);
CREATE INDEX IF NOT EXISTS idx_bill_authors_legislator ON bill_authors(legislator_id);

CREATE INDEX IF NOT EXISTS idx_votes_bill ON votes(bill_id);
CREATE INDEX IF NOT EXISTS idx_votes_legislator ON votes(legislator_id);
CREATE INDEX IF NOT EXISTS idx_votes_session ON votes(session);
CREATE INDEX IF NOT EXISTS idx_votes_date ON votes(vote_date);

CREATE INDEX IF NOT EXISTS idx_rollcalls_bill ON rollcalls(bill_id);
CREATE INDEX IF NOT EXISTS idx_rollcalls_date ON rollcalls(vote_date);

CREATE INDEX IF NOT EXISTS idx_bill_history_bill ON bill_history(bill_id);
CREATE INDEX IF NOT EXISTS idx_bill_history_date ON bill_history(action_date);

CREATE INDEX IF NOT EXISTS idx_bill_documents_bill ON bill_documents(bill_id);
CREATE INDEX IF NOT EXISTS idx_bill_documents_type ON bill_documents(document_type);

-- ============================================================================
-- ROW LEVEL SECURITY
-- ============================================================================

ALTER TABLE legislators ENABLE ROW LEVEL SECURITY;
ALTER TABLE bills ENABLE ROW LEVEL SECURITY;
ALTER TABLE bill_authors ENABLE ROW LEVEL SECURITY;
ALTER TABLE votes ENABLE ROW LEVEL SECURITY;
ALTER TABLE rollcalls ENABLE ROW LEVEL SECURITY;
ALTER TABLE bill_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE bill_documents ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- RLS POLICIES - Public Read Access
-- ============================================================================

-- Drop existing policies first (in case they exist)
DROP POLICY IF EXISTS "Anyone can read legislators" ON legislators;
DROP POLICY IF EXISTS "Anyone can read bills" ON bills;
DROP POLICY IF EXISTS "Anyone can read bill_authors" ON bill_authors;
DROP POLICY IF EXISTS "Anyone can read votes" ON votes;
DROP POLICY IF EXISTS "Anyone can read rollcalls" ON rollcalls;
DROP POLICY IF EXISTS "Anyone can read bill_history" ON bill_history;
DROP POLICY IF EXISTS "Anyone can read bill_documents" ON bill_documents;

-- Create public read policies
CREATE POLICY "Anyone can read legislators"
    ON legislators FOR SELECT
    USING (true);

CREATE POLICY "Anyone can read bills"
    ON bills FOR SELECT
    USING (true);

CREATE POLICY "Anyone can read bill_authors"
    ON bill_authors FOR SELECT
    USING (true);

CREATE POLICY "Anyone can read votes"
    ON votes FOR SELECT
    USING (true);

CREATE POLICY "Anyone can read rollcalls"
    ON rollcalls FOR SELECT
    USING (true);

CREATE POLICY "Anyone can read bill_history"
    ON bill_history FOR SELECT
    USING (true);

CREATE POLICY "Anyone can read bill_documents"
    ON bill_documents FOR SELECT
    USING (true);

-- ============================================================================
-- RLS POLICIES - Service Role Write Access
-- ============================================================================

-- Drop existing write policies first
DROP POLICY IF EXISTS "Service role can insert legislators" ON legislators;
DROP POLICY IF EXISTS "Service role can update legislators" ON legislators;
DROP POLICY IF EXISTS "Service role can insert bills" ON bills;
DROP POLICY IF EXISTS "Service role can update bills" ON bills;
DROP POLICY IF EXISTS "Service role can insert bill_authors" ON bill_authors;
DROP POLICY IF EXISTS "Service role can insert votes" ON votes;
DROP POLICY IF EXISTS "Service role can insert rollcalls" ON rollcalls;
DROP POLICY IF EXISTS "Service role can update rollcalls" ON rollcalls;
DROP POLICY IF EXISTS "Service role can insert bill_history" ON bill_history;
DROP POLICY IF EXISTS "Service role can insert bill_documents" ON bill_documents;

-- Create service role write policies
CREATE POLICY "Service role can insert legislators"
    ON legislators FOR INSERT
    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can update legislators"
    ON legislators FOR UPDATE
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can insert bills"
    ON bills FOR INSERT
    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can update bills"
    ON bills FOR UPDATE
    USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can insert bill_authors"
    ON bill_authors FOR INSERT
    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role can insert votes"
    ON votes FOR INSERT
    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');

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

-- ============================================================================
-- HELPER VIEWS AND FUNCTIONS
-- ============================================================================

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop existing triggers first
DROP TRIGGER IF EXISTS update_legislators_updated_at ON legislators;
DROP TRIGGER IF EXISTS update_bills_updated_at ON bills;

-- Create triggers for updated_at
CREATE TRIGGER update_legislators_updated_at BEFORE UPDATE ON legislators
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bills_updated_at BEFORE UPDATE ON bills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Helpful view for legislator vote counts
CREATE OR REPLACE VIEW legislator_vote_counts AS
SELECT
    l.id,
    l.name,
    l.party,
    l.chamber,
    COUNT(v.id) as total_votes,
    COUNT(v.id) FILTER (WHERE v.vote_type = 'yes') as yes_votes,
    COUNT(v.id) FILTER (WHERE v.vote_type = 'no') as no_votes,
    COUNT(v.id) FILTER (WHERE v.vote_type = 'abstain') as abstain_votes
FROM legislators l
LEFT JOIN votes v ON l.id = v.legislator_id
GROUP BY l.id, l.name, l.party, l.chamber;

-- ============================================================================
-- DONE!
-- ============================================================================
-- Next steps:
-- 1. Run: python import_legiscan_data_v2.py
-- 2. Set USE_SUPABASE=true in Railway environment variables
-- 3. Verify data in Supabase Table Editor
