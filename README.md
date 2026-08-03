# TestOrbit

AI-powered competitive intelligence for test-automation Product Managers.

This repository contains a deliberately synthetic local demo. It does not include confidential product information, real competitor assertions, credentials, or automated collection against external sites.

## Local setup

Frontend:

```bash
npm install
npm run dev
```

Backend (Python 3.11+ recommended):

```bash
cd apps/api
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

Copy `.env.example` to `.env` only when configuring server-side integrations. Never put secrets in frontend variables or commit `.env`.

## Deployment

The frontend is configured for GitHub Pages through `.github/workflows/deploy-pages.yml`. The backend Blueprint is `render.yaml`; Render secrets are declared as dashboard-managed values and are not committed. Configure the frontend origin in Render as `ALLOWED_ORIGINS` after Pages is live.

## Safety stance

The collector architecture will enforce public-source-only collection, robots.txt and terms boundaries, SSRF controls, private-IP blocking, response limits, rate limits, and prompt-injection isolation. LinkedIn, private, signed-in, paywalled, CAPTCHA-protected, and customer-portal sources are excluded.
