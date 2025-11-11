-- ============================================================================
-- Fix Assembly Chamber Mapping
-- ============================================================================
-- Updates legislators with chamber='Unknown' to properly identify Assembly members
-- based on their role in the LegiScan data

-- This fixes the issue where Assembly members were mapped to 'Unknown'
-- because LegiScan uses 'Rep' not 'Asm' for the role field

-- Note: This will update all legislators. You may want to re-import instead
-- if you have other data issues to fix.

-- Show current chamber distribution
SELECT chamber, COUNT(*) as count
FROM legislators
WHERE is_committee = false
GROUP BY chamber;

-- Update would go here if needed, but it's better to just re-import
-- the legislators since the import script is now fixed

-- To re-import legislators:
-- 1. The fixed import script will now correctly map Rep → Assembly
-- 2. Run: python import_legiscan_data_v2.py
-- 3. The upsert will update existing legislators with correct chambers
