# Railway Deployment Guide

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be on GitHub (already done)

## Step 1: Create New Project on Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository: `Dev-Chisom/crispy-palm-tree`

## Step 2: Add Services

You'll need 3 services:

### Service 1: PostgreSQL Database
1. Click "+ New" → "Database" → "Add PostgreSQL"
2. Railway will automatically create a PostgreSQL database
3. Note the connection details (will be in environment variables)

### Service 2: Redis
1. Click "+ New" → "Database" → "Add Redis"
2. Railway will create a Redis instance
3. Note the connection URL

### Service 3: Web Service (FastAPI)
1. Your main service should already be created from GitHub
2. This will run your FastAPI application

### Service 4: Celery Worker (Optional but Recommended)
1. Click "+ New" → "Empty Service"
2. Connect to the same GitHub repo
3. This will run your Celery worker

## Step 3: Configure Environment Variables

Go to your **Web Service** → **Variables** tab and add:

### Database
```
DATABASE_URL=<from PostgreSQL service>
```
Get this from: PostgreSQL service → Variables → `DATABASE_URL`

### Redis
```
REDIS_URL=<from Redis service>
```
Get this from: Redis service → Variables → `REDIS_URL`

### Celery
```
CELERY_BROKER_URL=<from Redis service>
CELERY_RESULT_BACKEND=<from Redis service>
```
Use the same Redis URL for both (Railway Redis provides a single URL)

### API Settings
```
API_V1_PREFIX=/api/v1
CORS_ORIGINS=https://your-frontend-domain.com,http://localhost:3000
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

### Data Sources
```
YFINANCE_ENABLED=true
NGX_API_ENABLED=false
TIMESCALEDB_ENABLED=true
```

### OpenAI (Optional)
```
OPENAI_API_KEY=your_openai_key_here
```

### Security
```
API_KEY_SECRET=generate_a_random_secret_key
```

## Step 4: Configure Celery Worker Service

For the **Celery Worker** service:

1. Go to **Settings** → **Start Command**
2. Set to: `celery -A app.tasks.celery_app worker --loglevel=info`
3. Add the same environment variables as the web service

## Step 5: Run Database Migrations

After deployment, you need to run migrations:

### Option 1: Railway CLI
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Run migrations
railway run alembic upgrade head

# Initialize TimescaleDB
railway run python scripts/init_timescaledb.py
```

### Option 2: One-off Service
1. Create a temporary service
2. Set start command: `alembic upgrade head && python scripts/init_timescaledb.py`
3. Deploy, wait for completion, then delete

## Step 6: Configure Port

Railway automatically sets `$PORT` environment variable. Your `Procfile` should use it:
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Step 7: Deploy

1. Railway will automatically deploy on every push to `main` branch
2. Or click "Deploy" button manually
3. Check logs for any errors

## Step 8: Get Your Domain

1. Go to your Web Service → **Settings** → **Generate Domain**
2. Railway will provide a URL like: `your-app.up.railway.app`
3. Update `CORS_ORIGINS` with your frontend domain

## Environment Variables Summary

Copy these to Railway Variables:

```env
# Database (from PostgreSQL service)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (from Redis service)
REDIS_URL=${{Redis.REDIS_URL}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}

# API
API_V1_PREFIX=/api/v1
CORS_ORIGINS=https://your-frontend.vercel.app
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Data Sources
YFINANCE_ENABLED=true
NGX_API_ENABLED=false
TIMESCALEDB_ENABLED=true

# Security
API_KEY_SECRET=your-secret-key-here

# OpenAI (optional)
OPENAI_API_KEY=sk-...
```

## Post-Deployment Checklist

- [ ] Database migrations run successfully
- [ ] TimescaleDB extension enabled
- [ ] Redis connected
- [ ] Celery worker running
- [ ] API accessible at Railway domain
- [ ] CORS configured for frontend
- [ ] Environment variables set
- [ ] Health check endpoint working: `/health`

## Troubleshooting

### Database Connection Issues
- Check `DATABASE_URL` is correct
- Ensure PostgreSQL service is running
- Verify migrations have run

### Redis Connection Issues
- Check `REDIS_URL` is correct
- Ensure Redis service is running
- Verify Celery worker can connect

### Celery Not Working
- Check worker service is running
- Verify `CELERY_BROKER_URL` matches Redis URL
- Check worker logs for errors

### Port Issues
- Ensure using `$PORT` environment variable
- Railway sets this automatically

## Cost Considerations

Railway pricing:
- **Hobby Plan**: $5/month + usage
- **Pro Plan**: $20/month + usage
- PostgreSQL: Included
- Redis: Included
- Bandwidth: Pay as you go

## Monitoring

- Check service logs in Railway dashboard
- Monitor resource usage
- Set up alerts for service failures
