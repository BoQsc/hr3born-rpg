import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from redis_client import RedisManager

class UserService:
    def __init__(self, db_pool, queries, redis_client):
        self.db = db_pool
        self.queries = queries
        self.redis = RedisManager(redis_client)
    
    async def create_user(self, username: str, email: str, password_hash: str, 
                         points: int = 0, character_slots: int = 25) -> str:
        """Create a new user"""
        async with self.db.acquire() as conn:
            result = await self.queries.create_user(
                conn, username, email, password_hash, points, character_slots
            )
            return str(result['id'])
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        async with self.db.acquire() as conn:
            result = await self.queries.get_user_by_username(conn, username)
            return dict(result) if result else None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        async with self.db.acquire() as conn:
            result = await self.queries.get_user_by_email(conn, email)
            return dict(result) if result else None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        async with self.db.acquire() as conn:
            result = await self.queries.get_user_by_id(conn, user_id)
            return dict(result) if result else None
    
    async def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp"""
        async with self.db.acquire() as conn:
            await self.queries.update_last_login(conn, user_id)
            return True
    
    async def update_user_points(self, user_id: str, points_change: int) -> bool:
        """Update user's points"""
        async with self.db.acquire() as conn:
            await self.queries.update_user_points(conn, user_id, points_change)
            return True
    
    async def get_user_characters(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all characters for a user"""
        async with self.db.acquire() as conn:
            results = await self.queries.get_user_characters(conn, user_id)
            return [dict(row) for row in results]
    
    async def create_session(self, user_id: str, token: str, expire_days: int = 7):
        """Create user session"""
        expire_seconds = expire_days * 24 * 3600
        session_data = {
            'user_id': user_id,
            'token': token,
            'created_at': datetime.now().isoformat()
        }
        await self.redis.set_session(user_id, session_data, expire_seconds)
    
    async def get_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user session"""
        return await self.redis.get_session(user_id)
    
    async def delete_session(self, user_id: str):
        """Delete user session"""
        await self.redis.delete_session(user_id)