# LegiScan Dataset Import Guide

This guide walks you through importing California legislative data from LegiScan datasets into your Supabase database.

## Why LegiScan?

- **Complete Data**: Full legislative history including all votes
- **No API Limits**: Download once, use forever
- **Public Domain**: California legislative data is freely available
- **Official Source**: LegiScan aggregates directly from state sources

## Prerequisites

1. Supabase project set up with schema (see SUPABASE_SETUP.md)
2. Python 3.8+ installed
3. Dependencies installed: `pip install -r requirements.txt`
4. Supabase credentials (URL and SERVICE_ROLE_KEY)

## Step 1: Download LegiScan Dataset

1. Visit [LegiScan California Datasets](https://legiscan.com/CA/datasets)
2. Find the latest dataset (they release weekly snapshots)
3. Click **Download** for the full California dataset
4. You'll get a ZIP file (usually named like `CA_2023-2024_dataset.zip`)

**Note**: LegiScan may require free registration for dataset access.

## Step 2: Extract the Dataset

```bash
# Create a directory for the data
mkdir legiscan_ca_data

# Extract the ZIP file
unzip CA_2023-2024_dataset.zip -d legiscan_ca_data/
```

The extracted folder should contain CSV files like:
- `people.csv` or `legislators.csv` - All legislators
- `bills.csv` or `legislation.csv` - All bills
- `roll_calls.csv` or `votes.csv` - All roll call votes

## Step 3: Set Environment Variables

The import script needs your Supabase credentials:

```bash
export SUPABASE_URL="https://xxxxx.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="your-service-role-key-here"
```

**Important**: Use the SERVICE_ROLE_KEY (not the anon key) for imports. This key has write permissions.

**Security**: Never commit these credentials to git. Keep them in your environment or use a `.env` file (already in .gitignore).

## Step 4: Run the Import Script

```bash
python import_legiscan_data.py
```

The script will:
1. Look for CSV files in `./legiscan_ca_data/` directory
2. Try multiple filename variations automatically
3. Import legislators, bills, and votes in chunks
4. Show progress as it imports

**Expected Output**:
```
🚀 LegiScan Dataset Import to Supabase
============================================================

📥 Importing legislators from legiscan_ca_data/people.csv...
✅ Imported 120 legislators

📥 Importing bills from legiscan_ca_data/bills.csv...
  Imported 100/2500 bills
  Imported 200/2500 bills
  ...
✅ Imported 2500 bills total

📥 Importing votes from legiscan_ca_data/roll_calls.csv...
  Imported 500/50000 votes
  Imported 1000/50000 votes
  ...
✅ Imported 50000 votes total

============================================================
✅ Import complete!

Check your Supabase dashboard to verify the data was imported.
```

## Step 5: Verify the Import

1. Go to your Supabase dashboard
2. Navigate to **Table Editor**
3. Check each table has data:
   - `legislators` - Should have ~120 rows (CA has 120 legislators)
   - `bills` - Should have thousands of rows
   - `votes` - Should have tens of thousands of rows

## Customizing the Import

### Change the Data Directory

Edit `import_legiscan_data.py` line 227:

```python
dataset_dir = Path("./your_custom_directory")
```

### Import Only Specific Tables

Comment out the tables you don't want to import in the `main()` function:

```python
# Don't import legislators
# if legislators_path:
#     import_legiscan_legislators(str(legislators_path))

# Only import bills and votes
if bills_path:
    import_legiscan_bills(str(bills_path))
if votes_path:
    import_legiscan_votes(str(votes_path))
```

## Troubleshooting

### "File not found" errors

**Problem**: Script can't find CSV files

**Solution**:
1. Check that you extracted the ZIP to `legiscan_ca_data/`
2. List files: `ls legiscan_ca_data/`
3. Update the `alt_files` dictionary in the script to match actual filenames

### Column mismatch errors

**Problem**: CSV columns don't match expected field names

**Solution**:
1. Open the CSV file and check column names
2. Update the field mapping in the import functions:

```python
legislator = {
    'id': row.get('people_id') or row.get('your_actual_id_column'),
    'name': row.get('name') or row.get('your_actual_name_column'),
    # ... adjust field names
}
```

### Timeout errors during import

**Problem**: Large imports timing out

**Solution**: The script already chunks imports:
- Bills: 100 per chunk
- Votes: 500 per chunk

You can reduce these further if needed by editing the `chunk_size` variables.

### Duplicate key errors

**Problem**: Data already exists

**Solution**: The script uses `upsert()` which updates existing records. This error usually means:
1. Your table has unique constraints that differ from the schema
2. The data has duplicate IDs within the CSV itself

Check your table constraints in Supabase SQL Editor.

## Updating the Data

LegiScan releases weekly dataset snapshots. To update:

1. Download the latest dataset
2. Extract to the same directory (overwrite old files)
3. Run the import script again

The script uses `upsert()` so it will:
- Update existing legislators/bills/votes
- Add new records
- Won't create duplicates

## Data Structure

### Legislators CSV Expected Columns
- `people_id`, `person_id`, or `id` - Unique identifier
- `name` or `first_name`/`last_name` - Legislator name
- `party` or `party_id` - Political party
- `role_name` - "Senator" or Assembly member
- `district` - District number
- `email`, `phone`, `url`, `website` - Contact info

### Bills CSV Expected Columns
- `bill_id` or `id` - Unique identifier
- `bill_number` or `bill_no` - Bill number (e.g., "AB 123")
- `title` or `description` - Bill title
- `session` or `session_id` - Legislative session
- `status` or `status_desc` - Current status
- `last_action` or `last_action_desc` - Latest action
- `last_action_date` - Date of last action
- `subjects` - Comma-separated subjects

### Votes CSV Expected Columns
- `bill_id` - Links to bills table
- `people_id` or `person_id` - Links to legislators table
- `vote_text` - Vote value (yea/nay/nv/absent)
- `date` or `roll_call_date` - Vote date
- `session` or `session_id` - Session identifier
- `chamber` - Senate or Assembly
- `desc` or `motion` - What was voted on
- `passed` - Whether motion passed (1/true or 0/false)

### Vote Type Normalization

The script normalizes various vote formats to standard values:
- **yes**: yea, aye, yes, 1
- **no**: nay, no, 2
- **not voting**: nv, not voting, 3
- **absent**: absent, excused, 4
- **abstain**: Everything else

## Next Steps

After importing:

1. Set `USE_SUPABASE=true` in your Railway environment variables
2. Redeploy your Streamlit app
3. Test the Vote Tracker - it should now use Supabase data
4. Enjoy no API rate limits!

## Cost Considerations

**Supabase Pro Plan** ($25/month):
- 8GB database storage
- 50GB bandwidth
- More than enough for CA legislative data

**Data Size Estimates**:
- Legislators: ~100 KB (120 rows)
- Bills: ~50 MB (5,000+ bills with text)
- Votes: ~200 MB (100,000+ individual votes)
- **Total**: ~250 MB (well within 8GB limit)

## Support

If you encounter issues:

1. Check the CSV files match expected structure
2. Verify Supabase credentials are correct
3. Check Supabase dashboard for import errors
4. Review the Python error messages for specific issues

For LegiScan-specific issues:
- Visit [LegiScan Documentation](https://legiscan.com/legiscan)
- Check their API documentation for CSV format details
