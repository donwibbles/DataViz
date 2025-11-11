# DataViz Remediation & Optimization Plan

This document breaks the remediation effort into phased chunks so a fresh engineering instance can tackle the backlog incrementally. Each phase lists goals, concrete tasks (with file references), and key context gathered during the last review. A ready‑to‑copy coordination prompt is included at the end.

---

## Phase 1 – Restore Streamlit App Stability & Remove Union Features
Goal: get every Streamlit page loading without exceptions and drop the half-baked union detection experience until we redesign it.

Tasks:
1. **Fix Campaign Finance sidebar crash**  
   - File: `pages/1_Campaign_Finance.py:559-588`  
   - Replace the `st.number_input` that uses `value=None` with a real numeric default (e.g., 100000) and add an explicit “Load entire file” toggle instead of relying on `None`.
2. **Fully strip union/labor analysis**  
   - Files: `pages/1_Campaign_Finance.py` (sections labelled “Union/Labor support” and helpers like `detect_union_labor`, state columns `union_*`, and union-specific charts), plus any references in PDF export `available_charts`.  
   - Remove related dependencies if no longer needed (e.g., regex-heavy detection code) and ensure downstream code no longer writes `df['is_union']`, etc.
3. **Repair boolean masking bug (if any remnants remain)**  
   - File: `pages/1_Campaign_Finance.py:1751-1755`  
   - Wherever multiple boolean masks are chained, combine them on the original dataframe (`df[mask_a & mask_b]`) to avoid pandas `IndexError`. This matters even after union removal if similar patterns exist elsewhere.
4. **Run the Streamlit pages manually (Campaign Finance, Vote Tracker, Agricultural Tracker) to ensure they render without errors after changes.**

Deliverables: Stable Streamlit UI with union functionality absent and no runtime tracebacks when navigating between pages.

**Status (2025-11-11):** ✅ Completed. Campaign Finance sidebar now uses a real numeric default plus a `Load entire file` toggle, all union detection/helpers/UI have been removed (including PDF references), boolean masking chains were eliminated with the associated section, and all three Streamlit pages (Campaign Finance, Vote Tracker, Agricultural Tracker) were smoke-tested headlessly without errors.

---

## Phase 2 – Supabase Vote Tracker Reliability
Goal: tighten the Supabase-only pipeline now that OpenStates is deprecated, ensuring the vote tracker UI matches the data stored in the database.

Tasks:
1. **Remove OpenStates fallback code**  
   - Files: `openstates/__init__.py`, `openstates/api.py`, `pages/2_Vote_Tracker.py`  
   - Delete the environment toggle (`USE_SUPABASE`) and strip the legacy OpenStates module to avoid dead code paths. The vote tracker should import directly from `openstates.supabase_api`.
2. **Consolidate Supabase helpers**  
   - File: `openstates/supabase_api.py`  
   - Ensure every public helper (`fetch_legislator_votes`, `fetch_bill_details`, etc.) has the parameters the UI expects and return types stay consistent with `openstates/models.py`.
3. **Supabase search fallback fix**  
   - File: `openstates/supabase_api.py:215-229`  
   - Rebuild the query for the title search instead of reusing the `bill_number` filtered one.
4. **Verify vote tracker flows**  
   - Manually exercise legislator search, authored bills, vote timelines, and bill search tabs to confirm everything works solely against Supabase.

Deliverables: Vote tracker relies exclusively on Supabase and no longer references OpenStates endpoints or API keys.

---

## Phase 3 – Data Import & Classification Integrity
Goal: ensure Supabase data imports and classifiers operate on complete datasets.

Tasks:
1. **Parameterize LegiScan imports for complete runs**  
   - Files: `import_legiscan_data.py`, `import_legiscan_data_v2.py`  
   - Replace the hardcoded dataset paths/testing throttles with CLI flags (dataset dir, optional session filters) so a default invocation ingests every available session without code edits while still allowing a capped/dev mode when needed.
2. **Unify LegiScan importer logic**  
   - Files: `import_legiscan_data.py`, `import_legiscan_data_v2.py`  
   - Deduplicate overlapping helpers, ensure both populate `session_name` and emit consistent progress logging, and remove any lingering OpenStates terminology.
3. **Classifier consistency**  
   - File: `openstates/agricultural_classifier.py` and scripts `bulk_classify_agricultural_bills.py`, `tag_agricultural_bills.py`.  
   - Confirm categories/priority enums are reused everywhere; add unit tests for classification edge cases once the environment is stable (see Phase 4).

Deliverables: Running import scripts populates full sessions; classification tooling is safe to rerun without manual intervention.

---

## Phase 4 – Environment & Test Health
Goal: make automated validation usable again and document environment expectations.

