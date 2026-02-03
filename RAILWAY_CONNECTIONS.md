# Connecting Services in Railway

## Current Status

You have 3 services:
- ✅ **Redis** - Online
- ✅ **Postgres-H2e5** - Online  
- 🔄 **crispy-palm-tree** - Deploying

## How to Connect Services

### Step 1: Access Service Variables

1. Click on **crispy-palm-tree** service
2. Go to **Variables** tab
3. You'll see Railway's variable reference system

### Step 2: Connect to PostgreSQL

Add this variable to **crispy-palm-tree**:

```
DATABASE_URL=${{Postgres-H2e5.DATABASE_URL}}
```

**How to add:**
1. Click "+ New Variable"
2. Name: `DATABASE_URL`
3. Value: `${{Postgres-H2e5.DATABASE_URL}}`
4. Railway will auto-populate the actual connection string

### Step 3: Connect to Redis

Add these variables to **crispy-palm-tree**:

```
REDIS_URL=${{Redis.REDIS_URL}}
CELERY_BROKER_URL=${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND=${{Redis.REDIS_URL}}
```

**How to add:**
1. Click "+ New Variable" for each
2. Use the `${{ServiceName.VARIABLE}}` syntax
3. Railway will auto-connect the services

### Step 4: Add Other Required Variables

Also add these (not service references):

```
API_V1_PREFIX=/api/v1
CORS_ORIGINS=https://your-frontend-domain.com,http://localhost:3000
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
YFINANCE_ENABLED=true
NGX_API_ENABLED=false
TIMESCALEDB_ENABLED=true
OPENAI_API_KEY=your_key_here
API_KEY_SECRET=generate_random_secret
```

## Visual Connection

After adding variables with `${{ServiceName.VARIABLE}}` syntax:
- Railway will show **connection lines** in Architecture view
- Services will appear connected
- Variables will be automatically synced

## Verify Connections

1. **Check Architecture View:**
   - You should see lines connecting services
   - Services should show as connected

2. **Check Variables:**
   - Go to crispy-palm-tree → Variables
   - Verify `DATABASE_URL` and `REDIS_URL` are populated
   - They should show actual connection strings (not `${{...}}`)

3. **Check Logs:**
   - After deployment, check logs
   - Should see successful database/Redis connections
   - No connection errors

## Troubleshooting

**Services not connecting?**
- Make sure you use exact service name: `Postgres-H2e5` (case-sensitive)
- Check service names in Architecture view
- Variables must use `${{ServiceName.VARIABLE}}` syntax

**Variables not populating?**
- Wait a few seconds after adding
- Refresh the Variables page
- Check that service names match exactly

**Connection errors?**
- Verify services are "Online"
- Check variable names are correct
- Ensure PostgreSQL and Redis are running
