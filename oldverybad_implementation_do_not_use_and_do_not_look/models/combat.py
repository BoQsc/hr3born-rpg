from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import random
import math
from enum import Enum

class DamageType(Enum):
    PHYSICAL = "physical"
    FIRE = "fire"
    KINETIC = "kinetic"
    ARCANE = "arcane"
    HOLY = "holy"
    SHADOW = "shadow"
    CHAOS = "chaos"
    VILE = "vile"

class CombatActionType(Enum):
    ATTACK = "attack"
    BLOCK = "block"
    CRITICAL = "critical"
    MISS = "miss"
    HEAL = "heal"
    SPECIAL = "special"

@dataclass
class CombatStats:
    """Combat stats for characters and NPCs"""
    level: int
    attack: int
    hit_points: int
    current_hp: int
    chaos_damage: int
    vile_damage: int
    elemental_attack: int
    
    # Resistances
    fire_resist: int
    kinetic_resist: int
    arcane_resist: int
    holy_resist: int
    shadow_resist: int
    elemental_resist: int
    
    # Combat bonuses
    critical_hit_chance: float
    rampage_bonus: int
    
    def get_total_attack(self) -> int:
        """Get total attack power"""
        return self.attack + self.elemental_attack + self.chaos_damage + self.vile_damage
    
    def get_resistance(self, damage_type: DamageType) -> int:
        """Get resistance for specific damage type"""
        resistance_map = {
            DamageType.FIRE: self.fire_resist,
            DamageType.KINETIC: self.kinetic_resist,
            DamageType.ARCANE: self.arcane_resist,
            DamageType.HOLY: self.holy_resist,
            DamageType.SHADOW: self.shadow_resist,
            DamageType.PHYSICAL: 0,  # No specific physical resistance
            DamageType.CHAOS: 0,     # Chaos damage ignores resistance
            DamageType.VILE: 0       # Vile damage ignores resistance
        }
        return resistance_map.get(damage_type, 0)
    
    def is_alive(self) -> bool:
        """Check if combatant is alive"""
        return self.current_hp > 0
    
    def take_damage(self, amount: int) -> int:
        """Take damage and return actual damage taken"""
        actual_damage = min(amount, self.current_hp)
        self.current_hp = max(0, self.current_hp - amount)
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """Heal and return actual healing done"""
        actual_healing = min(amount, self.hit_points - self.current_hp)
        self.current_hp = min(self.hit_points, self.current_hp + amount)
        return actual_healing

@dataclass
class CombatAction:
    """Represents a single combat action"""
    action_type: CombatActionType
    attacker_name: str
    target_name: str
    damage_amount: int
    damage_type: DamageType
    is_critical: bool = False
    is_blocked: bool = False
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_type': self.action_type.value,
            'attacker_name': self.attacker_name,
            'target_name': self.target_name,
            'damage_amount': self.damage_amount,
            'damage_type': self.damage_type.value,
            'is_critical': self.is_critical,
            'is_blocked': self.is_blocked,
            'message': self.message
        }

@dataclass
class CombatResult:
    """Result of a combat encounter"""
    winner_id: Optional[str]
    winner_name: str
    loser_id: Optional[str]
    loser_name: str
    combat_log: List[CombatAction]
    duration_seconds: int
    total_damage_dealt: int
    total_damage_received: int
    
    # Rewards
    exp_gained: int
    gold_gained: int
    items_gained: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'winner_id': self.winner_id,
            'winner_name': self.winner_name,
            'loser_id': self.loser_id,
            'loser_name': self.loser_name,
            'combat_log': [action.to_dict() for action in self.combat_log],
            'duration_seconds': self.duration_seconds,
            'total_damage_dealt': self.total_damage_dealt,
            'total_damage_received': self.total_damage_received,
            'rewards': {
                'exp_gained': self.exp_gained,
                'gold_gained': self.gold_gained,
                'items_gained': self.items_gained
            }
        }

@dataclass
class NPC:
    """NPC model for combat"""
    id: str
    name: str
    npc_type: str
    level: int
    room_id: str
    stats: CombatStats
    
    # Rewards
    gold_reward: int
    exp_reward: int
    loot_table: List[Dict[str, Any]]
    
    # Respawn
    respawn_time: int
    last_killed: Optional[datetime]
    
    # Special properties
    is_boss: bool
    is_raid_boss: bool
    faction_requirement: Optional[str]
    description: str
    
    def is_available(self) -> bool:
        """Check if NPC is available for combat (respawned)"""
        if not self.last_killed:
            return True
        
        time_since_death = datetime.now() - self.last_killed
        return time_since_death.total_seconds() >= self.respawn_time
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'npc_type': self.npc_type,
            'level': self.level,
            'room_id': self.room_id,
            'stats': {
                'level': self.stats.level,
                'attack': self.stats.attack,
                'hit_points': self.stats.hit_points,
                'current_hp': self.stats.current_hp,
                'resistances': {
                    'fire': self.stats.fire_resist,
                    'kinetic': self.stats.kinetic_resist,
                    'arcane': self.stats.arcane_resist,
                    'holy': self.stats.holy_resist,
                    'shadow': self.stats.shadow_resist
                }
            },
            'rewards': {
                'gold_reward': self.gold_reward,
                'exp_reward': self.exp_reward,
                'loot_table': self.loot_table
            },
            'properties': {
                'is_boss': self.is_boss,
                'is_raid_boss': self.is_raid_boss,
                'faction_requirement': self.faction_requirement
            },
            'description': self.description
        }

