# Supabase Setup for Legislative Data

This guide walks you through setting up Supabase to store California legislative data.

## Step 1: Create Database Schema

1. Go to your new Supabase project dashboard
2. Click **SQL Editor** in the sidebar
3. Click **New Query**
4. Copy and paste the contents of `supabase_schema.sql`
5. Click **Run** to execute
6. Verify tables were created in **Table Editor**

## Step 2: Get Your Credentials

1. In Supabase dashboard, go to **Settings** → **API**
2. Copy these values:

```
Project URL: https://xxxxx.supabase.co
anon public key: eyJhbGc...
service_role key: eyJhbGc... (keep this secret!)
```

## Step 3: Add to Railway Environment Variables

1. Go to your Railway project
2. Click **Variables** tab
3. Add these environment variables:

```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc... (your anon key)
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc... (your service role key)
OPENSTATES_API_KEY=your-openstates-key (keep this for import script)
```

## Step 4: Import Data

Run the import script locally (one-time setup):

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables locally
export OPENSTATES_API_KEY=your-key
export SUPABASE_URL=https://xxxxx.supabase.co
export SUPABASE_SERVICE_ROLE_KEY=your-service-key

# Run import script
python import_legislative_data.py
```

**Note:** The script has a safety limit at 5 pages (~500 bills) for testing. To import all bills:
1. Edit `import_legislative_data.py`
2. Remove or comment out the `if page > 5` limit
3. Run again (will take longer and use more API calls)

## Step 5: Switch to Supabase in the App

Update `openstates/__init__.py` to use Supabase:

```python
# Change from:
from .api import (...)

# To:
from .supabase_api import (...)
```

## Step 6: Redeploy

Railway will automatically redeploy when you push the changes.

## Verify It's Working

1. Visit your DataViz app
2. Go to Vote Tracker page
3. Search for a legislator
4. Should load from Supabase (no API rate limits!)

## Maintenance

**Weekly updates (optional):**

Run the import script weekly to get new bills/votes:

```bash
python import_legislative_data.py
```

Or set up a GitHub Action / cron job to do this automatically.

## Troubleshooting

**"Supabase credentials not configured"**
- Check Railway environment variables are set correctly
- Verify SUPABASE_URL and SUPABASE_ANON_KEY are present

**"No data returned"**
- Verify import script ran successfully
- Check Supabase dashboard that tables have data
- Check RLS policies allow public read access

**"Permission denied"**
- Service role key needed for import script
- Anon key is fine for the app (public read access)
