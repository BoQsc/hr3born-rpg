from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
from config import Config

@dataclass
class Character:
    id: str
    user_id: str
    name: str
    character_class: str
    level: int
    experience: int
    experience_yesterday: int
    
    # Combat stats
    attack: int
    hit_points: int
    current_hp: int
    chaos_damage: int
    vile_damage: int
    elemental_attack: int
    elemental_resist: int
    wilderness_level: int
    god_slayer_level: int
    
    # Resistances
    fire_resist: int
    kinetic_resist: int
    arcane_resist: int
    holy_resist: int
    shadow_resist: int
    
    # Resources
    gold: int
    rage: int
    max_rage: int
    rage_per_hour: int
    exp_per_hour: int
    gold_per_turn: int
    
    # Combat bonuses
    critical_hit_chance: float
    rampage_bonus: int
    
    # Social
    parent_id: Optional[str]
    faction: Optional[str]
    crew_id: Optional[str]
    crew_rank: str
    
    # Faction loyalty
    alvar_loyalty: int
    delruk_loyalty: int
    vordyn_loyalty: int
    
    # Location
    current_room_id: Optional[str]
    current_zone: str
    
    # Timestamps
    created_at: datetime
    last_active: datetime
    last_resource_update: datetime
    faction_change_last_used: Optional[datetime]
    
    def calculate_total_power(self) -> int:
        """Calculate total character power rating"""
        return (self.attack + self.hit_points + self.chaos_damage + 
                self.vile_damage + self.elemental_attack +
                self.fire_resist + self.kinetic_resist + self.arcane_resist +
                self.holy_resist + self.shadow_resist +
                self.max_rage // 10 + int(self.critical_hit_chance * 10) + 
                self.rampage_bonus)
    
    def get_class_bonuses(self) -> Dict[str, float]:
        """Get class-specific stat bonuses"""
        return Config.CHARACTER_CLASSES.get(self.character_class, {})
    
    def get_faction_bonuses(self) -> Dict[str, Any]:
        """Get faction-specific bonuses"""
        if not self.faction:
            return {}
        
        faction_config = Config.FACTIONS.get(self.faction, {})
        loyalty = getattr(self, f"{self.faction}_loyalty", 0)
        
        return {
            'bonus_type': faction_config.get('bonus_type'),
            'bonus_amount': faction_config.get('bonus_per_loyalty', 0) * loyalty,
            'loyalty': loyalty
        }
    
    def can_change_faction(self) -> bool:
        """Check if character can change faction"""
        if not self.faction_change_last_used:
            return True
        
        # Can change once per month for free
        now = datetime.now()
        days_since_change = (now - self.faction_change_last_used).days
        return days_since_change >= 30
    
    def calculate_experience_for_level(self, target_level: int) -> int:
        """Calculate experience required for target level"""
        # Simple exponential formula - can be adjusted
        return int(1000 * (target_level ** 2.2))
    
    def get_next_level_experience(self) -> int:
        """Get experience required for next level"""
        if self.level >= Config.MAX_LEVEL:
            return 0
        return self.calculate_experience_for_level(self.level + 1)
    
    def can_level_up(self) -> bool:
        """Check if character has enough experience to level up"""
        if self.level >= Config.MAX_LEVEL:
            return False
        return self.experience >= self.get_next_level_experience()
    
    def is_alive(self) -> bool:
        """Check if character is alive"""
        return self.current_hp > 0
    
    def get_health_percentage(self) -> float:
        """Get health as percentage"""
        return (self.current_hp / self.hit_points) * 100 if self.hit_points > 0 else 0
    
    def can_enter_faction_content(self) -> bool:
        """Check if character can access faction content"""
        return self.level >= 91 and self.faction is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert character to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'character_class': self.character_class,
            'level': self.level,
            'experience': self.experience,
            'experience_yesterday': self.experience_yesterday,
            'total_power': self.calculate_total_power(),
            
            'combat_stats': {
                'attack': self.attack,
                'hit_points': self.hit_points,
                'current_hp': self.current_hp,
                'chaos_damage': self.chaos_damage,
                'vile_damage': self.vile_damage,
                'elemental_attack': self.elemental_attack,
                'elemental_resist': self.elemental_resist,
                'wilderness_level': self.wilderness_level,
                'god_slayer_level': self.god_slayer_level
            },
            
            'resistances': {
                'fire_resist': self.fire_resist,
                'kinetic_resist': self.kinetic_resist,
                'arcane_resist': self.arcane_resist,
                'holy_resist': self.holy_resist,
                'shadow_resist': self.shadow_resist
            },
            
            'resources': {
                'gold': self.gold,
                'rage': self.rage,
                'max_rage': self.max_rage,
                'rage_per_hour': self.rage_per_hour,
                'exp_per_hour': self.exp_per_hour,
                'gold_per_turn': self.gold_per_turn
            },
            
            'combat_bonuses': {
                'critical_hit_chance': self.critical_hit_chance,
                'rampage_bonus': self.rampage_bonus
            },
            
            'social': {
                'parent_id': self.parent_id,
                'faction': self.faction,
                'crew_id': self.crew_id,
                'crew_rank': self.crew_rank,
                'faction_bonuses': self.get_faction_bonuses()
            },
            
            'faction_loyalty': {
                'alvar_loyalty': self.alvar_loyalty,
                'delruk_loyalty': self.delruk_loyalty,
                'vordyn_loyalty': self.vordyn_loyalty
            },
            
            'location': {
                'current_room_id': self.current_room_id,
                'current_zone': self.current_zone
            },
            
            'timestamps': {
                'created_at': self.created_at.isoformat(),
                'last_active': self.last_active.isoformat(),
                'last_resource_update': self.last_resource_update.isoformat(),
                'faction_change_last_used': self.faction_change_last_used.isoformat() if self.faction_change_last_used else None
            }
        }

