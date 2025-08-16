import uuid
import random
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from models.combat import CombatStats, CombatResult, CombatEngine, NPC, DamageType
from models.character import Character
from redis_client import RedisManager

class CombatService:
    def __init__(self, db_pool, queries, redis_client):
        self.db = db_pool
        self.queries = queries
        self.redis = RedisManager(redis_client)
    
    async def initiate_pvp_combat(self, attacker_id: str, defender_id: str) -> Tuple[bool, str, Optional[CombatResult]]:
        """Initiate PvP combat between two characters"""
        # Get both characters
        attacker = await self._get_character_combat_stats(attacker_id)
        defender = await self._get_character_combat_stats(defender_id)
        
        if not attacker or not defender:
            return False, "Character not found", None
        
        # Check if both characters are alive
        if not attacker['stats'].is_alive():
            return False, "Attacker is dead", None
        
        if not defender['stats'].is_alive():
            return False, "Defender is dead", None
        
        # Check if either character is already in combat
        if await self.redis.get_combat_state(attacker_id):
            return False, "Attacker is already in combat", None
        
        if await self.redis.get_combat_state(defender_id):
            return False, "Defender is already in combat", None
        
        # Store combat state in Redis
        combat_data = {
            'type': 'pvp',
            'attacker_id': attacker_id,
            'defender_id': defender_id,
            'started_at': datetime.now().isoformat()
        }
        
        await self.redis.set_combat_state(attacker_id, combat_data)
        await self.redis.set_combat_state(defender_id, combat_data)
        
        try:
            # Simulate combat
            result = CombatEngine.simulate_combat(
                attacker['stats'], attacker['name'], attacker_id,
                defender['stats'], defender['name'], defender_id
            )
            
            # Save combat log to database
            combat_log_id = await self._save_combat_log(
                attacker_id, defender_id, None, 'pvp', result
            )
            
            # Apply combat results
            await self._apply_combat_results(result, attacker_id, defender_id)
            
            return True, "Combat completed", result
            
        finally:
            # Clean up combat state
            await self.redis.delete_combat_state(attacker_id)
            await self.redis.delete_combat_state(defender_id)
    
    async def initiate_pve_combat(self, character_id: str, npc_id: str) -> Tuple[bool, str, Optional[CombatResult]]:
        """Initiate PvE combat between character and NPC"""
        # Get character and NPC
        character = await self._get_character_combat_stats(character_id)
        npc = await self.get_npc(npc_id)
        
        if not character:
            return False, "Character not found", None
        
        if not npc:
            return False, "NPC not found", None
        
        if not character['stats'].is_alive():
            return False, "Character is dead", None
        
        if not npc.is_available():
            return False, "NPC is not available (recently killed)", None
        
        # Check if character is already in combat
        if await self.redis.get_combat_state(character_id):
            return False, "Character is already in combat", None
        
        # Store combat state
        combat_data = {
            'type': 'pve',
            'character_id': character_id,
            'npc_id': npc_id,
            'started_at': datetime.now().isoformat()
        }
        
        await self.redis.set_combat_state(character_id, combat_data)
        
        try:
            # Simulate combat
            result = CombatEngine.simulate_combat(
                character['stats'], character['name'], character_id,
                npc.stats, npc.name, npc_id
            )
            
            # If NPC was defeated, mark it as killed and add loot
            if result.winner_id == character_id:
                await self._kill_npc(npc_id)
                result.exp_gained = npc.exp_reward
                result.gold_gained = npc.gold_reward
                result.items_gained = await self._generate_loot(npc.loot_table)
            
            # Save combat log
            combat_log_id = await self._save_combat_log(
                character_id, None, npc_id, 'pve', result
            )
            
            # Apply results to character
            await self._apply_pve_results(result, character_id)
            
            return True, "Combat completed", result
            
        finally:
            await self.redis.delete_combat_state(character_id)
    
    async def get_npc(self, npc_id: str) -> Optional[NPC]:
        """Get NPC by ID"""
        async with self.db.acquire() as conn:
            result = await self.queries.get_npc_by_id(conn, npc_id)
            if result:
                return self._db_result_to_npc(result)
        return None
    
    async def get_npcs_in_room(self, room_id: str, include_dead: bool = False) -> List[NPC]:
        """Get all NPCs in a room"""
        async with self.db.acquire() as conn:
            if include_dead:
                results = await self.queries.get_all_npcs_in_room(conn, room_id)
            else:
                results = await self.queries.get_npcs_in_room(conn, room_id)
            
            return [self._db_result_to_npc(row) for row in results]
    
    async def create_npc(self, npc_data: Dict[str, Any]) -> str:
        """Create a new NPC"""
        async with self.db.acquire() as conn:
            result = await self.queries.create_npc(
                conn,
                npc_data['name'], npc_data['npc_type'], npc_data['level'],
                npc_data['room_id'], npc_data['attack'], npc_data['hit_points'],
                npc_data['hit_points'], npc_data.get('chaos_damage', 0),
                npc_data.get('vile_damage', 0), npc_data.get('elemental_attack', 0),
                npc_data.get('fire_resist', 0), npc_data.get('kinetic_resist', 0),
                npc_data.get('arcane_resist', 0), npc_data.get('holy_resist', 0),
                npc_data.get('shadow_resist', 0), npc_data.get('elemental_resist', 0),
                npc_data.get('gold_reward', 0), npc_data.get('exp_reward', 0),
                npc_data.get('loot_table', []), npc_data.get('respawn_time', 3600),
                npc_data.get('is_boss', False), npc_data.get('is_raid_boss', False),
                npc_data.get('faction_requirement'), npc_data.get('description', '')
            )
            return str(result['id'])
    
    async def get_combat_history(self, character_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get combat history for a character"""
        async with self.db.acquire() as conn:
            results = await self.queries.get_character_combat_history(conn, character_id, limit)
            return [dict(row) for row in results]
    
    async def get_recent_pvp_battles(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent PvP battles"""
        async with self.db.acquire() as conn:
            results = await self.queries.get_recent_pvp_battles(conn, limit)
            return [dict(row) for row in results]
    
    async def _get_character_combat_stats(self, character_id: str) -> Optional[Dict[str, Any]]:
        """Get character's combat stats"""
        # This would use character service to get full character data
        # For now, simplified implementation
        async with self.db.acquire() as conn:
            result = await self.queries.get_character_by_id(conn, character_id)
            if result:
                stats = CombatStats(
                    level=result['level'],
                    attack=result['attack'],
                    hit_points=result['hit_points'],
                    current_hp=result['current_hp'],
                    chaos_damage=result['chaos_damage'],
                    vile_damage=result['vile_damage'],
                    elemental_attack=result['elemental_attack'],
                    fire_resist=result['fire_resist'],
                    kinetic_resist=result['kinetic_resist'],
                    arcane_resist=result['arcane_resist'],
                    holy_resist=result['holy_resist'],
                    shadow_resist=result['shadow_resist'],
                    elemental_resist=result['elemental_resist'],
                    critical_hit_chance=float(result['critical_hit_chance']),
                    rampage_bonus=result['rampage_bonus']
                )
                
                return {
                    'id': str(result['id']),
                    'name': result['name'],
                    'stats': stats
                }
        
        return None
    
    async def _save_combat_log(self, attacker_id: Optional[str], defender_id: Optional[str], 
                              npc_id: Optional[str], combat_type: str, result: CombatResult) -> str:
        """Save combat log to database"""
        async with self.db.acquire() as conn:
            log_result = await self.queries.create_combat_log(
                conn,
                attacker_id, defender_id, npc_id, combat_type, result.winner_id,
                [action.to_dict() for action in result.combat_log],
                result.total_damage_dealt, result.total_damage_received,
                result.duration_seconds, result.exp_gained, result.gold_gained,
                result.items_gained, datetime.now(), datetime.now()
            )
            return str(log_result['id'])
    
    async def _apply_combat_results(self, result: CombatResult, attacker_id: str, defender_id: str):
        """Apply combat results to both characters"""
        # Update HP for both characters
        # Winner gets rewards, loser takes damage
        
        # This would integrate with character service to update stats
        # For now, just invalidate caches
        await self.redis.invalidate_character_cache(attacker_id)
        await self.redis.invalidate_character_cache(defender_id)
    
    async def _apply_pve_results(self, result: CombatResult, character_id: str):
        """Apply PvE combat results to character"""
        # Update character HP, give experience and gold
        # This would integrate with character service
        await self.redis.invalidate_character_cache(character_id)
    
    async def _kill_npc(self, npc_id: str):
        """Mark NPC as killed"""
        async with self.db.acquire() as conn:
            await self.queries.kill_npc(conn, npc_id)
    
    async def _generate_loot(self, loot_table: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate loot from loot table"""
        loot = []
        
        for loot_entry in loot_table:
            chance = loot_entry.get('chance', 0.1)  # 10% default chance
            if random.random() < chance:
                loot.append({
                    'item_template_id': loot_entry['item_template_id'],
                    'quantity': loot_entry.get('quantity', 1)
                })
        
        return loot
    
    def _db_result_to_npc(self, result: Dict[str, Any]) -> NPC:
        """Convert database result to NPC object"""
        stats = CombatStats(
            level=result['level'],
            attack=result['attack'],
            hit_points=result['hit_points'],
            current_hp=result['max_hp'],  # NPCs start at full HP
            chaos_damage=result['chaos_damage'],
            vile_damage=result['vile_damage'],
            elemental_attack=result['elemental_attack'],
            fire_resist=result['fire_resist'],
            kinetic_resist=result['kinetic_resist'],
            arcane_resist=result['arcane_resist'],
            holy_resist=result['holy_resist'],
            shadow_resist=result['shadow_resist'],
            elemental_resist=result['elemental_resist'],
            critical_hit_chance=0.0,  # NPCs have no crit by default
            rampage_bonus=0
        )
        
        return NPC(
            id=str(result['id']),
            name=result['name'],
            npc_type=result['npc_type'],
            level=result['level'],
            room_id=str(result['room_id']),
            stats=stats,
            gold_reward=result['gold_reward'],
            exp_reward=result['exp_reward'],
            loot_table=result.get('loot_table', []),
            respawn_time=result['respawn_time'],
            last_killed=result['last_killed'],
            is_boss=result['is_boss'],
            is_raid_boss=result['is_raid_boss'],
            faction_requirement=result['faction_requirement'],
            description=result['description']
        )