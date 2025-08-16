import redis.asyncio as aioredis
import json
from typing import Any, Optional

async def init_redis(app):
    """Initialize Redis connection"""
    config = app['config']
    app['redis'] = await aioredis.from_url(
        config.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )

async def close_redis(app):
    """Close Redis connection"""
    if 'redis' in app:
        await app['redis'].close()

class RedisManager:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def set_session(self, user_id: str, session_data: dict, expire_seconds: int = 86400):
        """Store user session data"""
        key = f"session:{user_id}"
        await self.redis.setex(key, expire_seconds, json.dumps(session_data))
    
    async def get_session(self, user_id: str) -> Optional[dict]:
        """Get user session data"""
        key = f"session:{user_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def delete_session(self, user_id: str):
        """Delete user session"""
        key = f"session:{user_id}"
        await self.redis.delete(key)
    
    async def set_character_online(self, character_id: str, room_id: str = None):
        """Mark character as online"""
        key = f"online:{character_id}"
        data = {"last_seen": "now", "room_id": room_id}
        await self.redis.setex(key, 300, json.dumps(data))  # 5 minute expiry
    
    async def is_character_online(self, character_id: str) -> bool:
        """Check if character is online"""
        key = f"online:{character_id}"
        return await self.redis.exists(key)
    
    async def set_combat_state(self, character_id: str, combat_data: dict):
        """Store active combat state"""
        key = f"combat:{character_id}"
        await self.redis.setex(key, 300, json.dumps(combat_data))  # 5 minute expiry
    
    async def get_combat_state(self, character_id: str) -> Optional[dict]:
        """Get active combat state"""
        key = f"combat:{character_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def delete_combat_state(self, character_id: str):
        """Remove combat state"""
        key = f"combat:{character_id}"
        await self.redis.delete(key)
    
    async def cache_character_stats(self, character_id: str, stats: dict, expire_seconds: int = 3600):
        """Cache character stats for quick access"""
        key = f"stats:{character_id}"
        await self.redis.setex(key, expire_seconds, json.dumps(stats))
    
    async def get_cached_character_stats(self, character_id: str) -> Optional[dict]:
        """Get cached character stats"""
        key = f"stats:{character_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def invalidate_character_cache(self, character_id: str):
        """Invalidate all cached data for a character"""
        patterns = [
            f"stats:{character_id}",
            f"combat:{character_id}",
            f"online:{character_id}"
        ]
        for pattern in patterns:
            await self.redis.delete(pattern)
    
    async def set_room_players(self, room_id: str, character_ids: list):
        """Set list of players in a room"""
        key = f"room:{room_id}:players"
        await self.redis.setex(key, 300, json.dumps(character_ids))
    
    async def get_room_players(self, room_id: str) -> list:
        """Get list of players in a room"""
        key = f"room:{room_id}:players"
        data = await self.redis.get(key)
        return json.loads(data) if data else []
    
    async def add_player_to_room(self, room_id: str, character_id: str):
        """Add player to room"""
        players = await self.get_room_players(room_id)
        if character_id not in players:
            players.append(character_id)
            await self.set_room_players(room_id, players)
    
    async def remove_player_from_room(self, room_id: str, character_id: str):
        """Remove player from room"""
        players = await self.get_room_players(room_id)
        if character_id in players:
            players.remove(character_id)
            await self.set_room_players(room_id, players)
    
    async def set_resource_generation_lock(self, character_id: str, lock_time: int = 3600):
        """Set lock to prevent duplicate resource generation"""
        key = f"resource_lock:{character_id}"
        return await self.redis.set(key, "locked", ex=lock_time, nx=True)
    
    async def release_resource_generation_lock(self, character_id: str):
        """Release resource generation lock"""
        key = f"resource_lock:{character_id}"
        await self.redis.delete(key)
    
    async def set_daily_transfer_count(self, item_id: str, count: int):
        """Set daily transfer count for an item"""
        key = f"transfers:{item_id}:today"
        # Set with expiry at midnight
        import datetime
        now = datetime.datetime.now()
        midnight = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time.min)
        seconds_until_midnight = int((midnight - now).total_seconds())
        await self.redis.setex(key, seconds_until_midnight, str(count))
    
    async def get_daily_transfer_count(self, item_id: str) -> int:
        """Get daily transfer count for an item"""
        key = f"transfers:{item_id}:today"
        count = await self.redis.get(key)
        return int(count) if count else 0
    
    async def increment_daily_transfer_count(self, item_id: str) -> int:
        """Increment daily transfer count for an item"""
        key = f"transfers:{item_id}:today"
        count = await self.redis.incr(key)
        if count == 1:  # First increment, set expiry
            import datetime
            now = datetime.datetime.now()
            midnight = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time.min)
            seconds_until_midnight = int((midnight - now).total_seconds())
            await self.redis.expire(key, seconds_until_midnight)
        return count