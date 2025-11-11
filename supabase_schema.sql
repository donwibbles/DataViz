-- ============================================================================
-- California Legislative Data Schema for Supabase
-- ============================================================================
-- Run this in your Supabase SQL Editor to create the tables

-- Legislators table
CREATE TABLE IF NOT EXISTS legislators (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    party TEXT,
    chamber TEXT, -- 'Senate' or 'Assembly'
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
    bill_number TEXT NOT NULL, -- e.g. 'AB 123'
    title TEXT NOT NULL,
    session TEXT NOT NULL, -- e.g. '2023-2024'
    status TEXT,
    last_action TEXT,
    last_action_date DATE,
    subjects TEXT[], -- Array of subject tags
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Bill authors (many-to-many)
CREATE TABLE IF NOT EXISTS bill_authors (
    id SERIAL PRIMARY KEY,
    bill_id TEXT REFERENCES bills(id) ON DELETE CASCADE,
    legislator_id TEXT REFERENCES legislators(id) ON DELETE CASCADE,
    author_type TEXT, -- 'primary', 'coauthor', 'sponsor'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(bill_id, legislator_id)
);

-- Votes table
CREATE TABLE IF NOT EXISTS votes (
    id SERIAL PRIMARY KEY,
    bill_id TEXT REFERENCES bills(id) ON DELETE CASCADE,
    legislator_id TEXT REFERENCES legislators(id) ON DELETE CASCADE,
    vote_type TEXT NOT NULL, -- 'yes', 'no', 'abstain', 'not voting', 'absent'
    vote_date DATE,
    session TEXT,
    chamber TEXT, -- Which chamber this vote occurred in
    motion TEXT, -- What was being voted on
    passed BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(bill_id, legislator_id, vote_date, motion)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_legislators_name ON legislators(name);
CREATE INDEX IF NOT EXISTS idx_legislators_chamber ON legislators(chamber);
CREATE INDEX IF NOT EXISTS idx_legislators_party ON legislators(party);

CREATE INDEX IF NOT EXISTS idx_bills_number ON bills(bill_number);
CREATE INDEX IF NOT EXISTS idx_bills_session ON bills(session);
CREATE INDEX IF NOT EXISTS idx_bills_subjects ON bills USING GIN(subjects);

CREATE INDEX IF NOT EXISTS idx_bill_authors_bill ON bill_authors(bill_id);
CREATE INDEX IF NOT EXISTS idx_bill_authors_legislator ON bill_authors(legislator_id);

CREATE INDEX IF NOT EXISTS idx_votes_bill ON votes(bill_id);
CREATE INDEX IF NOT EXISTS idx_votes_legislator ON votes(legislator_id);
CREATE INDEX IF NOT EXISTS idx_votes_session ON votes(session);
CREATE INDEX IF NOT EXISTS idx_votes_date ON votes(vote_date);

-- Enable Row Level Security (but set to public read)
ALTER TABLE legislators ENABLE ROW LEVEL SECURITY;
ALTER TABLE bills ENABLE ROW LEVEL SECURITY;
ALTER TABLE bill_authors ENABLE ROW LEVEL SECURITY;
ALTER TABLE votes ENABLE ROW LEVEL SECURITY;

-- Public read access policies (legislative data is public)
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

-- Service role can write (for data imports)
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

-- Helpful views
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

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_legislators_updated_at BEFORE UPDATE ON legislators
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bills_updated_at BEFORE UPDATE ON bills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Done!
-- Next steps:
-- 1. Get your Supabase URL and SERVICE_ROLE key
-- 2. Add to Railway environment variables
-- 3. Run the bulk import script
