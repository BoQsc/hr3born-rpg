from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from config import Config

@dataclass
class ItemTemplate:
    id: str
    name: str
    item_type: str
    slot: str
    rarity: str
    level_requirement: int
    
    # Base stats
    attack_bonus: int
    hp_bonus: int
    chaos_damage_bonus: int
    vile_damage_bonus: int
    elemental_attack_bonus: int
    
    # Resistances
    fire_resist_bonus: int
    kinetic_resist_bonus: int
    arcane_resist_bonus: int
    holy_resist_bonus: int
    shadow_resist_bonus: int
    elemental_resist_bonus: int
    
    # Resource generation
    rage_per_hour_bonus: int
    exp_per_hour_bonus: int
    gold_per_turn_bonus: int
    max_rage_bonus: int
    
    # Combat bonuses
    critical_hit_bonus: float
    rampage_bonus: int
    
    # Meta properties
    can_transfer: bool
    max_transfers_per_day: int
    is_raidbound: bool
    
    description: str
    created_at: datetime
    
    def get_rarity_multiplier(self) -> float:
        """Get stat multiplier based on rarity"""
        multipliers = {
            'elite': 1.0,
            'brutal': 1.2,
            'godly': 1.5,
            'king': 2.0,
            'mythic': 3.0
        }
        return multipliers.get(self.rarity, 1.0)
    
    def get_effective_stats(self) -> Dict[str, Any]:
        """Get stats with rarity multiplier applied"""
        multiplier = self.get_rarity_multiplier()
        
        return {
            'attack_bonus': int(self.attack_bonus * multiplier),
            'hp_bonus': int(self.hp_bonus * multiplier),
            'chaos_damage_bonus': int(self.chaos_damage_bonus * multiplier),
            'vile_damage_bonus': int(self.vile_damage_bonus * multiplier),
            'elemental_attack_bonus': int(self.elemental_attack_bonus * multiplier),
            'fire_resist_bonus': int(self.fire_resist_bonus * multiplier),
            'kinetic_resist_bonus': int(self.kinetic_resist_bonus * multiplier),
            'arcane_resist_bonus': int(self.arcane_resist_bonus * multiplier),
            'holy_resist_bonus': int(self.holy_resist_bonus * multiplier),
            'shadow_resist_bonus': int(self.shadow_resist_bonus * multiplier),
            'elemental_resist_bonus': int(self.elemental_resist_bonus * multiplier),
            'rage_per_hour_bonus': int(self.rage_per_hour_bonus * multiplier),
            'exp_per_hour_bonus': int(self.exp_per_hour_bonus * multiplier),
            'gold_per_turn_bonus': int(self.gold_per_turn_bonus * multiplier),
            'max_rage_bonus': int(self.max_rage_bonus * multiplier),
            'critical_hit_bonus': self.critical_hit_bonus * multiplier,
            'rampage_bonus': int(self.rampage_bonus * multiplier)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'item_type': self.item_type,
            'slot': self.slot,
            'rarity': self.rarity,
            'level_requirement': self.level_requirement,
            'stats': self.get_effective_stats(),
            'meta': {
                'can_transfer': self.can_transfer,
                'max_transfers_per_day': self.max_transfers_per_day,
                'is_raidbound': self.is_raidbound
            },
            'description': self.description,
            'created_at': self.created_at.isoformat()
        }

@dataclass
class CharacterItem:
    id: str
    character_id: str
    item_template_id: str
    template: ItemTemplate
    
    # Item state
    equipped_slot: Optional[str]
    is_equipped: bool
    inventory_position: Optional[int]
    
    # Transfer tracking
    transfers_today: int
    last_transfer_date: date
    transfer_history: List[Dict[str, Any]]
    
    # Augments and modifications
    augments: List[Dict[str, Any]]
    custom_stats: Dict[str, Any]
    
    acquired_at: datetime
    
    def can_transfer_today(self) -> bool:
        """Check if item can be transferred today"""
        if not self.template.can_transfer:
            return False
        
        # Reset transfer count if it's a new day
        today = date.today()
        if self.last_transfer_date != today:
            return True
        
        return self.transfers_today < self.template.max_transfers_per_day
    
    def get_transfers_remaining_today(self) -> int:
        """Get number of transfers remaining today"""
        if not self.template.can_transfer:
            return 0
        
        today = date.today()
        if self.last_transfer_date != today:
            return self.template.max_transfers_per_day
        
        return max(0, self.template.max_transfers_per_day - self.transfers_today)
    
    def get_total_stats(self) -> Dict[str, Any]:
        """Get total stats including augments and custom modifications"""
        base_stats = self.template.get_effective_stats()
        
        # Apply custom stats (from augments, etc.)
        for stat, value in self.custom_stats.items():
            if stat in base_stats:
                base_stats[stat] += value
        
        # Apply augment bonuses
        for augment in self.augments:
            for stat, value in augment.get('stats', {}).items():
                if stat in base_stats:
                    base_stats[stat] += value
        
        return base_stats
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'character_id': self.character_id,
            'template': self.template.to_dict(),
            'state': {
                'equipped_slot': self.equipped_slot,
                'is_equipped': self.is_equipped,
                'inventory_position': self.inventory_position
            },
            'transfer_info': {
                'transfers_today': self.transfers_today,
                'transfers_remaining': self.get_transfers_remaining_today(),
                'can_transfer_today': self.can_transfer_today(),
                'last_transfer_date': self.last_transfer_date.isoformat()
            },
            'stats': self.get_total_stats(),
            'augments': self.augments,
            'custom_stats': self.custom_stats,
            'acquired_at': self.acquired_at.isoformat()
        }

