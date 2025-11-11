# Agricultural & Farm Worker Bill Tracker

## Overview

This system tracks and classifies California legislation related to agriculture, farm workers, and labor organizing. It provides automated keyword-based tagging and manual curation capabilities without requiring frontend authentication.

## Architecture

### Data Model

**Database Field**: `bills.agricultural_tags` (JSONB)

Structure:
```json
{
  "is_agricultural": true,
  "categories": ["farm_worker_rights", "safety", "union_organizing"],
  "priority": "high" | "medium" | "low",
  "manually_curated": false,
  "notes": "Optional curator notes",
  "auto_detected_keywords": ["farm worker", "heat illness"],
  "classification_date": "2025-01-11"
}
```

### Categories

1. **farm_worker_rights**: Core labor rights and protections
   - Keywords: "agricultural labor", "farm worker", "farmworker", "agricultural employee"

2. **safety**: Health and safety protections
   - Keywords: "heat illness", "pesticide exposure", "safety equipment", "workplace injury"

3. **union_organizing**: Collective bargaining and organizing rights
   - Keywords: "collective bargaining", "union", "labor organizing", "right to organize", "ALRA"

4. **wages**: Compensation and overtime
   - Keywords: "overtime", "minimum wage", "agricultural wage", "piece rate"

5. **immigration**: Immigration and visa programs
   - Keywords: "H-2A", "agricultural visa", "undocumented", "guest worker", "IRCA"

6. **working_conditions**: Housing, sanitation, and basic conditions
   - Keywords: "housing", "sanitation", "bathroom", "water access", "field conditions"

### Priority Levels

- **high**: Landmark legislation, major policy changes
- **medium**: Incremental improvements, enforcement mechanisms
- **low**: Minor amendments, technical changes

## Workflow

### Automated Classification

Bills are automatically classified when:
1. Imported from LegiScan (during import process)
2. Viewed in the UI (on-demand classification)
3. Bulk classification script is run

**Classification Logic** (`openstates/agricultural_classifier.py`):
- Scans bill title and description
- Uses regex patterns with word boundaries
- Checks LegiScan subjects for "Agriculture" or "Labor"
- Assigns categories based on keyword matches
- Sets priority based on number of matches and keyword significance

### Manual Curation

**Tools**:
- `tag_agricultural_bills.py` - Manual tagging script
- Runs locally with SERVICE_ROLE key
- Updates Supabase directly

**Workflow**:
1. Browse auto-tagged bills on website
2. Identify bills needing manual curation
3. Run tagging script locally:
   ```bash
   python tag_agricultural_bills.py \
     --bill-id "1893344" \
     --categories "farm_worker_rights,safety" \
     --priority "high" \
     --notes "Landmark heat illness prevention bill - opposed by agricultural lobby"
   ```
4. Refresh website to see updates

**Security**:
- No frontend authentication required
- All writes via SERVICE_ROLE key (local only)
- Frontend is read-only (uses ANON key)
- Manual curation tracked via `manually_curated: true` flag

## Files

### Backend
- `openstates/agricultural_classifier.py` - Classification logic
- `tag_agricultural_bills.py` - Manual curation script
- `bulk_classify_agricultural_bills.py` - One-time classification of all existing bills

### Frontend
- `pages/3_Agricultural_Tracker.py` - Browse and filter agricultural bills
- Integration with existing Vote Tracker and Campaign Finance tools

### Database
- `supabase_migration_agricultural.sql` - Adds agricultural_tags field
- Indexes on JSONB field for performance

### Documentation
- `AGRICULTURAL_TRACKER.md` - This file
- `AGRICULTURAL_KEYWORDS.md` - Detailed keyword lists and rationale

## Usage

### Initial Setup

1. **Add database field**:
   ```bash
   # Run in Supabase SQL Editor
   cat supabase_migration_agricultural.sql
   ```

2. **Classify existing bills** (one-time):
   ```bash
   export SUPABASE_URL="your-url"
   export SUPABASE_SERVICE_ROLE_KEY="your-key"
   python bulk_classify_agricultural_bills.py
   ```

   This will classify all ~44K bills. Expected results:
   - ~500-1500 bills tagged as agricultural
   - ~5-10 minutes to complete

3. **Browse on website**:
   - Visit `/Agricultural_Tracker`
   - Filter by category, priority, session
   - View legislator voting records on ag bills