@dataclass
class CharacterCreationRequest:
    name: str
    character_class: str
    
    def validate(self) -> tuple[bool, str]:
        """Validate character creation request"""
        if not self.name or len(self.name) < 3 or len(self.name) > 50:
            return False, "Character name must be between 3 and 50 characters"
        
        if not self.name.replace('_', '').replace('-', '').isalnum():
            return False, "Character name can only contain letters, numbers, hyphens, and underscores"
        
        if self.character_class not in Config.CHARACTER_CLASSES:
            return False, f"Invalid character class. Must be one of: {list(Config.CHARACTER_CLASSES.keys())}"
        
        return True, ""

def create_starting_character(user_id: str, request: CharacterCreationRequest) -> Character:
    """Create a new character with starting stats"""
    class_config = Config.CHARACTER_CLASSES[request.character_class]
    now = datetime.now()
    
    # Base starting stats
    base_attack = 10
    base_hp = 100
    base_max_rage = 1000
    
    # Apply class bonuses
    attack = int(base_attack * (1 + class_config['attack_bonus'] / 100))
    hp = int(base_hp * (1 + class_config['defense_bonus'] / 100))
    max_rage = int(base_max_rage * (1 + class_config['max_rage_bonus'] / 100))
    
    return Character(
        id="",  # Will be set by database
        user_id=user_id,
        name=request.name,
        character_class=request.character_class,
        level=1,
        experience=0,
        experience_yesterday=0,
        
        # Combat stats
        attack=attack,
        hit_points=hp,
        current_hp=hp,
        chaos_damage=0,
        vile_damage=0,
        elemental_attack=0,
        elemental_resist=0,
        wilderness_level=0,
        god_slayer_level=0,
        
        # Resistances
        fire_resist=0,
        kinetic_resist=0,
        arcane_resist=0,
        holy_resist=0,
        shadow_resist=0,
        
        # Resources
        gold=100,
        rage=0,
        max_rage=max_rage,
        rage_per_hour=int(50 * (1 + class_config['rage_bonus'] / 100)),
        exp_per_hour=50,
        gold_per_turn=0,
        
        # Combat bonuses
        critical_hit_chance=0.0,
        rampage_bonus=0,
        
        # Social
        parent_id=None,
        faction=None,
        crew_id=None,
        crew_rank='member',
        
        # Faction loyalty
        alvar_loyalty=0,
        delruk_loyalty=0,
        vordyn_loyalty=0,
        
        # Location
        current_room_id=None,  # Will be set to starting room
        current_zone='diamond_city',
        
        # Timestamps
        created_at=now,
        last_active=now,
        last_resource_update=now,
        faction_change_last_used=None
    )