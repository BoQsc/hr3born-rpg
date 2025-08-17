#!/usr/bin/env python3
"""
Test database initialization
"""
import asyncio
from database import init_database, get_db

async def test_db():
    print("Testing database initialization...")
    try:
        await init_database()
        print("Database init successful!")
        
        database = await get_db()
        print("Database connection successful!")
        
        async with database.get_connection_context() as conn:
            print("Connection context successful!")
            
            # Test a simple query
            result = await database.queries.get_all_classes(conn)
            print(f"Classes query successful! Found {len(result)} classes")
            
            # Test the new ranking queries
            rankings = await database.queries.get_power_rankings(conn, limit=10)
            print(f"Power rankings query successful! Found {len(rankings)} characters")
            
    except Exception as e:
        print(f"Database error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_db())