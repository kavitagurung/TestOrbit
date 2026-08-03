# Architecture

TestOrbit is a monorepo with a React/Vite frontend and FastAPI backend. Local development uses SQLite; deployment can use PostgreSQL. Collection, normalization, snapshots, differences, deterministic scoring, AI interpretation, and evidence storage are isolated stages so each is observable and testable. Gemini is optional, server-side only, and must return Pydantic-validated structured output. The synthetic demo operates without it.

