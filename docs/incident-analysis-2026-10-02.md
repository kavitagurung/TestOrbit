# TestOrbit diagnosis and repair — October 2, 2026

Status: source fixes implemented and tested; production deployment and model configuration pending. This report distinguishes observed production behavior, confirmed code defects, and remaining uncertainties.

## What was actually happening

TestOrbit was reachable. GitHub Pages served its frontend and the Render analysis endpoint returned HTTP 200. The API response used `mode: rule_based_fallback`. The first browser view showed loading; returning to the dashboard later displayed the fallback summary.

Render's live deployed commit was `86d6f92`, matching the source reviewed. Its environment list included `OPENAI_API_KEY`, `DATABASE_URL`, owner/Supabase authentication variables, and Slack configuration. `OPENAI_MODEL` was not listed. No secret values were revealed or copied, so key validity and quota are not established.

The latest inspected scheduled run, [36979028251](https://github.com/kavitagurung/TestOrbit/actions/runs/36979028251), completed at approximately 13:02 IST on October 2. Its result said `ran: true`, seven sources checked, zero new baselines, `failed_sources: ["Opkey"]`, and `slack_delivered: true`. This disproves the initial suspicion that all collection had stopped. A direct request to the configured Opkey newsroom returned HTTP 403. The old collector suppressed exception details, so we cannot conclusively equate the historical failure with that later 403, although they are consistent.

Render explicitly warned that its free instance sleeps and may take 50 seconds or more to resume. Logs also showed a normal service shutdown. A cold start is a plausible contributor to initial loading delay, not proof of the exact cause of the original request failure.

## Confirmed defects and fixes

| Defect | User-visible consequence | Implemented repair |
|---|---|---|
| Analysis fetch catches errors by resetting data to null, the same state used for loading | Failed requests can show loading forever | Separate error state, 90-second deadline, Retry button, response-shape checks, cancellation and stale-response protection |
| API CORS permits GET/POST but omits PUT | Browser cannot save the owner schedule | Permit PUT for the existing approved origins; owner authentication remains mandatory |
| Every OpenAI failure returns the same silent fallback | UI incorrectly suggests adding a key for authentication, model, quota, timeout, or malformed-response errors | Safe reason codes and warning logs; explicit model configuration; JSON mode and server-side schema validation |
| Backend default assumes `gpt-5.6-sol`; model not explicitly configured in Render | Model availability depends on an unverified default | Require `OPENAI_MODEL`; document choosing a model supported by the project's API key |
| Fixed fallback themes and recommendations are returned even with zero selected evidence | Empty periods can still show specific market trends and fixed 78/66/64 scores | Remove manufactured fallback trends and scores; empty periods explicitly state the evidence gap; future evidence excluded |
| Successful synthesis cache indexed only by date range | Cache can outlive a model/evidence change | Cache key includes model and selected evidence |
| Dashboard imports static July/August evidence, independent of stored collector snapshots | A successful scheduled run never refreshes those cards | Add database-backed collection activity with actual snapshot dates; label existing research as saved curated evidence |
| “Sources checked 09:00” and “Coverage today” are hard-coded | Dashboard implies current verification without evidence | Remove fake source-check times and label saved coverage honestly |
| Workflow treats every HTTP 200 as success, ignoring failed sources | Partial collection looks green | Inspect response fields and fail the job for source/provider failures; log safe source diagnostics |
| Manual collection UI promises Slack delivery solely on HTTP 200 | User receives a success claim even when no Slack message was sent | Report source-failure count and actual Slack delivery result; catch network errors |
| Owner access failure hides login without recovery | Signed-in users can get stuck on the restricted area | Add Retry owner access and Sign out controls |
| “Today” default is evaluated when the Python module loads | Long-lived workers retain an old date | Compute the current date for each call |

The Slack briefing's static background is also relabelled as saved research and includes failed-source names when collection is incomplete. No live Slack message was sent during this repair.

## What is not fixed by merely adding an API key

The current verified-research pipeline is incomplete: curated cards and model evidence are saved records, whereas the collector detects whole-page changes and stores snapshots. A changed page may reflect navigation, cookie text, or unrelated content. Automatically presenting every change as a verified new feature would be inaccurate. The repair exposes collection activity separately and preserves the review distinction. It does not claim to have built a new extraction, deduplication, verification, and publication pipeline.

Likewise, the competitor directory has 40 entries, but this is not proof that 40 active collection integrations exist. The inspected run checked seven sources. The new sidebar uses “Directory entries” instead of “Competitors watched.” Some prototype areas, including the capability matrix and Claim Lens examples, remain outside this repair's scope.

The exact production OpenAI failure remains unproven: the old code did not log it, and the stored key was not used outside the service. `OPENAI_API_KEY` being present corrects the earlier suggestion that it necessarily needed adding. Configure an API model explicitly and use the new diagnostics before replacing any key or changing billing.

Opkey's 403 is an external source restriction. This patch reports it rather than bypassing it. A supported public feed/API or publisher-permitted alternative needs to be selected before that source can be considered healthy.

## Validation

- Backend suite: 45 tests passed, including empty periods, future evidence, missing configuration, provider error classes, timeout, invalid model output, cache invalidation, database snapshot activity, partial collection, and CORS PUT/denied-origin behavior.
- Frontend suite: 5 tests passed, including failure/retry, malformed payloads, timeout, and out-of-order range responses.
- TypeScript/Vite production build and ESLint passed.
- Existing dependency deprecation warnings remain; they did not fail the tests. Tests used local Python 3.14; Render is configured for 3.13.4.
- Real browser preview was attempted, but the browser connection became unavailable. DOM behavior is covered by the frontend tests; visual browser verification remains pending.
- No real OpenAI call, owner schedule write, forced production collection, or production deployment was performed.

## Deployment and remaining actions

1. Review and merge the repair, deploying the API before the updated frontend. No database migration is required.
2. Set `OPENAI_MODEL` to an available API model. `gpt-4.1-mini` is a documented example supporting the Responses API; actual project access still requires verification. Preserve the existing key unless diagnostics show a key problem.
3. Verify the production analysis result and its reason code; investigate authentication/quota/model access only as indicated.
4. Verify owner schedule saving through the browser and that stored collection activity renders. Do not force Slack delivery as a read-only check.
5. Resolve the Opkey source restriction using an authorized supported source. Expect partial-failure jobs to become visibly red until the source issue is addressed.
6. If fully automatic current research is the desired product, implement the missing reviewed evidence ingestion pipeline as follow-up work. Enabling AI synthesis does not create fresh evidence by itself.

References: [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs), [GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini), and the repository's Render deployment guide.
