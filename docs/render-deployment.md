# Render deployment guide

Create a backend web service from `apps/api`, set its start command to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, and configure server-side environment values in Render. Do not deploy until explicitly approved.


## Analysis repair configuration

- Keep the existing `OPENAI_API_KEY` server-side. Its presence alone does not prove validity or available quota.
- Set `OPENAI_MODEL` explicitly to a Responses API model available to the key's project (for example `gpt-4.1-mini`). The repaired code no longer assumes `gpt-5.6-sol` is available.
- Keep `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `OWNER_EMAIL` configured. Do not put server keys in Vite variables.
- On an existing Blueprint, verify optional environment variables in the dashboard; do not assume adding `sync: false` declarations populates existing services.
- Deploy the backend before the frontend uses `/api/v1/intelligence/collection-activity`. No schema migration is needed; the endpoint reads existing snapshots.
- After deployment, check the analysis response's `fallback_reason` and Render warning logs. Reasons distinguish missing configuration, authentication/access/model errors, quota/rate limits, timeouts, connectivity, and invalid model output. Logs deliberately omit keys and provider response bodies.
- Confirm a `PUT` preflight from the GitHub Pages origin succeeds, then verify owner access normally. Authentication is still required.
- Scheduled jobs now fail visibly for source/provider failures. A red run can be a partial collection, not a total API outage. Inspect `failure_details`; do not repeatedly force collections just to get a green check.
- The free service can sleep. Requests wait up to 90 seconds before offering Retry; this does not remove cold starts.

For local verification, run the API on port 8000 and the frontend with `VITE_API_BASE_URL=http://localhost:8000` on `http://localhost:5173`.
