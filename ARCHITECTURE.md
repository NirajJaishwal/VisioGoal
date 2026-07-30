# Football Intelligence Platform — Technical Architecture (MVP)

> **Scope:** 2-day MVP, built so nothing has to be thrown away when it scales.
> **Leagues:** EPL, La Liga, Bundesliga, Serie A, Ligue 1.

This document reflects the **approved MVP-narrowed scope**. Deferred items are listed in
§13 so the boundary is explicit.

---

## 0. Guiding Decisions

- **Monorepo**, single FastAPI backend, single Next.js frontend. No microservices.
- **Ingest offline, serve online.** Batch jobs fetch → clean → load → embed. The API and
  RAG layer only ever *read* pre-computed data. Never call external APIs on the request path.
- **RAG is deliberately transparent** for the MVP: hand-written pipeline (embed → retrieve →
  prompt → generate) using the **Anthropic SDK + ChromaDB + Sentence Transformers**.
  No LlamaIndex, no agents, no tool-calling, no SQL-agent — so the pipeline is fully legible.

---

## 1. Repository Structure

```
football-intel/
├── docker-compose.yml            # postgres · chromadb · backend · frontend · ingestion
├── .env.example
├── .gitignore
├── README.md
├── ARCHITECTURE.md
│
├── frontend/                     # Next.js (App Router) + TS + Tailwind
│   ├── src/
│   │   ├── app/                  # routes: dashboard, teams, matches, chat
│   │   ├── components/{ui,charts,chat}/
│   │   ├── lib/                  # api client, formatters
│   │   └── types/                # TS types mirroring backend schemas
│   ├── package.json · tsconfig.json · next.config.mjs
│   ├── tailwind.config.ts · postcss.config.mjs · Dockerfile
│
├── backend/                      # FastAPI
│   ├── app/
│   │   ├── main.py               # app factory (added next phase)
│   │   ├── core/                 # config, logging, deps
│   │   ├── api/v1/               # routers: leagues, teams, matches, standings, chat
│   │   ├── models/               # SQLAlchemy ORM
│   │   ├── schemas/              # Pydantic I/O
│   │   ├── services/             # business logic
│   │   ├── ai/                   # RAG: embeddings, retriever, prompts, generate
│   │   └── db/                   # session/base
│   ├── alembic/ · alembic.ini    # migrations
│   ├── tests/
│   ├── pyproject.toml · Dockerfile
│
├── ingestion/                    # batch pipeline (separate lifecycle)
│   ├── sources/                  # external API adapters
│   ├── transform/                # pandas cleaning/normalization
│   ├── load/                     # idempotent upserts → postgres
│   ├── embed/                    # summaries → embeddings → chromadb
│   ├── pipelines/                # daily_refresh.py, backfill.py
│   ├── pyproject.toml · Dockerfile
```

`ingestion/` is a peer of `backend/` (different lifecycle). `ai/` lives *inside* the backend
(shares DB + config; extracting it now would add a needless network hop).

---

## 2. Frontend Architecture

- **App Router + Server Components** for data pages (leagues, teams, matches, standings),
  cached with Next's fetch revalidation — football data changes slowly, so caching is free wins.
- **Client Component chat** with **SSE streaming** from FastAPI for token-by-token answers.
- `lib/api.ts` = one typed fetch wrapper (base URL + error handling in one place).
- Charts via **Recharts**. State kept minimal — TanStack Query only in interactive areas.

---

## 3. Backend Architecture

```
Router (api/v1)  →  Service (services)  →  ORM (models)  →  Postgres
                        │
                        └→  ai/  →  ChromaDB + Claude API
```

- Thin routers (validate → call service → return schema). No logic in routers.
- Async SQLAlchemy + async Anthropic calls, so a slow LLM never blocks stat endpoints.
- Config via `pydantic-settings` from env; centralized logging + a global error handler;
  CORS locked to the frontend origin.

---

## 4. Database Design (MVP)

PostgreSQL is the single source of truth. **Six tables** for the MVP:

```
leagues       (id, code, name, country, season)
teams         (id, league_id → leagues, name, short_name, crest_url, venue)
matches       (id, league_id → leagues, home_team_id → teams, away_team_id → teams,
               matchday, kickoff_utc, status, home_score, away_score)
standings     (id, league_id → leagues, team_id → teams, season, position,
               played, won, drawn, lost, goals_for, goals_against, goal_difference, points)
                                        -- this table carries "basic team statistics"
documents     (id, entity_type, entity_id, content, chroma_id, updated_at)
chat_messages (id, session_id, role, content, created_at)
```

- `standings` **is** the basic-team-stats table for the MVP (W/D/L, GF/GA, points) — no
  separate `team_stats` needed yet.
- `documents` mirrors what's embedded in ChromaDB (Postgres keeps the source text; Chroma
  keeps vectors + ids), so the vector store is rebuildable from Postgres at any time.
- `season` is a first-class column so multi-season is a data change, not a schema change.
- Alembic from day one; indexes on FKs, `(league_id, season)`, `matches.kickoff_utc`.

---

## 5. API Design

RESTful, versioned `/api/v1`, OpenAPI auto-documented.

