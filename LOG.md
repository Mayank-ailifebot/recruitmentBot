# RecruitBot — Implementation Log

This document tracks the chronological progress of the RecruitBot implementation, detailing completed features, structural changes, and sprint accomplishments.

---

## Initial Foundation Setup (Pre-Sprint 0.1)

**Date:** 2026-06-18
**Focus:** Monorepo Initialization & Verification

*   **Architecture & Monorepo:**
    *   Established root monorepo containing `frontend/` (Vite/React) and `backend/` (FastAPI).
    *   Configured root `package.json` with `concurrently` to run both services simultaneously via `npm run dev`.
    *   Configured Vite proxy (`vite.config.ts`) to seamlessly route `/api` requests to the FastAPI backend on port 8000, eliminating local CORS issues.
    *   Created comprehensive `.gitignore` covering Python caches, Node modules, env files, and build outputs.

*   **Frontend Setup:**
    *   Scaffolded modern React 19 + TypeScript + Vite project.
    *   Integrated **Tailwind CSS v4** via the `@tailwindcss/vite` plugin.
    *   Built a CSS-first design system (`src/index.css`) establishing a premium dark-mode aesthetic, custom gradients, and glassmorphism utilities.
    *   Linked Google Fonts (Inter, Outfit, JetBrains Mono) in `index.html`.
    *   Developed a live status dashboard (`App.tsx`) to verify end-to-end connectivity with the backend.

*   **Backend Setup:**
    *   Configured modular FastAPI architecture (`app/api`, `app/core`, `app/models`, `app/schemas`, `app/services`).
    *   Created central entry point (`main.py`) with CORS middleware and API router.
    *   Implemented `pydantic-settings` (`core/config.py`) for centralized environment variable management.
    *   Added health-check endpoints (`/api/v1/health`) to monitor system readiness.

---

## Phase 0 — Sprint 0.1: Environments & CI/CD

**Date:** 2026-06-18
**Focus:** Project Skeleton, Docker, and Compliance

*   **Environment Configuration:**
    *   Created comprehensive `.env.example` mapping essential configuration keys for Database connections, Anthropic/Voyage AI APIs, and JWT security.
    *   Enforced **Python 3.11** runtime standard across the project, including local virtual environment recreation.

*   **Docker Orchestration:**
    *   Developed `docker-compose.yml` to orchestrate local infrastructure, featuring a `pgvector/pgvector:pg16` database service and the FastAPI backend.
    *   Built `backend/Dockerfile` using `python:3.11-slim` and configured `backend/.dockerignore`.

*   **CI/CD Pipeline:**
    *   Created `.github/workflows/ci.yml` defining automated GitHub Actions for code checkout, dependency installation, and `flake8` linting/testing gates.

*   **Compliance & Data Residency:**
    *   Authored `DOCS_DATA_RESIDENCY.md` establishing the architectural baseline for India-region AWS/GCP hosting, DPDP Act compliance (affirmative consent, right to erase), and PII anonymization protocols.

---

## Phase 0 — Sprint 0.2: Data Model, Database & Seed Data

**Date:** 2026-06-18
**Focus:** Canonical Schema, pgvector Integration, and Synthetic Data

*   **Database Infrastructure:**
    *   Installed and configured asynchronous SQLAlchemy stack (`sqlalchemy[asyncio]`, `asyncpg`, `pgvector`, `alembic`).
    *   Configured async database connection and session factory in `app/core/database.py`.

*   **Canonical Schema Definition:**
    *   Defined 9 foundational database models in `app/models/__init__.py`:
        1.  `Employee`: Internal staff with performance metrics and 1024-dim Career DNA embeddings.
        2.  `Candidate`: External applicants and sourced profiles.
        3.  `JobRequisition`: Job openings, JD content, and archetype vectors.
        4.  `Application`: Pipeline state tracking linking candidates to jobs.
        5.  `Resume`: Raw text, parsed JSON schemas, and semantic embeddings.
        6.  `Interview`: Session states, chat transcripts, soft-skill markers, and snapshot anomalies.
        7.  `FitScore`: Weighted 30/40/30 scoring model for candidate ranking.
        8.  `Consent`: DPDP compliance tracking per candidate.
        9.  `AuditLog`: Immutable tracking of AI recommendations and human overrides.

