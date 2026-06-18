# Understanding RecruitBot: Phase 0 Architecture & Implementation

This document serves as a comprehensive technical guide for engineering leadership to understand the foundational architecture (Phase 0) of the RecruitBot platform. It details the core systems built, design decisions made, and provides actionable steps to verify the implementation locally.

---

## 1. Executive Summary: Phase 0 Objectives

Phase 0 is the foundational layer of RecruitBot. Before building complex AI recruitment workflows, we needed a robust, secure, and compliant infrastructure. 

**The primary goals achieved in Phase 0 were:**
1.  **Canonical Data Model:** Establishing a PostgreSQL schema capable of handling high-dimensional vector embeddings (via `pgvector`) alongside standard relational data.
2.  **Centralized AI Governance:** Building an "LLM Gateway" to route all AI traffic, ensuring multi-provider fallback, PII anonymization, and strict cost/token telemetry.
3.  **Security & Identity:** Implementing a JWT-based authentication system with Role-Based Access Control (RBAC) to securely separate Hiring Managers, Recruiters, and Candidates.
4.  **Verifiable Infrastructure:** Proving the system works end-to-end (from database to API to LLM) using synthetic seed data and real API round-trips.

---

## 2. Architecture & Codebase Organization

RecruitBot utilizes a decoupled architecture with a strict separation of concerns, designed to scale to enterprise levels.

### 2.1 Technology Stack Deep-Dive
*   **Frontend:** React 19 + TypeScript + Vite. We leverage Tailwind CSS v4 for utility-first styling. During development, Vite proxies all `/api` requests to the FastAPI backend, eliminating CORS overhead.
*   **Backend:** FastAPI running on Python 3.11. Chosen for its native asynchronous capabilities (ASGI), auto-generated Swagger documentation, and Pydantic-driven request validation.
*   **Database Engine:** PostgreSQL 16 equipped with the `pgvector` extension.
*   **LLM Orchestration:** `litellm` (multi-provider proxy) + `instructor` (Pydantic schema enforcer) + `tenacity` (exponential backoff/retries).

### 2.2 High-Level File Structure
A high-level view of the monorepo architecture:

```text
recruitmentBot/
├── backend/                  # FastAPI Application
│   ├── alembic/              # Database migration scripts
│   ├── app/
│   │   ├── api/              # API Route Controllers (Auth, Requisitions, etc.)
│   │   ├── core/             # Auth logic, DB connection, Config, Prompts
│   │   ├── models/           # SQLAlchemy Models (pgvector schema)
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── services/         # LLM Gateway, Anonymizer, Telemetry
│   │   ├── main.py           # FastAPI application entry point
│   │   └── seed.py           # Synthetic data generator
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # React 19 + Vite Application
│   ├── src/
│   │   ├── App.tsx           # Main application dashboard
│   │   ├── index.css         # Tailwind v4 core styles
│   │   └── main.tsx
│   ├── vite.config.ts        # Vite config with backend API proxy
│   └── package.json
├── docker-compose.yml        # Orchestrates pgvector database & backend
├── package.json              # Root package to run `concurrently` dev server
├── .env.example              # Centralized environment configurations
└── IMPLEMENTATION_PLAN.md    # Master project roadmap
```

### 2.3 Backend Directory Deep-Dive (`backend/app/`)
The backend is organized via a modular monolith pattern:
*   `api/`: Contains all FastAPI routers (`routes.py`, `auth_routes.py`, `requisition_routes.py`, `llm_routes.py`). Each module defines request/response Pydantic models specific to its endpoints.
*   `core/`: Application-wide configurations and utilities.
    *   `config.py`: Centralized environment variable management using `pydantic-settings`.
    *   `database.py`: Asynchronous SQLAlchemy engine and session factory setup.
    *   `auth.py`: JWT token generation, decoding, and bcrypt password hashing.
    *   `dependencies.py`: Reusable FastAPI dependencies (e.g., `get_current_user`, `require_role`).
    *   `prompts.py`: The `PromptRegistry`, decoupling raw prompt strings from business logic.
*   `models/`: SQLAlchemy ORM models (`__init__.py`). Defines the canonical schema.
*   `services/`: Domain logic and external integrations.
    *   `llm.py`: The `LLMGateway` singleton.
    *   `anonymizer.py`: Regex-based PII redaction engine.
    *   `telemetry.py`: In-memory tracking of LLM costs and latency.

### 2.3 Request Lifecycle (Example: Requisition Creation)
When a Hiring Manager submits a job brief:
1.  **Ingress:** Request hits `POST /api/v1/requisitions`.
2.  **Authentication (Dependency Injection):** FastAPI invokes `Depends(require_role("hiring_manager"))`. This triggers `get_current_user`, which validates the JWT Bearer token via `core.auth.decode_access_token`.
3.  **Controller Logic:** A synchronous SQLAlchemy session is opened.
4.  **LLM Delegation:** The controller calls `llm_gateway.generate(prompt_name="jd_generation", ...)`.
5.  **Anonymization:** The Gateway passes the prompt inputs through `Anonymizer.redact()`.
6.  **Provider Routing:** LiteLLM routes the prompt to `anthropic/claude-sonnet-4-20250514`. If it times out, it falls back to `gemini/gemini-2.0-flash`.
7.  **Persistence:** The generated Job Description is saved to the `job_requisitions` table.
8.  **Audit Logging:** An immutable entry is written to `audit_log` linking the Hiring Manager's user ID to the new requisition ID.

