import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from models.character import Character, CharacterCreationRequest, create_starting_character
from redis_client import RedisManager
from config import Config

class CharacterService:
    def __init__(self, db_pool, queries, redis_client):
        self.db = db_pool
        self.queries = queries
        self.redis = RedisManager(redis_client)
    
    async def create_character(self, user_id: str, request: CharacterCreationRequest) -> tuple[bool, str, Optional[Character]]:
        """Create a new character for a user"""
        # Validate request
        is_valid, error_msg = request.validate()
        if not is_valid:
            return False, error_msg, None
        
        async with self.db.acquire() as conn:
            # Check if user exists and has available character slots
            user = await self.queries.get_user_by_id(conn, user_id)
            if not user:
                return False, "User not found", None
            
            # Check character count
            user_characters = await self.queries.get_user_characters(conn, user_id)
            if len(user_characters) >= user['character_slots']:
                return False, f"Maximum characters reached ({user['character_slots']})", None
            
            # Check if character name is unique
            existing = await self.queries.get_character_by_name(conn, request.name)
            if existing:
                return False, "Character name already exists", None
            
            # Create character with starting stats
            character = create_starting_character(user_id, request)
            
            # Get starting room (Training Ground in Diamond City)
            starting_room = await self._get_starting_room(conn)
            
            # Insert into database
            try:
                result = await self.queries.create_character(
                    conn,
                    character.user_id,
                    character.name,
                    character.character_class,
                    character.level,
                    character.experience,
                    character.attack,
                    character.hit_points,
                    character.current_hp,
                    character.max_rage,
                    character.rage_per_hour,
                    character.exp_per_hour,
                    starting_room['id'] if starting_room else None
                )
                
                character.id = str(result['id'])
                character.current_room_id = str(starting_room['id']) if starting_room else None
                
                # Cache character stats
                await self.redis.cache_character_stats(character.id, character.to_dict())
                
                return True, "Character created successfully", character
                
            except Exception as e:
                return False, f"Database error: {str(e)}", None
    
    async def get_character(self, character_id: str) -> Optional[Character]:
        """Get character by ID"""
        # Try cache first
        cached_stats = await self.redis.get_cached_character_stats(character_id)
        if cached_stats:
            return self._dict_to_character(cached_stats)
        
        async with self.db.acquire() as conn:
            result = await self.queries.get_character_stats(conn, character_id)
            if result:
                character = self._db_result_to_character(result)
                # Cache for future requests
                await self.redis.cache_character_stats(character_id, character.to_dict())
                return character
        
        return None
    
    async def get_character_by_name(self, name: str) -> Optional[Character]:
        """Get character by name"""
        async with self.db.acquire() as conn:
            result = await self.queries.get_character_by_name(conn, name)
            if result:
                return self._db_result_to_character(result)
        return None
    
    async def get_user_characters(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all characters for a user"""
        async with self.db.acquire() as conn:
            results = await self.queries.get_user_characters(conn, user_id)
            return [dict(row) for row in results]
    
    async def update_character_location(self, character_id: str, room_id: str, zone: str) -> bool:
        """Update character's current location"""
        async with self.db.acquire() as conn:
            await self.queries.update_character_location(conn, character_id, room_id, zone)
            
        # Invalidate cache
        await self.redis.invalidate_character_cache(character_id)
        return True
    
    async def update_character_resources(self, character_id: str, gold: int, rage: int, current_hp: int) -> bool:
        """Update character's resources"""
        async with self.db.acquire() as conn:
            await self.queries.update_character_resources(conn, character_id, gold, rage, current_hp)
        
        # Invalidate cache
        await self.redis.invalidate_character_cache(character_id)
        return True
    
    async def gain_experience(self, character_id: str, exp_amount: int) -> tuple[bool, bool, int]:
        """Add experience to character and check for level up"""
        character = await self.get_character(character_id)
        if not character:
            return False, False, 0
        
        old_level = character.level
        character.experience += exp_amount
        
        # Check for level up
        leveled_up = False
        while character.can_level_up() and character.level < Config.MAX_LEVEL:
            character.level += 1
            leveled_up = True
            
            # Increase base stats on level up
            character.attack += 2
            character.hit_points += 10
            character.current_hp += 10  # Also heal on level up
        
        async with self.db.acquire() as conn:
            await self.queries.update_character_experience(
                conn, character_id, character.experience, 
                character.experience_yesterday, character.level
            )
            
            if leveled_up:
                await self.queries.update_character_stats(
                    conn, character_id, character.attack, character.hit_points,
                    character.chaos_damage, character.vile_damage, character.elemental_attack,
                    character.elemental_resist, character.fire_resist, character.kinetic_resist,
                    character.arcane_resist, character.holy_resist, character.shadow_resist,
                    character.max_rage, character.rage_per_hour, character.exp_per_hour,
                    character.gold_per_turn, character.critical_hit_chance, character.rampage_bonus
                )
        
        # Invalidate cache
        await self.redis.invalidate_character_cache(character_id)
        
        return True, leveled_up, character.level - old_level
    
    async def join_crew(self, character_id: str, crew_id: str, rank: str = 'member') -> bool:
        """Add character to a crew"""
        async with self.db.acquire() as conn:
            await self.queries.join_crew(conn, character_id, crew_id, rank)
        
        await self.redis.invalidate_character_cache(character_id)
        return True
    
    async def leave_crew(self, character_id: str) -> bool:
        """Remove character from crew"""
        async with self.db.acquire() as conn:
            await self.queries.leave_crew(conn, character_id)
        
        await self.redis.invalidate_character_cache(character_id)
        return True
    
    async def change_faction(self, character_id: str, faction: str) -> tuple[bool, str]:
        """Change character's faction"""
        character = await self.get_character(character_id)
        if not character:
            return False, "Character not found"
        
        if character.level < 91:
            return False, "Must be level 91 or higher to join a faction"
        
        if faction not in Config.FACTIONS and faction is not None:
            return False, "Invalid faction"
        
        if not character.can_change_faction():
            return False, "Can only change faction once per month"
        
        async with self.db.acquire() as conn:
            await self.queries.set_faction(conn, character_id, faction)
        
        await self.redis.invalidate_character_cache(character_id)
        return True, "Faction changed successfully"
    
    async def update_faction_loyalty(self, character_id: str, faction: str, loyalty_change: int) -> bool:
        """Update faction loyalty points"""
        character = await self.get_character(character_id)
        if not character:
            return False
        
        # Update loyalty
        current_loyalty = getattr(character, f"{faction}_loyalty", 0)
        new_loyalty = max(0, min(10, current_loyalty + loyalty_change))
        
        loyalty_dict = {
            'alvar_loyalty': character.alvar_loyalty,
            'delruk_loyalty': character.delruk_loyalty,
            'vordyn_loyalty': character.vordyn_loyalty
        }
        loyalty_dict[f"{faction}_loyalty"] = new_loyalty
        
        async with self.db.acquire() as conn:
            await self.queries.update_faction_loyalty(
                conn, character_id, loyalty_dict['alvar_loyalty'],
                loyalty_dict['delruk_loyalty'], loyalty_dict['vordyn_loyalty']
            )
        
        await self.redis.invalidate_character_cache(character_id)
        return True
    
    async def heal_character(self, character_id: str, heal_amount: int) -> bool:
        """Heal character's HP"""
        async with self.db.acquire() as conn:
            await self.queries.heal_character(conn, character_id, heal_amount)
        
        await self.redis.invalidate_character_cache(character_id)
        return True
    
    async def get_characters_in_room(self, room_id: str) -> List[Dict[str, Any]]:
        """Get all characters currently in a room"""
        async with self.db.acquire() as conn:
            results = await self.queries.get_characters_in_room(conn, room_id)
            return [dict(row) for row in results]
    
    async def get_top_characters(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get top characters by level"""
        async with self.db.acquire() as conn:
            results = await self.queries.get_top_characters_by_level(conn, limit)
            return [dict(row) for row in results]
    
    async def process_resource_generation(self, character_id: str) -> Dict[str, int]:
        """Process hourly resource generation for character"""
        # Check if already processed recently
        if not await self.redis.set_resource_generation_lock(character_id):
            return {'gold': 0, 'rage': 0, 'exp': 0}
        
        try:
            character = await self.get_character(character_id)
            if not character:
                return {'gold': 0, 'rage': 0, 'exp': 0}
            
            # Calculate time since last update
            now = datetime.now()
            time_diff = now - character.last_resource_update
            hours_passed = time_diff.total_seconds() / 3600
            
            if hours_passed < 1:  # Less than an hour, no generation
                return {'gold': 0, 'rage': 0, 'exp': 0}
            
            # Cap at 24 hours of generation
            hours_passed = min(hours_passed, 24)
            
            # Calculate generation
            rage_gained = int(character.rage_per_hour * hours_passed)
            exp_gained = int(character.exp_per_hour * hours_passed)
            gold_gained = int(character.gold_per_turn * hours_passed * 10)  # Assume 10 turns per hour
            
            # Apply generation
            new_rage = min(character.rage + rage_gained, character.max_rage)
            new_gold = character.gold + gold_gained
            
            # Update character
            await self.update_character_resources(character_id, new_gold, new_rage, character.current_hp)
            
            # Give experience
            if exp_gained > 0:
                await self.gain_experience(character_id, exp_gained)
            
            return {
                'gold': gold_gained,
                'rage': rage_gained,
                'exp': exp_gained
            }
            
        finally:
            await self.redis.release_resource_generation_lock(character_id)
    
    async def _get_starting_room(self, conn) -> Optional[Dict[str, Any]]:
        """Get the starting room for new characters"""
        # This would query for the training ground room
        # For now, return None to be implemented when world system is ready
        return None
    
    def _db_result_to_character(self, result: Dict[str, Any]) -> Character:
        """Convert database result to Character object"""
        return Character(
            id=str(result['id']),
            user_id=str(result['user_id']),
            name=result['name'],
            character_class=result['character_class'],
            level=result['level'],
            experience=result['experience'],
            experience_yesterday=result['experience_yesterday'],
            
            attack=result['attack'],
            hit_points=result['hit_points'],
            current_hp=result['current_hp'],
            chaos_damage=result['chaos_damage'],
            vile_damage=result['vile_damage'],
            elemental_attack=result['elemental_attack'],
            elemental_resist=result['elemental_resist'],
            wilderness_level=result['wilderness_level'],
            god_slayer_level=result['god_slayer_level'],
            
            fire_resist=result['fire_resist'],
            kinetic_resist=result['kinetic_resist'],
            arcane_resist=result['arcane_resist'],
            holy_resist=result['holy_resist'],
            shadow_resist=result['shadow_resist'],
            
            gold=result['gold'],
            rage=result['rage'],
            max_rage=result['max_rage'],
            rage_per_hour=result['rage_per_hour'],
            exp_per_hour=result['exp_per_hour'],
            gold_per_turn=result['gold_per_turn'],
            
            critical_hit_chance=float(result['critical_hit_chance']),
            rampage_bonus=result['rampage_bonus'],
            
            parent_id=str(result['parent_id']) if result['parent_id'] else None,
            faction=result['faction'],
            crew_id=str(result['crew_id']) if result['crew_id'] else None,
            crew_rank=result['crew_rank'],
            
            alvar_loyalty=result['alvar_loyalty'],
            delruk_loyalty=result['delruk_loyalty'],
            vordyn_loyalty=result['vordyn_loyalty'],
            
            current_room_id=str(result['current_room_id']) if result['current_room_id'] else None,
            current_zone=result['current_zone'],
            
            created_at=result['created_at'],
            last_active=result['last_active'],
            last_resource_update=result['last_resource_update'],
            faction_change_last_used=result['faction_change_last_used']
        )
    
    def _dict_to_character(self, data: Dict[str, Any]) -> Character:
        """Convert dictionary to Character object (from cache)"""
        return Character(
            id=data['id'],
            user_id=data.get('user_id', ''),
            name=data['name'],
            character_class=data['character_class'],
            level=data['level'],
            experience=data['experience'],
            experience_yesterday=data['experience_yesterday'],
            
            attack=data['combat_stats']['attack'],
            hit_points=data['combat_stats']['hit_points'],
            current_hp=data['combat_stats']['current_hp'],
            chaos_damage=data['combat_stats']['chaos_damage'],
            vile_damage=data['combat_stats']['vile_damage'],
            elemental_attack=data['combat_stats']['elemental_attack'],
            elemental_resist=data['combat_stats']['elemental_resist'],
            wilderness_level=data['combat_stats']['wilderness_level'],
            god_slayer_level=data['combat_stats']['god_slayer_level'],
            
            fire_resist=data['resistances']['fire_resist'],
            kinetic_resist=data['resistances']['kinetic_resist'],
            arcane_resist=data['resistances']['arcane_resist'],
            holy_resist=data['resistances']['holy_resist'],
            shadow_resist=data['resistances']['shadow_resist'],
            
            gold=data['resources']['gold'],
            rage=data['resources']['rage'],
            max_rage=data['resources']['max_rage'],
            rage_per_hour=data['resources']['rage_per_hour'],
            exp_per_hour=data['resources']['exp_per_hour'],
            gold_per_turn=data['resources']['gold_per_turn'],
            
            critical_hit_chance=data['combat_bonuses']['critical_hit_chance'],
            rampage_bonus=data['combat_bonuses']['rampage_bonus'],
            
            parent_id=data['social']['parent_id'],
            faction=data['social']['faction'],
            crew_id=data['social']['crew_id'],
            crew_rank=data['social']['crew_rank'],
            
            alvar_loyalty=data['faction_loyalty']['alvar_loyalty'],
            delruk_loyalty=data['faction_loyalty']['delruk_loyalty'],
            vordyn_loyalty=data['faction_loyalty']['vordyn_loyalty'],
            
            current_room_id=data['location']['current_room_id'],
            current_zone=data['location']['current_zone'],
            
            created_at=datetime.fromisoformat(data['timestamps']['created_at']),
            last_active=datetime.fromisoformat(data['timestamps']['last_active']),
            last_resource_update=datetime.fromisoformat(data['timestamps']['last_resource_update']),
            faction_change_last_used=datetime.fromisoformat(data['timestamps']['faction_change_last_used']) if data['timestamps']['faction_change_last_used'] else None
        )