*   **Migrations (Alembic):**
    *   Initialized Alembic and configured `alembic/env.py` to auto-detect models and handle dynamic database URLs.
    *   Generated initial migration script (`init_all_tables`) and executed `alembic upgrade head` to instantiate the schema on the active Postgres container.
    *   Successfully ran up/down rollback tests.

*   **Synthetic Seed Generator:**
    *   Developed `app/seed.py` to populate the database with realistic fake data.
    *   Generated 10 top-performing employees, 3 active job requisitions, and 30 candidates (including 5 "silver medalists").
    *   Created simulated applications, fit scores, and consent records.
    *   Implemented mathematically valid, cluster-based 1024-dimension normalized vectors to mock embedding API outputs.
    *   Built and verified a `pgvector` cosine similarity sanity test comparing top employees against candidate resumes.

---
## Phase 0 — Sprint 0.3: LLM Gateway & Guardrail Scaffold

**Date:** 2026-06-18
**Focus:** Unified Multi-Provider LLM Gateway, Prompt Registry, Telemetry & PII Anonymization

*   **Package Selection & Installation:**
    *   Chose **LiteLLM** as the multi-provider gateway (supports 100+ providers including Anthropic, Google, OpenAI via a unified API).
    *   Chose **Instructor** for structured JSON output enforcement (validates LLM responses against Pydantic schemas).
    *   Installed `litellm`, `instructor`, and `tenacity` (retry logic).

*   **Config Updates (`app/core/config.py`):**
    *   Pinned model IDs in config using LiteLLM's `provider/model` format:
        *   **Premium tier:** `anthropic/claude-sonnet-4-20250514` (JD generation, screening, snapshots).
        *   **Fast tier:** `anthropic/claude-haiku-4-5-20251001` (parsing, classification).
        *   **Fallback:** `gemini/gemini-2.0-flash` (used when primary provider fails).
    *   Added API key support for Anthropic, Gemini, and OpenAI — switching providers is a one-line config change.

*   **Prompt Template Registry (`app/core/prompts.py`):**
    *   Built a centralized, versioned prompt management system.
    *   Registered 5 SOW-aligned prompt templates:
        1.  `jd_generation:v1` — Inclusive JD generation from manager briefs.
        2.  `resume_parsing:v1` — Structured data extraction from resumes.
        3.  `fit_score_evaluation:v1` — 30/40/30 weighted scoring (bias-blind).
        4.  `interview_followup:v1` — Dynamic follow-up question generation.
        5.  `candidate_snapshot:v1` — Vibe Check + Red Flags + Top 3 Reasons summary.

*   **LLM Gateway Service (`app/services/llm.py`):**
    *   Created the `LLMGateway` class — single audited chokepoint for ALL model traffic.
    *   `generate()` — text generation with automatic fallback and telemetry.
    *   `generate_structured()` — returns validated Pydantic model instances via Instructor.
    *   Built-in retry logic, timeout handling, and provider failover.

*   **PII Anonymization / AI Firewall (`app/services/anonymizer.py`):**
    *   Regex-based anonymizer that strips emails, Indian phone numbers, Aadhaar, PAN, and URLs before sending text to external LLM APIs.
    *   Tracks redaction counts for audit compliance.

*   **Telemetry Service (`app/services/telemetry.py`):**
    *   In-memory ring buffer logging every LLM call with: model, tokens, estimated cost (USD), latency, prompt metadata, and anonymization status.
    *   Model-specific cost estimation using current provider pricing tables.
    *   Aggregate stats endpoint for monitoring.

*   **API Routes (`app/api/llm_routes.py`):**
    *   `GET /api/v1/llm/models` — shows pinned model IDs per tier.
    *   `GET /api/v1/llm/prompts` — lists all registered prompt templates.
    *   `GET /api/v1/llm/telemetry/stats` — aggregate usage statistics.
    *   `GET /api/v1/llm/telemetry/recent` — recent call events.
    *   `POST /api/v1/llm/generate` — test generation endpoint (dev only).

*   **Verification:**
    *   Server starts cleanly with all new modules loaded.
    *   All 5 API endpoints return correct responses.
    *   Telemetry stats initialize at zero and are ready for live calls.

---
*Log ends here. Ready for Sprint 0.4.*