### Manual Curation Examples

**Tag a specific bill**:
```bash
python tag_agricultural_bills.py \
  --bill-id "1893344" \
  --add-categories "farm_worker_rights" \
  --priority "high"
```

**Update priority**:
```bash
python tag_agricultural_bills.py \
  --bill-id "1893344" \
  --priority "low" \
  --notes "Technical amendment only"
```

**Remove agricultural tag**:
```bash
python tag_agricultural_bills.py \
  --bill-id "1893344" \
  --remove-tag
```

**Bulk tag bills from list**:
```bash
# Create bills.txt with one bill_id per line
python tag_agricultural_bills.py \
  --bulk-file bills.txt \
  --categories "safety" \
  --priority "high"
```

### Frontend Features

**Agricultural Bills Page** (`/Agricultural_Tracker`):
- Filter by category, priority, session, legislator
- Sort by date, priority, relevance
- View bill details with agricultural context
- Link to Campaign Finance data for authors
- Export to CSV for advocacy use

**Integration with Campaign Finance**:
- "Agricultural Industry Donations" filter
- Cross-reference: "Voted NO while receiving $X from ag PACs"
- Union alignment score

**Legislator Profiles** (future):
- Farm Worker Voting Score: % pro-worker votes on ag bills
- Key votes on landmark legislation
- District agricultural profile

## Maintenance

### Regular Tasks

**Weekly** (optional):
- Review newly imported bills for agricultural content
- Manually curate high-priority legislation

**Per Session** (every 2 years):
- Identify landmark bills for manual tagging
- Update keyword list based on emerging issues
- Generate session report

### Updating Keywords

Edit `openstates/agricultural_classifier.py`:
```python
FARM_WORKER_KEYWORDS = [
    r'\bfarm worker\b',
    r'\bfarmworker\b',
    # Add new patterns here
]
```

Then re-run bulk classification:
```bash
python bulk_classify_agricultural_bills.py --force-reclassify
```

## Data Sources

**LegiScan Data**:
- Bill titles and descriptions
- Subjects field (when "Agriculture" or "Labor")
- Full bill text (for detailed analysis)

**Campaign Finance Data**:
- Agricultural industry contributions
- Farm worker union contributions (UFW, etc.)
- Lobbyist registrations

**External Sources** (potential future integration):
- UFW priority bill lists
- CalFarmJustice legislative updates
- Agricultural employer association positions

## Performance

**Query Optimization**:
- JSONB GIN index on `agricultural_tags`
- Filter queries: ~50ms for 1K bills
- Full scan: ~200ms for all agricultural bills

**Caching**:
- Legislator scores cached in `legislator_scores` table
- Refreshed weekly or on-demand

## Privacy & Security

**Public Data**:
- All legislative data is public record
- Campaign finance data is public record
- No PII stored

**Authentication**:
- Frontend: ANON key (read-only)
- Manual curation: SERVICE_ROLE key (local scripts only)
- No user accounts or authentication system

## Future Enhancements

### Phase 2
- Legislator Farm Worker Voting Score
- District agricultural workforce data
- Geographic heat map

### Phase 3
- Bill prediction (likelihood of passage)
- Alert system for new bills
- Historical trend analysis

### Phase 4
- API access for advocacy organizations
- Automated weekly reports
- Integration with organizing databases

## Troubleshooting

**Bills not appearing as agricultural**:
1. Check keyword matches in classifier
2. Verify agricultural_tags field exists
3. Run bulk classification script
4. Manually tag if false negative

**Performance issues**:
1. Check JSONB index exists
2. Limit query to specific sessions
3. Use materialized views for complex queries

**Manual tagging not working**:
1. Verify SERVICE_ROLE key is set
2. Check bill_id is valid
3. Review script error messages
4. Confirm network access to Supabase

## Resources

- **UFW Website**: https://ufw.org/
- **California ALRA**: https://www.alrb.ca.gov/
- **LegiScan API Docs**: https://legiscan.com/legiscan
- **Campaign Finance (Cal-Access)**: https://cal-access.sos.ca.gov/

## Contact

For questions about this system:
- Review this documentation
- Check script comments for technical details
- Consult Claude Code session history for implementation decisions

## Version History

- **v1.0** (2025-01-11): Initial implementation
  - Automated classification
  - Manual tagging script
  - Frontend browse page
  - 6 core categories
