#!/usr/bin/env python3
"""
Test database and Redis connections
"""
import asyncio
import asyncpg
import redis.asyncio as aioredis
from config import Config

async def test_database():
    """Test PostgreSQL connection"""
    try:
        conn = await asyncpg.connect(Config.DATABASE_URL)
        result = await conn.fetchval("SELECT version()")
        await conn.close()
        print("[OK] Database connection successful!")
        print(f"   PostgreSQL version: {result}")
        return True
    except Exception as e:
        print("[ERROR] Database connection failed!")
        print(f"   Error: {e}")
        print(f"   URL: {Config.DATABASE_URL}")
        return False

async def test_redis():
    """Test Redis connection"""
    try:
        redis = await aioredis.from_url(Config.REDIS_URL)
        await redis.ping()
        await redis.close()
        print("[OK] Redis connection successful!")
        return True
    except Exception as e:
        print("[ERROR] Redis connection failed!")
        print(f"   Error: {e}")
        print(f"   URL: {Config.REDIS_URL}")
        return False

async def main():
    print("Testing Outwar RPG Database Connections...")
    print()
    
    db_ok = await test_database()
    redis_ok = await test_redis()
    
    print()
    if db_ok and redis_ok:
        print("All connections successful! You can now run the game.")
        print("   Next steps:")
        print("   1. python setup_game.py  (initialize game data)")
        print("   2. python main.py         (start the server)")
    else:
        print("Please fix the connection issues above before proceeding.")

if __name__ == '__main__':
    asyncio.run(main())