Tasks:
1. **Fix the pandas/pyarrow segfault**  
   - Recreate the virtualenv, reinstall dependencies from `requirements.txt`, and verify that `python -c "import pandas"` no longer crashes.  
   - If the issue stems from incompatible wheels on macOS/arm64, pin versions that are known to work (e.g., pandas 2.2.x + numpy 1.26.x).
2. **Restore `pytest`**  
   - Once the environment is stable, run `pytest` and add coverage for the CSV visualizer plus any new helper functions touched in earlier phases.
3. **Document environment setup**  
   - Update `README.md` with explicit python version, venv instructions, and troubleshooting notes for M-series Macs.

Deliverables: Tests run green locally; contributors have a reliable setup recipe.

---

## Phase 5 – Optimization & Future Enhancements
Goal: after the codebase is healthy, pursue optimizations and new UX improvements.

Ideas:
1. **Campaign Finance performance** – consider lazy-loading data previews, caching expensive aggregations (`st.cache_data` on filtered DataFrames), and introducing sampling toggles for multi-hundred-thousand-row CSVs.
2. **Vote tracker UX** – add pagination and infinite scroll for votes/authored bills, plus clear messaging when Supabase-exclusive enrichments (agricultural tags, committee metadata) are unavailable.
3. **Agricultural tracker polish** – add manual curation tools, better sorting, and saved filter sets once Supabase performance is verified.

These items are optional until earlier phases are complete.

---

## Coordination Prompt
Use this prompt when spinning up a new engineering instance so they have the relevant context:

```
You are taking over maintenance of the DataViz Toolkit (Streamlit + Supabase). 
Key blockers already identified:
1. Campaign Finance page crashes due to invalid number_input config and still contains unfinished union-analysis code that must be removed entirely.
2. Vote Tracker still carries legacy OpenStates code paths even though all data now lives in Supabase; consolidate on the Supabase helpers and fix the title-search bug.
3. Data import/classification scripts still include safety hacks (e.g., page limits) that leave Supabase datasets incomplete.
4. The Python environment currently segfaults when importing pandas, so tests cannot run.

Work through the remediation plan in PLAN.md phase by phase, verifying each Streamlit page after changes, and finish by restoring a healthy `pytest` run. Coordinate with the team if you need Supabase credentials or LegiScan snapshots.
```

---

**Author:** Codex CLI – GPT-5 instance  
**Last Updated:** 2025-11-11
**Phase 1 Prompt**
```
Focus on Campaign Finance stability:
- Fix the sidebar number_input crash by providing a real default and separate “Load entire file” control.
- Remove `detect_union_labor`, union session-state columns, union dashboards, PDF chart options, and any other union references from `pages/1_Campaign_Finance.py`.
- Re-test the Campaign Finance page end-to-end to ensure no new warnings appear.
Deliver updated screenshots/logs if anything unexpected pops up.
```
**Phase 2 Prompt**
```
We have fully migrated to Supabase data. Clean up the vote tracker by:
- Removing the `USE_SUPABASE` toggle and the entire OpenStates fallback from `openstates/__init__.py` and `pages/2_Vote_Tracker.py`.
- Making sure `openstates.supabase_api` exposes every helper (`fetch_legislator_votes`, `fetch_bill_details`, etc.) with signatures that match the Streamlit usage.
- Fixing the bill search fallback so the title search doesn’t inherit the bill-number filter.
- Manually run through both tabs (legislators and bills) to confirm search, profile view, authored bills, and vote timelines all work with Supabase.
Document any data assumptions or missing indexes you encounter.
```
**Phase 3 Prompt**
```
Hardening imports/classifiers:
- Parameterize `import_legiscan_data.py` and `import_legiscan_data_v2.py` with CLI flags (dataset directory, optional session filters, dry-run/dev limits) so default runs import every session without code edits.
- Ensure both LegiScan importers share logging helpers, populate `session_name`, and avoid redundant logic paths that drift out of sync.
- Review classifier scripts to confirm category/priority enums match `openstates/agricultural_classifier.py`, and note any gaps needing tests later.
Provide a short summary of how long a full session import takes and any performance pain points.
```
**Phase 4 Prompt**
```
Environment repair:
- Rebuild the Python virtualenv (document Python version) until `python -c "import pandas"` succeeds without segfaulting.
- Run `pytest` and fix any failures; add minimal new tests if needed to cover regression risk from earlier phases.
- Update README (or a new CONTRIBUTING.md) with the exact setup commands, dependency versions, and troubleshooting tips for macOS arm64.
Share the final `pip freeze` in the PR/notes so the next engineer can replicate the working env.
```
**Phase 5 Prompt**
```
With stability restored, explore targeted optimizations:
- Profile Campaign Finance interactions and propose caching/lazy-loading strategies.
- Improve Vote Tracker UX (pagination, clearer Supabase-only messaging).
- Polish Agricultural Tracker filters/curation workflows.
Each idea should include effort estimate, dependencies, and metrics/KPIs to watch once implemented.
```