@dataclass
class CrewVaultItem:
    id: str
    crew_id: str
    item_template_id: str
    template: ItemTemplate
    deposited_by: Optional[str]
    deposited_by_name: Optional[str]
    vault_position: int
    deposited_at: datetime
    
    # Item state from when it was deposited
    augments: List[Dict[str, Any]]
    custom_stats: Dict[str, Any]
    
    def get_total_stats(self) -> Dict[str, Any]:
        """Get total stats including augments and custom modifications"""
        base_stats = self.template.get_effective_stats()
        
        # Apply custom stats
        for stat, value in self.custom_stats.items():
            if stat in base_stats:
                base_stats[stat] += value
        
        # Apply augment bonuses
        for augment in self.augments:
            for stat, value in augment.get('stats', {}).items():
                if stat in base_stats:
                    base_stats[stat] += value
        
        return base_stats
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'crew_id': self.crew_id,
            'template': self.template.to_dict(),
            'vault_position': self.vault_position,
            'deposited_by': self.deposited_by,
            'deposited_by_name': self.deposited_by_name,
            'deposited_at': self.deposited_at.isoformat(),
            'stats': self.get_total_stats(),
            'augments': self.augments,
            'custom_stats': self.custom_stats
        }

@dataclass
class EquipmentSlots:
    """Represents character's equipment slots"""
    # Top row
    accessory_1: Optional[CharacterItem] = None
    head: Optional[CharacterItem] = None
    accessory_2: Optional[CharacterItem] = None
    
    # Middle row
    weapon: Optional[CharacterItem] = None
    chest: Optional[CharacterItem] = None
    shield: Optional[CharacterItem] = None
    
    # Bottom row
    ring_1: Optional[CharacterItem] = None
    legs: Optional[CharacterItem] = None
    ring_2: Optional[CharacterItem] = None
    
    # Additional
    boots: Optional[CharacterItem] = None
    
    # Quick slots (5 additional)
    quick_1: Optional[CharacterItem] = None
    quick_2: Optional[CharacterItem] = None
    quick_3: Optional[CharacterItem] = None
    quick_4: Optional[CharacterItem] = None
    quick_5: Optional[CharacterItem] = None
    
    def get_all_equipped_items(self) -> List[CharacterItem]:
        """Get all equipped items"""
        items = []
        for slot_name in self.__dataclass_fields__:
            item = getattr(self, slot_name)
            if item is not None:
                items.append(item)
        return items
    
    def get_item_in_slot(self, slot: str) -> Optional[CharacterItem]:
        """Get item in specific slot"""
        return getattr(self, slot, None)
    
    def set_item_in_slot(self, slot: str, item: Optional[CharacterItem]):
        """Set item in specific slot"""
        if hasattr(self, slot):
            setattr(self, slot, item)
    
    def calculate_total_bonuses(self) -> Dict[str, Any]:
        """Calculate total stat bonuses from all equipped items"""
        total_bonuses = {
            'attack_bonus': 0,
            'hp_bonus': 0,
            'chaos_damage_bonus': 0,
            'vile_damage_bonus': 0,
            'elemental_attack_bonus': 0,
            'fire_resist_bonus': 0,
            'kinetic_resist_bonus': 0,
            'arcane_resist_bonus': 0,
            'holy_resist_bonus': 0,
            'shadow_resist_bonus': 0,
            'elemental_resist_bonus': 0,
            'rage_per_hour_bonus': 0,
            'exp_per_hour_bonus': 0,
            'gold_per_turn_bonus': 0,
            'max_rage_bonus': 0,
            'critical_hit_bonus': 0.0,
            'rampage_bonus': 0
        }
        
        for item in self.get_all_equipped_items():
            item_stats = item.get_total_stats()
            for stat, value in item_stats.items():
                if stat in total_bonuses:
                    total_bonuses[stat] += value
        
        return total_bonuses
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        result = {}
        for slot_name in self.__dataclass_fields__:
            item = getattr(self, slot_name)
            result[slot_name] = item.to_dict() if item else None
        
        result['total_bonuses'] = self.calculate_total_bonuses()
        return result

# Equipment slot mappings
EQUIPMENT_SLOTS = {
    'accessory': ['accessory_1', 'accessory_2'],
    'head': ['head'],
    'weapon': ['weapon'],
    'chest': ['chest'],
    'shield': ['shield'],
    'ring': ['ring_1', 'ring_2'],
    'legs': ['legs'],
    'boots': ['boots'],
    'quick': ['quick_1', 'quick_2', 'quick_3', 'quick_4', 'quick_5']
}

def get_available_slots_for_item(item_type: str) -> List[str]:
    """Get list of slots where an item type can be equipped"""
    return EQUIPMENT_SLOTS.get(item_type, [])