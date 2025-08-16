import uuid
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date
from models.equipment import ItemTemplate, CharacterItem, CrewVaultItem, EquipmentSlots, get_available_slots_for_item
from redis_client import RedisManager

class EquipmentService:
    def __init__(self, db_pool, queries, redis_client):
        self.db = db_pool
        self.queries = queries
        self.redis = RedisManager(redis_client)
    
    async def create_item_template(self, item_data: Dict[str, Any]) -> str:
        """Create a new item template"""
        async with self.db.acquire() as conn:
            result = await self.queries.create_item_template(
                conn,
                item_data['name'], item_data['item_type'], item_data['slot'],
                item_data['rarity'], item_data['level_requirement'],
                item_data.get('attack_bonus', 0), item_data.get('hp_bonus', 0),
                item_data.get('chaos_damage_bonus', 0), item_data.get('vile_damage_bonus', 0),
                item_data.get('elemental_attack_bonus', 0),
                item_data.get('fire_resist_bonus', 0), item_data.get('kinetic_resist_bonus', 0),
                item_data.get('arcane_resist_bonus', 0), item_data.get('holy_resist_bonus', 0),
                item_data.get('shadow_resist_bonus', 0), item_data.get('elemental_resist_bonus', 0),
                item_data.get('rage_per_hour_bonus', 0), item_data.get('exp_per_hour_bonus', 0),
                item_data.get('gold_per_turn_bonus', 0), item_data.get('max_rage_bonus', 0),
                item_data.get('critical_hit_bonus', 0.0), item_data.get('rampage_bonus', 0),
                item_data.get('can_transfer', True), item_data.get('max_transfers_per_day', 3),
                item_data.get('is_raidbound', False), item_data.get('description', '')
            )
            return str(result['id'])
    
    async def get_item_template(self, template_id: str) -> Optional[ItemTemplate]:
        """Get item template by ID"""
        async with self.db.acquire() as conn:
            result = await self.queries.get_item_template_by_id(conn, template_id)
            if result:
                return self._db_result_to_item_template(result)
        return None
    
    async def get_character_items(self, character_id: str) -> List[CharacterItem]:
        """Get all items for a character"""
        async with self.db.acquire() as conn:
            results = await self.queries.get_character_items(conn, character_id)
            return [self._db_result_to_character_item(row) for row in results]
    
    async def get_character_equipped_items(self, character_id: str) -> EquipmentSlots:
        """Get character's equipped items organized by slots"""
        async with self.db.acquire() as conn:
            results = await self.queries.get_character_equipped_items(conn, character_id)
        
        equipment = EquipmentSlots()
        
        for row in results:
            item = self._db_result_to_character_item(row)
            slot = row['equipped_slot']
            if slot and hasattr(equipment, slot):
                setattr(equipment, slot, item)
        
        return equipment
    
    async def give_item_to_character(self, character_id: str, item_template_id: str) -> Optional[str]:
        """Give an item to a character"""
        async with self.db.acquire() as conn:
            # Get next inventory position
            position_result = await self.queries.get_next_inventory_position(conn, character_id)
            next_position = position_result if position_result else 1
            
            # Create the item
            result = await self.queries.give_item_to_character(
                conn, character_id, item_template_id, next_position
            )
            
            if result:
                # Invalidate character cache
                await self.redis.invalidate_character_cache(character_id)
                return str(result['id'])
        
        return None
    
    async def equip_item(self, character_id: str, item_id: str, slot: str) -> Tuple[bool, str]:
        """Equip an item to a specific slot"""
        # Get the item
        item = await self.get_character_item(character_id, item_id)
        if not item:
            return False, "Item not found"
        
        if item.is_equipped:
            return False, "Item is already equipped"
        
        # Check if slot is valid for this item type
        available_slots = get_available_slots_for_item(item.template.slot)
        if slot not in available_slots:
            return False, f"Cannot equip {item.template.slot} item to {slot} slot"
        
        # Check if slot is already occupied
        equipment = await self.get_character_equipped_items(character_id)
        current_item = equipment.get_item_in_slot(slot)
        
        async with self.db.acquire() as conn:
            if current_item:
                # Unequip current item first
                next_inv_pos = await self.queries.get_next_inventory_position(conn, character_id)
                await self.queries.unequip_item(conn, current_item.id, next_inv_pos, character_id)
            
            # Equip the new item
            await self.queries.equip_item(conn, item_id, slot, character_id)
        
        # Update character stats
        await self._update_character_stats_from_equipment(character_id)
        
        return True, "Item equipped successfully"
    
    async def unequip_item(self, character_id: str, item_id: str) -> Tuple[bool, str]:
        """Unequip an item"""
        item = await self.get_character_item(character_id, item_id)
        if not item:
            return False, "Item not found"
        
        if not item.is_equipped:
            return False, "Item is not equipped"
        
        async with self.db.acquire() as conn:
            # Get next inventory position
            next_position = await self.queries.get_next_inventory_position(conn, character_id)
            
            # Unequip the item
            await self.queries.unequip_item(conn, item_id, next_position, character_id)
        
        # Update character stats
        await self._update_character_stats_from_equipment(character_id)
        
        return True, "Item unequipped successfully"
    
    async def transfer_item(self, item_id: str, from_character_id: str, to_character_id: str) -> Tuple[bool, str]:
        """Transfer an item between characters"""
        item = await self.get_character_item(from_character_id, item_id)
        if not item:
            return False, "Item not found"
        
        if item.is_equipped:
            return False, "Cannot transfer equipped items"
        
        if not item.can_transfer_today():
            return False, "Item has reached daily transfer limit"
        
        if item.template.is_raidbound:
            return False, "Raidbound items cannot be transferred"
        
        # Create transfer record
        transfer_record = {
            'from_character_id': from_character_id,
            'to_character_id': to_character_id,
            'timestamp': datetime.now().isoformat(),
            'transfer_type': 'character_to_character'
        }
        
        async with self.db.acquire() as conn:
            # Get next inventory position for target character
            next_position = await self.queries.get_next_inventory_position(conn, to_character_id)
            
            # Update item ownership and transfer count
            await self.queries.transfer_item(conn, item_id, to_character_id, [transfer_record])
        
        # Update transfer count in Redis
        await self.redis.increment_daily_transfer_count(item_id)
        
        # Invalidate caches
        await self.redis.invalidate_character_cache(from_character_id)
        await self.redis.invalidate_character_cache(to_character_id)
        
        return True, "Item transferred successfully"
    
    async def get_crew_vault_items(self, crew_id: str) -> List[CrewVaultItem]:
        """Get all items in crew vault"""
        async with self.db.acquire() as conn:
            results = await self.queries.get_crew_vault_items(conn, crew_id)
            return [self._db_result_to_crew_vault_item(row) for row in results]
    
    async def deposit_item_to_vault(self, character_id: str, item_id: str, crew_id: str) -> Tuple[bool, str]:
        """Deposit an item from character to crew vault"""
        item = await self.get_character_item(character_id, item_id)
        if not item:
            return False, "Item not found"
        
        if item.is_equipped:
            return False, "Cannot deposit equipped items"
        
        # Check crew vault capacity
        vault_items = await self.get_crew_vault_items(crew_id)
        if len(vault_items) >= 100:  # Default vault capacity
            return False, "Crew vault is full"
        
        async with self.db.acquire() as conn:
            # Get next vault position
            next_position = await self.queries.get_next_vault_position(conn, crew_id)
            
            # Deposit item to vault
            await self.queries.deposit_item_to_vault(conn, crew_id, character_id, next_position, item_id)
            
            # Remove from character
            await self.queries.remove_item_from_character(conn, item_id, character_id)
        
        await self.redis.invalidate_character_cache(character_id)
        
        return True, "Item deposited to crew vault"
    
    async def award_vault_item(self, vault_item_id: str, crew_id: str, character_id: str) -> Tuple[bool, str]:
        """Award a vault item to a character"""
        async with self.db.acquire() as conn:
            # Get next inventory position for character
            next_position = await self.queries.get_next_inventory_position(conn, character_id)
            
            # Award item to character
            result = await self.queries.award_vault_item_to_character(
                conn, character_id, next_position, vault_item_id
            )
            
            if result:
                # Remove from vault
                await self.queries.remove_vault_item(conn, vault_item_id, crew_id)
        
        await self.redis.invalidate_character_cache(character_id)
        
        return True, "Item awarded successfully"
    
    async def delete_vault_item(self, vault_item_id: str, crew_id: str) -> Tuple[bool, str]:
        """Delete an item from crew vault"""
        async with self.db.acquire() as conn:
            await self.queries.remove_vault_item(conn, vault_item_id, crew_id)
        
        return True, "Item deleted from vault"
    
    async def get_character_item(self, character_id: str, item_id: str) -> Optional[CharacterItem]:
        """Get a specific character item"""
        items = await self.get_character_items(character_id)
        for item in items:
            if item.id == item_id:
                return item
        return None
    
    async def _update_character_stats_from_equipment(self, character_id: str):
        """Update character's stats based on equipped items"""
        equipment = await self.get_character_equipped_items(character_id)
        bonuses = equipment.calculate_total_bonuses()
        
        # This would update character stats in the database
        # Implementation depends on how character stats are calculated
        # For now, invalidate cache so stats are recalculated on next access
        await self.redis.invalidate_character_cache(character_id)
    
    def _db_result_to_item_template(self, result: Dict[str, Any]) -> ItemTemplate:
        """Convert database result to ItemTemplate"""
        return ItemTemplate(
            id=str(result['id']),
            name=result['name'],
            item_type=result['item_type'],
            slot=result['slot'],
            rarity=result['rarity'],
            level_requirement=result['level_requirement'],
            attack_bonus=result['attack_bonus'],
            hp_bonus=result['hp_bonus'],
            chaos_damage_bonus=result['chaos_damage_bonus'],
            vile_damage_bonus=result['vile_damage_bonus'],
            elemental_attack_bonus=result['elemental_attack_bonus'],
            fire_resist_bonus=result['fire_resist_bonus'],
            kinetic_resist_bonus=result['kinetic_resist_bonus'],
            arcane_resist_bonus=result['arcane_resist_bonus'],
            holy_resist_bonus=result['holy_resist_bonus'],
            shadow_resist_bonus=result['shadow_resist_bonus'],
            elemental_resist_bonus=result['elemental_resist_bonus'],
            rage_per_hour_bonus=result['rage_per_hour_bonus'],
            exp_per_hour_bonus=result['exp_per_hour_bonus'],
            gold_per_turn_bonus=result['gold_per_turn_bonus'],
            max_rage_bonus=result['max_rage_bonus'],
            critical_hit_bonus=float(result['critical_hit_bonus']),
            rampage_bonus=result['rampage_bonus'],
            can_transfer=result['can_transfer'],
            max_transfers_per_day=result['max_transfers_per_day'],
            is_raidbound=result['is_raidbound'],
            description=result['description'],
            created_at=result['created_at']
        )
    
    def _db_result_to_character_item(self, result: Dict[str, Any]) -> CharacterItem:
        """Convert database result to CharacterItem"""
        template = self._db_result_to_item_template(result)
        
        return CharacterItem(
            id=str(result['id']),
            character_id=str(result['character_id']),
            item_template_id=str(result['item_template_id']),
            template=template,
            equipped_slot=result['equipped_slot'],
            is_equipped=result['is_equipped'],
            inventory_position=result['inventory_position'],
            transfers_today=result['transfers_today'],
            last_transfer_date=result['last_transfer_date'],
            transfer_history=result.get('transfer_history', []),
            augments=result.get('augments', []),
            custom_stats=result.get('custom_stats', {}),
            acquired_at=result['acquired_at']
        )
    
    def _db_result_to_crew_vault_item(self, result: Dict[str, Any]) -> CrewVaultItem:
        """Convert database result to CrewVaultItem"""
        template = self._db_result_to_item_template(result)
        
        return CrewVaultItem(
            id=str(result['id']),
            crew_id=str(result['crew_id']),
            item_template_id=str(result['item_template_id']),
            template=template,
            deposited_by=str(result['deposited_by']) if result['deposited_by'] else None,
            deposited_by_name=result.get('deposited_by_name'),
            vault_position=result['vault_position'],
            deposited_at=result['deposited_at'],
            augments=result.get('augments', []),
            custom_stats=result.get('custom_stats', {})
        )