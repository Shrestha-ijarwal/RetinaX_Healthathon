# RetinaX Care — Deployment, Operations & Cloud Guide

**Document Version:** 2.0.0  
**Target Environments:** Local Docker Compose & AWS ECS Fargate  

---

## 1. Quick Start: Local Docker Compose (Recommended)

The complete full-stack platform (PostgreSQL, Redis, MinIO, FastAPI Backend, Celery Worker, Next.js Frontend) can be initialized with a single command:

```bash
# 1. Clone or navigate to the repository
cd C:\Users\sijar\Downloads\RetinaX_Healthathon

# 2. Copy environment template
cp .env.example .env

# 3. Build and launch all containerized services
docker compose build
docker compose up -d

# 4. Verify running health status
docker compose ps
```

### Running Services & Ports
| Service | Container Name | Local Port | Health Check |
|---|---|---|---|
| **Next.js Frontend** | `retinax_frontend` | `http://localhost:3000` | HTTP 200 |
| **FastAPI Backend** | `retinax_backend` | `http://localhost:8000` | `GET /health` |
| **PostgreSQL 16** | `retinax_postgres` | `localhost:5432` | `pg_isready` |
| **Redis 7** | `retinax_redis` | `localhost:6379` | `redis-cli ping` |
| **MinIO S3 Console** | `retinax_minio` | `http://localhost:9001` | `GET /minio/health/live` |
| **Celery Worker** | `retinax_celery_worker` | (Internal) | Celery ping |

---

## 2. Native Local Development Setup (Without Docker)

For rapid iteration without Docker containers:

### 2.1 Backend Setup
```powershell
# In PowerShell:
Set-Location "C:\Users\sijar\Downloads\RetinaX_Healthathon"
$env:PYTHONPATH="C:\Users\sijar\Downloads\RetinaX_Healthathon"

# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Run database migrations
python -m alembic upgrade head

# 3. Seed synthetic demonstration dataset & demo accounts
python backend/app/db/seed.py

# 4. Start the FastAPI development server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend is available at `http://localhost:8000` (OpenAPI docs at `http://localhost:8000/api/v1/docs`).*

### 2.2 Frontend Setup
```powershell
Set-Location "C:\Users\sijar\Downloads\RetinaX_Healthathon\frontend"

# 1. Install npm dependencies
npm.cmd install

# 2. Start Next.js development server
npm.cmd run dev
```
*Frontend is available at `http://localhost:3000`.*

---

## 3. Database Migrations & Seeding Commands

### Apply Alembic Migrations
```bash
python -m alembic upgrade head
```

### Generate a New Migration
```bash
python -m alembic revision --autogenerate -m "describe_schema_change"
```

### Idempotently Seed Synthetic Patient Records & Demo Accounts
```bash
python backend/app/db/seed.py
```
*The seed script verifies existing primary keys and will not create duplicate records if rerun.*

---

## 4. Demonstration Accounts

| Role | Email | Password | Full Name | Capabilities |
|---|---|---|---|---|
| **Specialist** | `specialist@retinax.care` | `Specialist@2026` | Dr. Suresh Chandran, MS | Review queue access, submit tele-ophthalmology reviews, record attributed care directives. |
| **Care Coordinator** | `coordinator@retinax.care` | `Coordinator@2026` | Ananya Sharma | Patient directory, care journeys, follow-up contact attempts, bilingual reminder previews. |
| **Administrator** | `admin@retinax.care` | `Admin@2026` | Rajiv Menon | Audit event inspection, cohort data reset, system configuration. |

---

## 5. AWS ECS Fargate Deployment Blueprint

### Target Cloud Services
- **Compute:** AWS ECS Fargate (Task definitions provided in `infrastructure/aws/`)
- **Database:** Amazon RDS for PostgreSQL (Engine 16.x, Multi-AZ)
- **Message Broker:** Amazon ElastiCache for Redis (Cluster mode)
- **Document Storage:** Private Amazon S3 Bucket with AES-256 server-side encryption
- **Ingress:** Application Load Balancer (ALB) with ACM TLS 1.3 certificate
- **Secrets:** AWS Secrets Manager (`retinax/db-url`, `retinax/secret-key`)
- **Logs:** Amazon CloudWatch (`/ecs/retinax-care-backend`, `/ecs/retinax-care-frontend`)

### Step-by-Step AWS Setup
1. **ECR Image Repositories:**
   ```bash
   aws ecr create-repository --repository-name retinax-backend --region ap-south-1
   aws ecr create-repository --repository-name retinax-frontend --region ap-south-1
   ```
2. **Build and Push Docker Images:**
   ```bash
   docker build -t <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/retinax-backend:latest -f backend/Dockerfile .
   docker push <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/retinax-backend:latest

   docker build -t <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/retinax-frontend:latest -f frontend/Dockerfile .
   docker push <ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/retinax-frontend:latest
   ```
3. **Register ECS Task Definitions:**
   ```bash
   aws ecs register-task-definition --cli-input-json file://infrastructure/aws/task-definition-backend.json
   aws ecs register-task-definition --cli-input-json file://infrastructure/aws/task-definition-frontend.json
   ```
4. **Deploy ECS Services:**
   Create an ECS Service behind an ALB with Target Group health check path `/health`.


---

## 6. Live Hybrid Production Deployment: Vercel Frontend + Hosted Backend

This configuration integrates the live deployed Vercel frontend (`https://retina-x01.vercel.app/`) with the containerized FastAPI backend.

### 6.1 Backend Hosting Options (Render / Railway / Fly.io / GCP Cloud Run / AWS ECS)

#### Deploying with Docker:
- **Build Command / Dockerfile:** `backend/Dockerfile`
- **Port:** `8000`
- **Health Check Endpoint:** `/health`
- **Environment Variables:**
  ```ini
  ENVIRONMENT=production
  SECRET_KEY=<generate_secure_random_64_char_key>
  DATABASE_URL=postgresql://<user>:<password>@<host>:5432/<dbname>?sslmode=require
  CORS_ORIGINS=https://retina-x01.vercel.app
  BACKEND_CORS_ORIGINS=["https://retina-x01.vercel.app"]
  ```

#### Initializing Database on Cloud:
After provisioning your PostgreSQL database (e.g. Supabase, Neon, AWS RDS, or Render PostgreSQL):
```bash
python -m alembic upgrade head
python backend/app/db/seed.py
python scripts/generate_valid_synthetic_pdfs.py
```

### 6.2 Connecting the Vercel Frontend (`https://retina-x01.vercel.app`)

1. Open your **Vercel Dashboard** -> Select `retina-x01` project -> **Settings** -> **Environment Variables**.
2. Add the following variable:
   - **Key:** `NEXT_PUBLIC_API_URL`
   - **Value:** `https://<your-backend-domain>` (e.g., `https://retinax-api.onrender.com` or your ECS ALB domain)
   - **Environments:** Production, Preview, Development.
3. Trigger a redeploy:
   - Go to **Deployments** -> Click **Redeploy** on the latest deployment.
4. **Verification Checklist:**
   - Navigating to `https://retina-x01.vercel.app/` loads real patient statistics from `/api/v1/analytics/overview`.
   - Logging in as `coordinator@retinax.care` or `specialist@retinax.care` stores the session token and enables full patient directory navigation.
   - Clicking **Download PDF** on any of the 12 patient records opens the 18 clinical dossiers seamlessly in a new browser tab with authentic medical content.