## 3. Core Components Breakdown (Phase 0 Sprints)

### 3.1 Sprint 0.2: Database Schema & pgvector Deep-Dive
The database leverages **SQLAlchemy (Async)** and **Alembic**. The 10 foundational tables are strictly typed:

*   **Identity & Access:**
    *   `users`: Contains `hashed_password` (bcrypt) and `role` (`hiring_manager`, `recruiter`, `candidate`). Indexed on `email` and `role`.
    *   `consent`: DPDP compliance tracking. Contains `consent_type` (e.g., `ai_interviewing`), `ip_address`, and revocation timestamps.
*   **Core Recruitment Entities:**
    *   `employees`: Used to model "High Performers". Contains raw performance data and a 1024-dimension `embedding` vector representing their "Career DNA".
    *   `candidates`: External profiles.
    *   `job_requisitions`: Contains the `raw_brief` (manager input) and `generated_jd` (AI output). Also holds an `archetype_embedding` vector (the "ideal candidate" profile).
    *   `applications`: The junction table linking candidates to requisitions. Tracks pipeline state (`screening`, `interviewing`, etc.).
*   **AI Artifacts & Explainability:**
    *   `resumes`: Stores `raw_text` and a strictly enforced `parsed_json` structure. Includes semantic `embedding`.
    *   `interviews`: Stores the JSON transcript and AI-generated `soft_skill_markers` (e.g., `{"communication": 0.85}`).
    *   `fit_scores`: Implements the 30/40/30 weighted ranking model. Contains a `rationale_json` to explain *why* the AI assigned a specific score, ensuring auditability.
*   **Audit Logging:**
    *   `audit_log`: Every single action (AI recommendation, human override, consent change) writes here. It is immutable and indexed by `entity_type` and `actor_id`.

**The Power of `pgvector`:** We configured the vector columns (e.g., `Employee.embedding = Column(Vector(1024))`) using `pgvector`. This allows us to perform high-speed cosine similarity searches directly inside SQL queries (`ORDER BY embedding <=> query_vector`). We use 1024 dimensions specifically to match the output of Voyage AI/Cohere embedding models, eliminating the need for an external vector database like Pinecone.

### 3.2 Sprint 0.3: The LLM Gateway & Guardrails
To prevent scattered, unmonitored API calls ("spaghetti AI"), we instituted a strict singleton **LLM Gateway Pattern** (`app/services/llm.py`). No developer is allowed to call `openai.ChatCompletion` directly.

*   **Multi-Provider Abstraction (LiteLLM):** The gateway uses `litellm`. We define "Tiers" in `config.py` rather than hardcoding models:
    *   `model_premium`: e.g., `anthropic/claude-sonnet-4-20250514` (Used for complex logic like JD generation).
    *   `model_fast`: e.g., `anthropic/claude-haiku-4-5-20251001` (Used for quick data extraction).
    *   `model_fallback`: e.g., `gemini/gemini-2.0-flash`.
    *   *Resilience:* If the primary Anthropic API goes down, the `@retry` decorator triggers, and if it completely fails, LiteLLM automatically routes the request to Gemini without the caller service ever knowing.
*   **Structured Output (Instructor):** When we need structured data (like parsing a resume into JSON), the gateway exposes `generate_structured()`. This uses the `instructor` library to pass a Pydantic schema to the LLM. If the LLM hallucinates an invalid JSON structure, Instructor automatically catches the validation error and prompts the LLM to fix it.
*   **AI Firewall (Anonymizer):** Data minimization is a strict requirement for DPDP. Before text reaches any external LLM, the `Anonymizer` class intercepts it. It uses highly tuned regex patterns to scrub Indian phone numbers (`+91...`), Emails, Aadhaar IDs, and PAN cards, replacing them with tokens like `[REDACTED_EMAIL]`.
*   **Telemetry Ring Buffer:** Every call logs `prompt_name`, `tokens_used`, `latency_ms`, and `cost_usd` to an in-memory ring buffer (exposed via `/api/v1/llm/telemetry/stats`). The cost is calculated accurately based on the specific model used via LiteLLM's pricing dictionaries.

### 3.3 Sprint 0.4: Auth & Role-Based Access Control
We implemented a robust JWT-based authentication system using `bcrypt` (used directly to avoid passlib compatibility issues with bcrypt>=5.0) and `python-jose` for token generation.

