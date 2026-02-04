#!/usr/bin/env python3
"""Diagnostic script to check local setup."""

import sys
import os

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"❌ Python version too old: {version.major}.{version.minor}")
        print("   Required: Python 3.9+")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def check_env_file():
    """Check if .env file exists."""
    if not os.path.exists(".env"):
        print("❌ .env file not found")
        print("   Create .env file with required variables")
        return False
    print("✅ .env file exists")
    return True

def check_imports():
    """Check if main imports work."""
    try:
        from app.main import app
        print("✅ App imports successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error importing app: {e}")
        return False

def check_config():
    """Check if config loads correctly."""
    try:
        from app.config import settings
        print("✅ Config loaded")
        
        if not settings.database_url:
            print("⚠️  DATABASE_URL not set")
        else:
            print(f"   Database URL: {settings.database_url[:40]}...")
        
        if not settings.redis_url:
            print("⚠️  REDIS_URL not set")
        else:
            print(f"   Redis URL: {settings.redis_url[:40]}...")
        
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def check_database():
    """Check database connection."""
    try:
        from app.config import settings
        from sqlalchemy import create_engine, text
        
        if not settings.database_url:
            print("⚠️  Database: URL not set (skipping connection test)")
            return True
        
        engine = create_engine(settings.database_url, connect_args={"connect_timeout": 5})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection: OK")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   Make sure PostgreSQL is running:")
        print("   - Docker: docker-compose up -d postgres")
        print("   - Or start PostgreSQL service manually")
        return False

def check_redis():
    """Check Redis connection."""
    try:
        from app.config import settings
        import redis
        
        if not settings.redis_url:
            print("⚠️  Redis: URL not set (skipping connection test)")
            return True
        
        r = redis.from_url(settings.redis_url, socket_connect_timeout=5)
        r.ping()
        print("✅ Redis connection: OK")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("   Make sure Redis is running:")
        print("   - Docker: docker-compose up -d redis")
        print("   - Or start Redis service manually: redis-server")
        return False

def check_dependencies():
    """Check if key dependencies are installed."""
    required = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "celery",
        "redis",
        "pandas",
        "yfinance",
    ]
    
    missing = []
    for dep in required:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    print("✅ All required dependencies installed")
    return True

def main():
    """Run all checks."""
    print("🔍 LOCAL SETUP DIAGNOSTICS")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        (".env File", check_env_file),
        ("Dependencies", check_dependencies),
        ("App Imports", check_imports),
        ("Config", check_config),
        ("Database", check_database),
        ("Redis", check_redis),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"Checking {name}...")
        result = check_func()
        results.append((name, result))
        print()
    
    print("=" * 60)
    print("SUMMARY:")
    print()
    
    all_ok = True
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
        if not result:
            all_ok = False
    
    print()
    if all_ok:
        print("✅ All checks passed! You can start the server with:")
        print("   python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    else:
        print("❌ Some checks failed. Fix the issues above before starting the server.")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
