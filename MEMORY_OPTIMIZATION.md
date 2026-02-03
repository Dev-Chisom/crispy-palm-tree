# Memory Optimization Guide

## Current Memory-Efficient Configuration

### ✅ Optimizations Applied

1. **Database Connection Pool**
   - `pool_size=5` (reduced from 10)
   - `max_overflow=10` (reduced from 20)
   - `pool_recycle=3600` (prevents connection leaks)
   - **Memory saved**: ~50% reduction in connection pool memory

2. **Celery Worker**
   - `concurrency=2` (limits parallel tasks)
   - `max-tasks-per-child=50` (restarts worker to prevent memory leaks)
   - `worker_prefetch_multiplier=4` (limits prefetched tasks)
   - `result_expires=3600` (auto-cleans results)
   - **Memory saved**: Prevents memory accumulation from long-running workers

3. **Uvicorn Server**
   - `--workers 1` (single worker for Railway)
   - `--limit-concurrency 100` (limits concurrent requests)
   - **Memory saved**: Single process instead of multiple workers

4. **Removed Heavy Dependencies**
   - TensorFlow removed (saves ~500MB+)
   - pandas-ta removed (optional)
   - ta-lib removed (optional)

### 📊 Estimated Memory Usage

**Web Service (FastAPI):**
- Base: ~100-150 MB
- Dependencies: ~200-300 MB
- **Total: ~300-450 MB**

**Celery Worker:**
- Base: ~100-150 MB
- Dependencies: ~200-300 MB
- **Total: ~300-450 MB**

**Total Runtime: ~600-900 MB** (well within Railway's limits)

### 🔧 Railway Resource Limits

Railway Hobby Plan:
- **512 MB RAM** per service (default)
- Can upgrade to 1GB, 2GB, 4GB if needed

Our setup uses **~300-450 MB per service**, which fits comfortably.

### 💡 Additional Optimizations (If Needed)

1. **Reduce pandas DataFrames**
   - Process data in chunks
   - Delete large DataFrames after use

2. **Limit Cache Size**
   - Redis already has TTLs configured
   - Consider maxmemory policy if needed

3. **Database Query Optimization**
   - Use `.limit()` on all queries
   - Avoid loading entire tables

4. **Celery Task Optimization**
   - Process one stock at a time
   - Clear DataFrames after processing

### 🚨 Memory Monitoring

Monitor memory usage in Railway:
- Go to service → Metrics → Memory
- Set up alerts if memory > 80%

### 📝 Configuration Files

All optimizations are in:
- `app/database.py` - Connection pool settings
- `app/tasks/celery_app.py` - Celery worker settings
- `Procfile` - Process limits
