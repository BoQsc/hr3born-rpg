from dataclasses import dataclass
from typing import Optional, Dict, Any
import math

@dataclass
class Character:
    id: int
    account_id: int
    name: str
    class_id: int
    class_name: str
    level: int = 1
    experience: int = 0
    gold: int = 1000
    rage_current: int = 100
    rage_max: int = 100
    hit_points_current: int = 100
    hit_points_max: int = 100
    
    # Combat stats
    attack: int = 10
    chaos_damage: int = 0
    vile_damage: int = 0
    fire_damage: int = 0
    kinetic_damage: int = 0
    arcane_damage: int = 0
    holy_damage: int = 0
    shadow_damage: int = 0
    
    # Resistances
    fire_resist: int = 0
    kinetic_resist: int = 0
    arcane_resist: int = 0
    holy_resist: int = 0
    shadow_resist: int = 0
    
    # Special stats
    wilderness_level: int = 1
    god_slayer_level: int = 0
    total_power: int = 0
    
    # Class bonuses
    attack_bonus: float = 0.0
    defense_bonus: float = 0.0
    rage_per_turn_bonus: float = 0.0
    max_rage_bonus: float = 0.0
    
    # Faction system
    faction_id: Optional[int] = None
    faction_name: Optional[str] = None
    alvar_loyalty: int = 0
    delruk_loyalty: int = 0
    vordyn_loyalty: int = 0
    
    # Location
    current_room_id: int = 1
    
    @classmethod
    def from_db_row(cls, row: Dict[str, Any]) -> 'Character':
        """Create Character from database row"""
        return cls(**row)
    
    def experience_needed_for_next_level(self) -> int:
        """Calculate experience needed for next level"""
        if self.level >= 95:
            return 0
        # Exponential curve: level^3 * 100
        next_level_exp = (self.level + 1) ** 3 * 100
        current_level_exp = self.level ** 3 * 100
        return next_level_exp - self.experience
    
    def can_level_up(self) -> bool:
        """Check if character can level up"""
        if self.level >= 95:
            return False
        required_exp = (self.level + 1) ** 3 * 100
        return self.experience >= required_exp
    
    def level_up(self) -> Dict[str, int]:
        """Level up the character and return stat gains"""
        if not self.can_level_up():
            return {}
            
        old_level = self.level
        self.level += 1
        
        # Base stat gains per level
        hp_gain = 5 + (self.level // 10)  # 5-14 HP per level
        attack_gain = 2 + (self.level // 15)  # 2-8 attack per level
        rage_gain = 3 + (self.level // 20)  # 3-7 rage per level
        
        # Apply class bonuses
        attack_gain = int(attack_gain * (1 + self.attack_bonus))
        hp_gain = int(hp_gain * (1 + self.defense_bonus))
        rage_gain = int(rage_gain * (1 + self.max_rage_bonus))
        
        self.hit_points_max += hp_gain
        self.hit_points_current += hp_gain  # Heal on level up
        self.attack += attack_gain
        self.rage_max += rage_gain
        self.rage_current = min(self.rage_current + rage_gain, self.rage_max)
        
        return {
            'level': self.level - old_level,
            'hp': hp_gain,
            'attack': attack_gain,
            'rage': rage_gain
        }
    
    def get_effective_attack(self) -> int:
        """Get attack including class bonuses"""
        return int(self.attack * (1 + self.attack_bonus))
    
    def get_effective_defense(self) -> int:
        """Get defense including class bonuses"""
        return int(self.hit_points_max * (1 + self.defense_bonus))
    
    def get_total_elemental_damage(self) -> int:
        """Get sum of all elemental damage types"""
        return (self.fire_damage + self.kinetic_damage + self.arcane_damage + 
                self.holy_damage + self.shadow_damage)
    
    def get_total_resistance(self) -> int:
        """Get sum of all resistances"""
        return (self.fire_resist + self.kinetic_resist + self.arcane_resist + 
                self.holy_resist + self.shadow_resist)
    
    def is_alive(self) -> bool:
        """Check if character is alive"""
        return self.hit_points_current > 0
    
    def calculate_damage_to(self, target: 'Character') -> Dict[str, int]:
        """Calculate damage this character would deal to target"""
        base_damage = self.get_effective_attack()
        
        # Add elemental damages
        fire_dmg = max(0, self.fire_damage - target.fire_resist)
        kinetic_dmg = max(0, self.kinetic_damage - target.kinetic_resist)
        arcane_dmg = max(0, self.arcane_damage - target.arcane_resist)
        holy_dmg = max(0, self.holy_damage - target.holy_resist)
        shadow_dmg = max(0, self.shadow_damage - target.shadow_resist)
        
        elemental_total = fire_dmg + kinetic_dmg + arcane_dmg + holy_dmg + shadow_dmg
        
        # Special damage types (not reduced by resistances)
        chaos_dmg = self.chaos_damage
        vile_dmg = self.vile_damage
        
        total_damage = base_damage + elemental_total + chaos_dmg + vile_dmg
        
        # Add some randomness (±20%)
        import random
        variance = random.uniform(0.8, 1.2)
        total_damage = int(total_damage * variance)
        
        return {
            'base': base_damage,
            'fire': fire_dmg,
            'kinetic': kinetic_dmg,
            'arcane': arcane_dmg,
            'holy': holy_dmg,
            'shadow': shadow_dmg,
            'chaos': chaos_dmg,
            'vile': vile_dmg,
            'total': max(1, total_damage)  # Minimum 1 damage
        }
    
    def take_damage(self, damage: int) -> int:
        """Apply damage and return actual damage taken"""
        if damage <= 0:
            return 0
            
        actual_damage = min(damage, self.hit_points_current)
        self.hit_points_current -= actual_damage
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """Heal character and return actual healing done"""
        if amount <= 0:
            return 0
            
        actual_healing = min(amount, self.hit_points_max - self.hit_points_current)
        self.hit_points_current += actual_healing
        return actual_healing
    
    def gain_experience(self, amount: int) -> Dict[str, int]:
        """Gain experience and potentially level up"""
        self.experience += amount
        level_gains = {}
        
        # Check for level ups
        while self.can_level_up():
            gains = self.level_up()
            for stat, value in gains.items():
                level_gains[stat] = level_gains.get(stat, 0) + value
        
        return level_gains
    
    def can_access_factions(self) -> bool:
        """Check if character can access faction system (level 91+)"""
        return self.level >= 91
    
    def get_faction_bonus(self) -> Dict[str, float]:
        """Get current faction bonuses"""
        if not self.faction_id or not self.can_access_factions():
            return {}
            
        bonus_multiplier = 0
        bonus_type = ""
        
        if self.faction_id == 1:  # Alvar Liberation
            bonus_multiplier = self.alvar_loyalty * 0.01
            bonus_type = "elemental"
        elif self.faction_id == 2:  # Delruk Alliance
            bonus_multiplier = self.delruk_loyalty * 0.02
            bonus_type = "attack_vile"
        elif self.faction_id == 3:  # Vordyn Rebellion
            bonus_multiplier = self.vordyn_loyalty * 0.02
            bonus_type = "chaos"
            
        return {"type": bonus_type, "multiplier": bonus_multiplier}

@dataclass
class Equipment:
    slot_id: int
    slot_name: str
    item_id: Optional[int] = None
    item_name: Optional[str] = None
    rarity_name: Optional[str] = None
    rarity_color: Optional[str] = None
    
    # Stats from equipped item
    attack: int = 0
    hit_points: int = 0
    chaos_damage: int = 0
    vile_damage: int = 0
    fire_damage: int = 0
    kinetic_damage: int = 0
    arcane_damage: int = 0
    holy_damage: int = 0
    shadow_damage: int = 0
    fire_resist: int = 0
    kinetic_resist: int = 0
    arcane_resist: int = 0
    holy_resist: int = 0
    shadow_resist: int = 0
    critical_hit_percent: float = 0.0
    rampage_percent: float = 0.0
    rage_per_hour: int = 0
    experience_per_hour: int = 0
    gold_per_turn: int = 0
    max_rage: int = 0

@dataclass 
class InventoryItem:
    id: int
    item_id: int
    name: str
    slot_name: str
    rarity_name: str
    rarity_color: str
    level_requirement: int
    quantity: int = 1
    transfers_remaining: Optional[int] = None
    
    # Item stats
    attack: int = 0
    hit_points: int = 0