```
GET  /api/v1/leagues
GET  /api/v1/leagues/{id}/standings?season=2024
GET  /api/v1/teams/{id}
GET  /api/v1/matches?league_id=&matchday=
POST /api/v1/chat                     # {query, session_id?} → SSE stream
```

Plural nouns, query-param filtering, consistent `{error:{code,message}}` envelope.
`/chat` streams (SSE); everything else returns JSON. Frontend TS types generated from OpenAPI.

---

## 6. AI / RAG Architecture (simple & transparent)

Hand-written pipeline — no framework abstraction — so the mechanics are visible:

```
User query
   │  embed query (Sentence Transformers)
   ▼
ChromaDB similarity search → top-k football summary documents
   │  assemble context (retrieved docs only)
   ▼
Claude (Anthropic SDK), streaming
   │  system prompt: answer ONLY from context; say "I don't have that data" otherwise
   ▼
SSE → frontend   (+ persist turn to chat_messages)
```

**Embedded documents** are natural-language summaries generated by ingestion — one per
league, team, and (optionally) matchday — e.g. *"In the 2024 season Arsenal have won X,
drawn Y, sit Nth with Z points…"*. LLMs ground far better on prose than on raw rows.

**Explicitly not in the MVP:** agents, tool/function calling, SQL agents, hybrid
structured+semantic retrieval. (Semantic-only retrieval keeps the pipeline understandable;
hybrid is a documented post-MVP upgrade.)

**Models:** Claude via the Anthropic SDK (model id from env, verified against the current
`claude-api` reference at implementation time). Embeddings: `all-MiniLM-L6-v2` (local,
free, fast — no external embedding dependency).

---

## 7. Data Ingestion Pipeline

Batch jobs, fully decoupled from the API:

```
Fetch (sources/)   → raw JSON, cached to disk
Transform (transform/) → pandas clean/normalize (names, matchdays, scores)
Load (load/)       → idempotent UPSERT on external ids (safe to re-run)
Embed (embed/)     → build NL summaries for changed entities → embed → upsert ChromaDB
                     → record text + chroma_id in `documents`
```

MVP orchestration: a plain `pipelines/daily_refresh.py` entrypoint + a `backfill.py` for the
initial load. Run on demand (`docker compose run ingestion`) — no scheduler yet.

---

## 8. External API Integration

- **Source:** Football-Data.org (free tier covers the top-5 leagues) behind an **adapter
  protocol** (`sources/base.py`). The rest of the pipeline depends on the protocol, never on
  a vendor's JSON shape — so a richer paid source drops in later untouched.
- Resilience: respect rate limits, retry with backoff, cache raw responses to disk. External
  calls happen only in ingestion, never on the request path.

---

## 9. Development Phases (2 days)

**Day 1 — Foundations & Data**
1. Scaffold + docker-compose boots the stack. *(this step)*
2. ORM models + Alembic migration (6 tables).
3. Ingestion: Football-Data adapter → transform → load. Real data in Postgres.
4. Read endpoints: leagues, teams, matches, standings + OpenAPI.

**Day 2 — Intelligence & UI**
5. Embedding job → summaries → ChromaDB.
6. `POST /chat`: embed → retrieve → prompt → Claude (streaming), persist to `chat_messages`.
7. Frontend: dashboard, team/matches/standings pages with charts, streaming chat.
8. Polish: error handling, empty states, README.

---

## 10. Recommended Dependencies

**Backend:** `fastapi`, `uvicorn[standard]`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`,
`pydantic`, `pydantic-settings`, `anthropic`, `chromadb`, `sentence-transformers`, `httpx`.
Dev: `pytest`, `pytest-asyncio`, `ruff`.

**Ingestion:** `pandas`, `httpx`, `sqlalchemy`, `asyncpg`, `chromadb`, `sentence-transformers`.

**Frontend:** `next`, `react`, `typescript`, `tailwindcss`, `@tanstack/react-query`,
`recharts`, `zod`, `clsx`, `tailwind-merge`.

---

## 11. Security (MVP-appropriate)

- Secrets via env only (`.env` git-ignored, `.env.example` committed).
- Anthropic key lives server-side; the frontend never sees it — all AI calls proxy through FastAPI.
- Pydantic validation on every endpoint; cap chat input size.
- Treat retrieved documents as data, not instructions (basic prompt-injection hygiene).
- Parameterized queries only (SQLAlchemy). CORS restricted to the frontend origin.
- **No auth in the MVP** (public football data only) — deferred.

---

## 12. Deployment (MVP)

Local **Docker Compose** only: `postgres · chromadb · backend · frontend · ingestion`
(ingestion runs on demand). Multi-stage-ready Dockerfiles, healthchecks, `depends_on`
ordering. **CI/CD, cloud hosting, and scaling are out of scope for now.**

---

## 13. Explicitly Deferred (post-MVP)

Player analytics · xG/xA · injuries · heatmaps · advanced metrics · hybrid/SQL retrieval ·
agents & tool-calling · LlamaIndex · Redis caching · authentication · CI/CD · cloud deploy ·
multi-season history (schema already supports it) · scheduler for ingestion.

---

## Assumptions

1. Single current season for the MVP (schema allows multi-season later).
2. Football-Data.org free tier is sufficient; adapter allows upgrade.
3. No user accounts. Read-heavy, slow-changing data → caching is easy and effective.