class CombatEngine:
    """Main combat calculation engine"""
    
    @staticmethod
    def calculate_damage(attacker_stats: CombatStats, defender_stats: CombatStats, 
                        damage_type: DamageType) -> tuple[int, bool, bool]:
        """
        Calculate damage dealt from attacker to defender
        Returns: (damage_amount, is_critical, is_blocked)
        """
        # Base damage calculation
        base_damage = 0
        
        if damage_type == DamageType.PHYSICAL:
            base_damage = attacker_stats.attack
        elif damage_type == DamageType.FIRE:
            base_damage = attacker_stats.elemental_attack
        elif damage_type == DamageType.KINETIC:
            base_damage = attacker_stats.elemental_attack
        elif damage_type == DamageType.ARCANE:
            base_damage = attacker_stats.elemental_attack
        elif damage_type == DamageType.HOLY:
            base_damage = attacker_stats.elemental_attack
        elif damage_type == DamageType.SHADOW:
            base_damage = attacker_stats.elemental_attack
        elif damage_type == DamageType.CHAOS:
            base_damage = attacker_stats.chaos_damage
        elif damage_type == DamageType.VILE:
            base_damage = attacker_stats.vile_damage
        
        # Add random variance (±20%)
        variance = random.uniform(0.8, 1.2)
        base_damage = int(base_damage * variance)
        
        # Check for critical hit
        is_critical = random.random() < (attacker_stats.critical_hit_chance / 100)
        if is_critical:
            base_damage = int(base_damage * 1.5)  # 50% critical bonus
        
        # Check for block (defender has small chance to block)
        block_chance = 0.1  # 10% base block chance
        is_blocked = random.random() < block_chance
        if is_blocked:
            base_damage = int(base_damage * 0.3)  # Blocked attacks do 30% damage
        
        # Apply resistance (except for chaos/vile damage)
        if damage_type not in [DamageType.CHAOS, DamageType.VILE]:
            resistance = defender_stats.get_resistance(damage_type)
            # Resistance reduces damage by a percentage (max 90% reduction)
            resistance_reduction = min(0.9, resistance / 1000.0)
            base_damage = int(base_damage * (1 - resistance_reduction))
        
        # Apply rampage bonus
        base_damage += attacker_stats.rampage_bonus
        
        # Minimum damage of 1
        final_damage = max(1, base_damage)
        
        return final_damage, is_critical, is_blocked
    
    @staticmethod
    def determine_damage_type(attacker_stats: CombatStats) -> DamageType:
        """Determine what type of damage to deal based on attacker's stats"""
        damage_sources = []
        
        if attacker_stats.attack > 0:
            damage_sources.append((DamageType.PHYSICAL, attacker_stats.attack))
        if attacker_stats.elemental_attack > 0:
            # Randomly choose elemental type
            elemental_types = [DamageType.FIRE, DamageType.KINETIC, DamageType.ARCANE, 
                             DamageType.HOLY, DamageType.SHADOW]
            damage_sources.append((random.choice(elemental_types), attacker_stats.elemental_attack))
        if attacker_stats.chaos_damage > 0:
            damage_sources.append((DamageType.CHAOS, attacker_stats.chaos_damage))
        if attacker_stats.vile_damage > 0:
            damage_sources.append((DamageType.VILE, attacker_stats.vile_damage))
        
        if not damage_sources:
            return DamageType.PHYSICAL
        
        # Weight selection by damage amount
        total_weight = sum(weight for _, weight in damage_sources)
        if total_weight == 0:
            return DamageType.PHYSICAL
        
        rand_value = random.randint(1, total_weight)
        current_weight = 0
        
        for damage_type, weight in damage_sources:
            current_weight += weight
            if rand_value <= current_weight:
                return damage_type
        
        return damage_sources[0][0]  # Fallback
    
    @staticmethod
    def simulate_combat(attacker_stats: CombatStats, attacker_name: str, attacker_id: str,
                       defender_stats: CombatStats, defender_name: str, defender_id: Optional[str]) -> CombatResult:
        """Simulate a complete combat encounter"""
        combat_log = []
        start_time = datetime.now()
        total_damage_dealt = 0
        total_damage_received = 0
        
        # Make copies to avoid modifying original stats
        attacker_hp = attacker_stats.current_hp
        defender_hp = defender_stats.current_hp
        
        # Combat loop - max 50 rounds to prevent infinite combat
        max_rounds = 50
        round_count = 0
        
        while attacker_hp > 0 and defender_hp > 0 and round_count < max_rounds:
            round_count += 1
            
            # Attacker's turn
            if attacker_hp > 0:
                damage_type = CombatEngine.determine_damage_type(attacker_stats)
                damage, is_critical, is_blocked = CombatEngine.calculate_damage(
                    attacker_stats, defender_stats, damage_type
                )
                
                if is_blocked:
                    action = CombatAction(
                        CombatActionType.BLOCK,
                        attacker_name, defender_name,
                        0, damage_type, False, True,
                        f"{defender_name} blocked {attacker_name}'s attack!"
                    )
                else:
                    actual_damage = min(damage, defender_hp)
                    defender_hp -= actual_damage
                    total_damage_dealt += actual_damage
                    
                    action_type = CombatActionType.CRITICAL if is_critical else CombatActionType.ATTACK
                    message = f"{attacker_name} hit {defender_name} for {actual_damage} {damage_type.value} damage!"
                    if is_critical:
                        message = f"{attacker_name} critically hit {defender_name} for {actual_damage} {damage_type.value} damage!"
                    
                    action = CombatAction(
                        action_type, attacker_name, defender_name,
                        actual_damage, damage_type, is_critical, False, message
                    )
                
                combat_log.append(action)
                
                if defender_hp <= 0:
                    combat_log.append(CombatAction(
                        CombatActionType.SPECIAL, attacker_name, defender_name,
                        0, DamageType.PHYSICAL, False, False,
                        f"{attacker_name} has defeated {defender_name}!"
                    ))
                    break
            
            # Defender's turn
            if defender_hp > 0:
                damage_type = CombatEngine.determine_damage_type(defender_stats)
                damage, is_critical, is_blocked = CombatEngine.calculate_damage(
                    defender_stats, attacker_stats, damage_type
                )
                
                if is_blocked:
                    action = CombatAction(
                        CombatActionType.BLOCK,
                        defender_name, attacker_name,
                        0, damage_type, False, True,
                        f"{attacker_name} blocked {defender_name}'s attack!"
                    )
                else:
                    actual_damage = min(damage, attacker_hp)
                    attacker_hp -= actual_damage
                    total_damage_received += actual_damage
                    
                    action_type = CombatActionType.CRITICAL if is_critical else CombatActionType.ATTACK
                    message = f"{defender_name} hit {attacker_name} for {actual_damage} {damage_type.value} damage!"
                    if is_critical:
                        message = f"{defender_name} critically hit {attacker_name} for {actual_damage} {damage_type.value} damage!"
                    
                    action = CombatAction(
                        action_type, defender_name, attacker_name,
                        actual_damage, damage_type, is_critical, False, message
                    )
                
                combat_log.append(action)
                
                if attacker_hp <= 0:
                    combat_log.append(CombatAction(
                        CombatActionType.SPECIAL, defender_name, attacker_name,
                        0, DamageType.PHYSICAL, False, False,
                        f"{defender_name} has defeated {attacker_name}!"
                    ))
                    break
        
        # Determine winner
        if attacker_hp > 0:
            winner_id = attacker_id
            winner_name = attacker_name
            loser_id = defender_id
            loser_name = defender_name
        elif defender_hp > 0:
            winner_id = defender_id
            winner_name = defender_name
            loser_id = attacker_id
            loser_name = attacker_name
        else:
            # Draw - attacker wins by default
            winner_id = attacker_id
            winner_name = attacker_name
            loser_id = defender_id
            loser_name = defender_name
        
        end_time = datetime.now()
        duration = int((end_time - start_time).total_seconds())
        
        # Calculate rewards (basic implementation)
        exp_gained = 0
        gold_gained = 0
        items_gained = []
        
        if winner_id == attacker_id:
            # Attacker won - calculate rewards based on defender level
            level_diff = max(1, defender_stats.level - attacker_stats.level + 10)
            exp_gained = level_diff * 10
            gold_gained = random.randint(1, 10)
        
        return CombatResult(
            winner_id=winner_id,
            winner_name=winner_name,
            loser_id=loser_id,
            loser_name=loser_name,
            combat_log=combat_log,
            duration_seconds=duration,
            total_damage_dealt=total_damage_dealt,
            total_damage_received=total_damage_received,
            exp_gained=exp_gained,
            gold_gained=gold_gained,
            items_gained=items_gained
        )