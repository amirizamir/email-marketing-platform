# Internal Email Marketing Platform

**FastAPI** + **PostgreSQL** + **Redis** + **Alembic** + **email worker** + **Next.js (App Router)** with **Nginx** as a single Docker deployment (no local installs required for production use).

## Deploy with Docker (recommended)

### Linux cloud VM (VPS, EC2, etc.)

On the server (Ubuntu/Debian-style):

```bash
sudo apt update && sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker "$USER"   # log out/in to apply
git clone <your-repo-url> && cd email-marketing-platform
cp deploy.env.example .env
nano .env   # set SECRET_KEY, ENCRYPTION_KEY, POSTGRES_PASSWORD, HTTP_PORT
docker compose up -d --build
```

**Firewall:** allow inbound TCP on **`HTTP_PORT`** (default `8080`). Example with UFW:

```bash
sudo ufw allow ${HTTP_PORT:-8080}/tcp
sudo ufw enable
```

Then open **`http://YOUR_PUBLIC_IP:8080`** (or port `80` if you set `HTTP_PORT=80`).

The Compose file uses project name **`email-marketing`**, a dedicated network **`email_marketing_net`**, **Redis AOF persistence**, **log rotation** for containers, and a **single backend image** for both `api` and `worker` (faster builds). Only **nginx** publishes a host port; Postgres and Redis stay on the internal Docker network.

### Any machine (same steps)

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

   - **UI + API (same origin):** `http://<host>:8080`  
   - **OpenAPI:** `http://<host>:8080/docs`  
   - **API health:** `http://<host>:8080/health`  

Nginx routes `/` to the Next.js app and `/api/...` to FastAPI, so the browser does **not** need `NEXT_PUBLIC_API_URL` (leave it empty in `.env`).

Services: **Postgres** (data), **Redis** (queue + rate keys + persistence volume), **api** (migrations on boot), **worker** (same image as api — sends mail), **web** (Next.js), **nginx** (entry point).

### Web image build: npm `ETIMEDOUT` (registry.npmjs.org)

The frontend `Dockerfile` uses **BuildKit**, an npm **cache mount**, **`RUN --network=host`** on the deps step (Linux: uses the host network; fixes many registry timeouts), and **`frontend/docker-install-deps.sh`**, which retries in order:

1. `NPM_REGISTRY` from `.env` (if set)  
2. `https://registry.npmjs.org`  
3. `https://registry.npmmirror.com`

On older daemons: `export DOCKER_BUILDKIT=1`.

**Still timing out?** Set a mirror in `.env` and rebuild the web image only:

```env
NPM_REGISTRY=https://registry.npmmirror.com
```

```bash
docker compose build web --no-cache
```

**Lockfile (fewer requests):**

```bash
chmod +x scripts/gen-frontend-lockfile.sh
./scripts/gen-frontend-lockfile.sh
git add frontend/package-lock.json && git commit -m "Add npm lockfile for Docker"
```

**Linux:** uncomment `network: host` under `web.build` in `docker-compose.yml` if you need the whole build to use host networking.

**Proxy:** set `HTTP_PROXY` / `HTTPS_PROXY` on the host before `docker compose build`, or add them as build args in `frontend/Dockerfile`.

**Docker Desktop (Windows/Mac):** `RUN --network=host` is only fully supported on **Linux** builders; build the `web` image on the Linux server, or use WSL2.

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