**1. Token Issuance & JWT Payload:**
When a user logs in via `POST /api/v1/auth/login`, we generate a JWT containing the following claims:
*   `sub`: The user's UUID.
*   `email`: The user's email address.
*   `role`: The user's assigned role (`hiring_manager`, `recruiter`, `candidate`).
*   `exp` / `iat`: Expiry and Issued-At timestamps.

**2. FastAPI Dependency Injection (`app/core/dependencies.py`):**
We utilize FastAPI's powerful dependency injection system to protect routes effortlessly:
*   `Depends(get_current_user)`: Extracts the `Authorization: Bearer <token>` header, decodes the JWT using our `JWT_SECRET_KEY`, and returns the user payload. If the token is expired or tampered with, it throws a `401 Unauthorized` exception before the controller logic even begins.
*   `Depends(require_role("hiring_manager", "recruiter"))`: A factory function that wraps `get_current_user`. It checks the decoded `role` claim. If a candidate tries to access this route, it throws a `403 Forbidden` exception.

**3. Controller Logic ("Real Wiring" Example):**
In `POST /api/v1/requisitions`, we killed the frontend "setTimeout" fake and wired the backend:
1.  The route requires the `hiring_manager` or `recruiter` role.
2.  The controller receives the `CreateRequisitionRequest` Pydantic model (validating string lengths and required fields).
3.  It calls the LLM Gateway (`llm_gateway.generate(prompt_name="jd_generation", ...)`) to automatically write a professional Job Description based on the manager's brief. *(Note: If the Anthropic API key is not configured, the code gracefully falls back to a string stub so development can continue uninterrupted).*
4.  It opens a synchronous database session, `INSERT`s the new job into `job_requisitions`, and immediately `INSERT`s an audit trail into `audit_log` linking the manager's user ID.

*Design for the Future:* Because we use `get_current_user` to extract claims, if the company later decides to use an external OIDC provider (like Auth0, Azure AD, or Keycloak), we only need to swap the token decoding logic. The route protection logic remains 100% untouched.

## 4. Local Setup & Verification Guide

This section is specifically for engineering leadership to independently run and verify the Phase 0 deliverables.

### Prerequisites
1.  Python 3.11 installed.
2.  Docker and Docker Compose installed (for the Postgres database).
3.  Node.js (for the frontend).

### Step-by-Step Verification

**1. Boot the Infrastructure (Database)**
```bash
# In the root directory
docker-compose up -d
```
*Verification:* Run `docker ps`. You should see `recruitbot-db` running using the `pgvector/pgvector:pg16` image.

**2. Setup the Backend & Run Migrations**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run database migrations to create the 10 tables
alembic upgrade head
```
*Verification:* Check your local postgres instance on port `5432` (user: `recruit_admin`, pass: `localdevsecret`). You will see all tables created.

**3. Seed the Database with Synthetic Data**
```bash
python -m app.seed
```
*Verification:* This script generates 10 employees, 3 requisitions, and 30 candidates with mathematically valid 1024-dim `pgvector` embeddings. It will output "Database seeding complete!" upon success.

**4. Start the Application**
```bash
# In the root directory, start both Frontend and Backend concurrently
npm run dev
```

### 5. API Verification Tests

Once the backend is running (typically on `http://localhost:8000`), you can use standard tools (Postman, cURL, or the built-in Swagger docs at `http://localhost:8000/docs`) to verify the core mechanisms:

**Test 1: LLM Gateway Configuration**
*   **Action:** `GET http://localhost:8000/api/v1/llm/models`
*   **Expected:** Returns JSON showing pinned models (e.g., Claude 3.5 Sonnet for premium, Gemini 2.0 Flash for fallback).

**Test 2: Role-Based Access Control (RBAC) & Requisition Flow**
1.  **Register a Candidate:**
    *   `POST /api/v1/auth/register` with body `{"email":"test@example.com", "password":"password123", "first_name":"Test", "last_name":"User", "role":"candidate"}`.
    *   Save the returned `access_token`.
2.  **Verify RBAC Denial:**
    *   Attempt `POST /api/v1/requisitions` using the Candidate's token.
    *   **Expected:** `403 Forbidden` (Role 'candidate' not authorized. Required: hiring_manager, recruiter).
3.  **Register a Hiring Manager:**
    *   `POST /api/v1/auth/register` with role `hiring_manager`.
    *   Save the new `access_token`.
4.  **Create Requisition (Real Wiring):**
    *   `POST /api/v1/requisitions` using the Hiring Manager's token. Provide a basic JSON body with a `title` and `raw_brief`.
    *   **Expected:** `201 Created`. The system attempts to generate an AI JD. It saves to the DB and creates an audit log entry.

**Test 3: Telemetry**
*   **Action:** `GET http://localhost:8000/api/v1/llm/telemetry/stats`
*   **Expected:** Returns real-time aggregate statistics for LLM usage (token counts, estimated cost in USD, and total API calls).

---
*End of Document. Phase 0 Foundation complete.*
