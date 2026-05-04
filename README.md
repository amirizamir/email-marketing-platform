# Internal Email Marketing Platform

**FastAPI** + **PostgreSQL** + **Redis** + **Alembic** + **email worker** + **Next.js (App Router)** with **Nginx** as a single Docker deployment (no local installs required for production use).

## Deploy with Docker (recommended)

1. **Create environment file** in the project root (next to `docker-compose.yml`):

   ```bash
   cp deploy.env.example .env
   ```

2. **Edit `.env`**: set at least `SECRET_KEY` and `ENCRYPTION_KEY` to strong values (and `POSTGRES_PASSWORD` in production).  

   - `SECRET_KEY`: e.g. `openssl rand -hex 32`  
   - `ENCRYPTION_KEY` (Fernet, for SMTP passwords at rest):  
     `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

3. **Start the stack**:

   ```bash
   docker compose up -d --build
   ```

4. **Open the app** (default port **8080** — see `HTTP_PORT` in `.env`):

   - **UI + API (same origin):** `http://localhost:8080`  
   - **OpenAPI:** `http://localhost:8080/docs`  
   - **API health:** `http://localhost:8080/health`  

Nginx routes `/` to the Next.js app and `/api/...` to FastAPI, so the browser does **not** need `NEXT_PUBLIC_API_URL` (leave it empty in `.env`).

Services: **Postgres** (data), **Redis** (queue + rate keys), **api** (migrations on boot), **worker** (sends mail), **web** (Next.js), **nginx** (entry point). Database and Redis are **not** exposed to the host by default (internal network only).

### Optional: API on a different host than the UI

If the UI is served from a different origin than the API, rebuild the `web` image with:

```bash
NEXT_PUBLIC_API_URL=https://api.example.com docker compose build web --no-cache
docker compose up -d
```

Set `NEXT_PUBLIC_API_URL` to the **browser-visible** API base (no trailing slash).

---

## Architecture

- **API** (`backend/app`): JWT auth, tenant isolation, SlowAPI rate limits, Fernet encryption for SMTP secrets.
- **Worker** (`backend/app/worker/email_worker.py`): Reads pending `email_jobs`, **per-SMTP-account** spacing via Redis (`≥10s + jitter`), pause/resume/schedule.
- **Queue**: API `LPUSH` to `email_campaign_queue` on start/resume; PostgreSQL remains the source of truth.
- **Frontend** (`frontend/`): Dashboard, SMTP, CSV contacts, HTML templates (`{{email}}`, etc.), campaigns, live stats.

## API (under `/api/v1`, Bearer token except `POST /auth/*`)

| Area      | Endpoints |
|-----------|-----------|
| Auth      | `POST /auth/register`, `POST /auth/login` |
| SMTP      | `POST/GET /smtp`, `POST /smtp/test`, `POST /smtp/test-existing` |
| Lists     | `POST/GET /lists` |
| Contacts  | `POST /contacts/upload`, `GET /contacts`, `DELETE /contacts` |
| Templates | `POST/GET /templates`, `GET/PUT /templates/{id}` |
| Campaigns | `POST/GET /campaigns`, `PUT /campaigns/{id}`, `POST .../start`, `pause`, `resume`, `schedule`, `GET .../stats`, `POST .../retry-failed` |

## Email engine

- One row per job; statuses `pending` / `sent` / `failed`; retries with backoff; global **per sender** rate limit via Redis.
- **Pause / resume** via campaign status; **schedule** via `scheduled_at` and worker promotion to `running`.

## Optional: local development (no Docker)

See `backend/.env.example` and `frontend/.env.local.example` for running API, worker, and `npm run dev` on your machine.

## License

Internal use — adapt as needed.
