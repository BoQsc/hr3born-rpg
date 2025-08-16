import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/outwar_game')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET = os.getenv('JWT_SECRET', 'dev-jwt-secret')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', 8000))
    
    # Game configuration
    MAX_LEVEL = 95
    MAX_CHARACTERS_PER_ACCOUNT = 25
    RESOURCE_GENERATION_INTERVAL = 3600  # 1 hour in seconds
    COMBAT_TIMEOUT = 30  # seconds
    CREW_VAULT_MAX_ITEMS = 100
    DAILY_HAND_CHANGE_LIMIT = 3
    
    # Character classes
    CHARACTER_CLASSES = {
        'gangster': {
            'name': 'Gangster',
            'attack_bonus': 5,
            'defense_bonus': 10,
            'rage_bonus': 0,
            'max_rage_bonus': 0
        },
        'monster': {
            'name': 'Monster',
            'attack_bonus': 0,
            'defense_bonus': 0,
            'rage_bonus': 5,
            'max_rage_bonus': 10
        },
        'popstar': {
            'name': 'Pop Star',
            'attack_bonus': 2.5,
            'defense_bonus': 5,
            'rage_bonus': 2.5,
            'max_rage_bonus': 5
        }
    }
    
    # Faction system
    FACTIONS = {
        'alvar': {
            'name': 'Alvar Liberation',
            'description': 'Survivors of the Astral Dimension war',
            'bonus_type': 'elemental_damage',
            'bonus_per_loyalty': 1
        },
        'delruk': {
            'name': 'Delruk Alliance',
            'description': 'Members of Diamond City and nearby lands',
            'bonus_type': 'attack_vile',
            'bonus_per_loyalty': 2
        },
        'vordyn': {
            'name': 'Vordyn Rebellion',
            'description': 'Formed on Veldara during Thanox\'s reign',
            'bonus_type': 'chaos_damage',
            'bonus_per_loyalty': 2
        }
    }
    
    # Item rarity tiers
    ITEM_RARITY = ['elite', 'brutal', 'godly', 'king', 'mythic']
    
    # Element types
    ELEMENTS = ['fire', 'kinetic', 'arcane', 'holy', 'shadow']