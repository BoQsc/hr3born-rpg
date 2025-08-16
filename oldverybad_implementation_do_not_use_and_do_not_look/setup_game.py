#!/usr/bin/env python3
"""
Setup script for Outwar RPG Game
Creates initial game data including zones, rooms, NPCs, and items
"""

import asyncio
import asyncpg
from config import Config

async def create_initial_zones(conn):
    """Create initial game zones"""
    zones = [
        {
            'name': 'Diamond City',
            'description': 'The main hub city with training grounds and essential services',
            'min_level': 1,
            'zone_type': 'city'
        },
        {
            'name': 'Wastelands',
            'description': 'Dangerous areas outside the city with hostile creatures',
            'min_level': 10,
            'zone_type': 'wilderness'
        },
        {
            'name': 'Fire Dimension',
            'description': 'Elemental plane of fire - high level content',
            'min_level': 90,
            'zone_type': 'elemental'
        }
    ]
    
    zone_ids = {}
    
    for zone in zones:
        result = await conn.fetchrow(
            """INSERT INTO zones (name, description, min_level, zone_type) 
               VALUES ($1, $2, $3, $4) 
               ON CONFLICT (name) DO UPDATE SET 
               description = EXCLUDED.description,
               min_level = EXCLUDED.min_level,
               zone_type = EXCLUDED.zone_type
               RETURNING id""",
            zone['name'], zone['description'], zone['min_level'], zone['zone_type']
        )
        zone_ids[zone['name']] = str(result['id'])
    
    print("✓ Created initial zones")
    return zone_ids

async def create_initial_rooms(conn, zone_ids):
    """Create initial rooms in zones"""
    rooms = [
        {
            'zone': 'Diamond City',
            'room_number': 1,
            'name': 'Training Ground',
            'description': 'A safe area for new characters to learn combat basics',
            'room_type': 'training',
            'has_npcs': True,
            'has_shops': False,
            'is_safe': True,
            'exits': {'north': 2, 'east': 3},
            'special_features': {'training_dummies': True}
        },
        {
            'zone': 'Diamond City',
            'room_number': 2,
            'name': 'City Hall',
            'description': 'The administrative center of Diamond City',
            'room_type': 'government',
            'has_npcs': True,
            'has_shops': False,
            'is_safe': True,
            'exits': {'south': 1, 'west': 4},
            'special_features': {'faction_npc': True}
        },
        {
            'zone': 'Diamond City',
            'room_number': 3,
            'name': 'Underground Casino',
            'description': 'The infamous underground gambling establishment',
            'room_type': 'casino',
            'has_npcs': True,
            'has_shops': False,
            'is_safe': False,
            'exits': {'west': 1, 'down': 5},
            'special_features': {'gambling': True, 'pvp_allowed': True}
        },
        {
            'zone': 'Diamond City',
            'room_number': 4,
            'name': 'Equipment Shop',
            'description': 'A shop selling basic equipment and supplies',
            'room_type': 'shop',
            'has_npcs': True,
            'has_shops': True,
            'is_safe': True,
            'exits': {'east': 2},
            'special_features': {'shop_type': 'equipment'}
        },
        {
            'zone': 'Diamond City',
            'room_number': 5,
            'name': 'Fight Arena',
            'description': 'Where warriors come to test their skills in combat',
            'room_type': 'arena',
            'has_npcs': True,
            'has_shops': False,
            'is_safe': False,
            'exits': {'up': 3},
            'special_features': {'arena_battles': True, 'pvp_encouraged': True}
        }
    ]
    
    room_ids = {}
    
    for room in rooms:
        zone_id = zone_ids[room['zone']]
        result = await conn.fetchrow(
            """INSERT INTO rooms (zone_id, room_number, name, description, room_type, 
                                 has_npcs, has_shops, is_safe, exits, special_features) 
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) 
               ON CONFLICT (zone_id, room_number) DO UPDATE SET 
               name = EXCLUDED.name,
               description = EXCLUDED.description,
               room_type = EXCLUDED.room_type,
               has_npcs = EXCLUDED.has_npcs,
               has_shops = EXCLUDED.has_shops,
               is_safe = EXCLUDED.is_safe,
               exits = EXCLUDED.exits,
               special_features = EXCLUDED.special_features
               RETURNING id""",
            zone_id, room['room_number'], room['name'], room['description'],
            room['room_type'], room['has_npcs'], room['has_shops'], room['is_safe'],
            room['exits'], room['special_features']
        )
        room_key = f"{room['zone']}-{room['room_number']}"
        room_ids[room_key] = str(result['id'])
    
    print("✓ Created initial rooms")
    return room_ids

async def create_initial_npcs(conn, room_ids):
    """Create initial NPCs"""
    npcs = [
        {
            'name': 'Training Dummy',
            'npc_type': 'training',
            'level': 1,
            'room': 'Diamond City-1',
            'attack': 5,
            'hit_points': 50,
            'gold_reward': 2,
            'exp_reward': 10,
            'respawn_time': 60,
            'description': 'A practice dummy for combat training'
        },
        {
            'name': 'Sparring Partner',
            'npc_type': 'training',
            'level': 5,
            'room': 'Diamond City-1',
            'attack': 15,
            'hit_points': 150,
            'gold_reward': 5,
            'exp_reward': 25,
            'respawn_time': 300,
            'description': 'A more challenging training opponent'
        },
        {
            'name': 'High Roller',
            'npc_type': 'enemy',
            'level': 20,
            'room': 'Diamond City-3',
            'attack': 80,
            'hit_points': 400,
            'chaos_damage': 20,
            'gold_reward': 20,
            'exp_reward': 100,
            'respawn_time': 1800,
            'description': 'A dangerous gambler who doesn\'t like to lose'
        },
        {
            'name': 'The Boss',
            'npc_type': 'boss',
            'level': 22,
            'room': 'Diamond City-3',
            'attack': 120,
            'hit_points': 800,
            'chaos_damage': 50,
            'vile_damage': 30,
            'gold_reward': 100,
            'exp_reward': 500,
            'respawn_time': 3600,
            'is_boss': True,
            'description': 'The notorious boss of the underground casino'
        },
        {
            'name': 'Arena Champion',
            'npc_type': 'boss',
            'level': 25,
            'room': 'Diamond City-5',
            'attack': 150,
            'hit_points': 1000,
            'elemental_attack': 75,
            'fire_resist': 100,
            'kinetic_resist': 100,
            'gold_reward': 150,
            'exp_reward': 750,
            'respawn_time': 7200,
            'is_boss': True,
            'description': 'The undefeated champion of the fight arena'
        }
    ]
    
    for npc in npcs:
        room_id = room_ids[npc['room']]
        await conn.execute(
            """INSERT INTO npcs (name, npc_type, level, room_id, attack, hit_points, max_hp,
                               chaos_damage, vile_damage, elemental_attack,
                               fire_resist, kinetic_resist, arcane_resist, holy_resist, shadow_resist,
                               elemental_resist, gold_reward, exp_reward, loot_table,
                               respawn_time, is_boss, is_raid_boss, description) 
               VALUES ($1, $2, $3, $4, $5, $6, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22)
               ON CONFLICT (name, room_id) DO UPDATE SET
               npc_type = EXCLUDED.npc_type,
               level = EXCLUDED.level,
               attack = EXCLUDED.attack,
               hit_points = EXCLUDED.hit_points,
               max_hp = EXCLUDED.max_hp,
               chaos_damage = EXCLUDED.chaos_damage,
               vile_damage = EXCLUDED.vile_damage,
               elemental_attack = EXCLUDED.elemental_attack,
               gold_reward = EXCLUDED.gold_reward,
               exp_reward = EXCLUDED.exp_reward,
               respawn_time = EXCLUDED.respawn_time,
               is_boss = EXCLUDED.is_boss,
               description = EXCLUDED.description""",
            npc['name'], npc['npc_type'], npc['level'], room_id,
            npc['attack'], npc['hit_points'],
            npc.get('chaos_damage', 0), npc.get('vile_damage', 0), npc.get('elemental_attack', 0),
            npc.get('fire_resist', 0), npc.get('kinetic_resist', 0), npc.get('arcane_resist', 0),
            npc.get('holy_resist', 0), npc.get('shadow_resist', 0), npc.get('elemental_resist', 0),
            npc['gold_reward'], npc['exp_reward'], [],
            npc['respawn_time'], npc.get('is_boss', False), False, npc['description']
        )
    
    print("✓ Created initial NPCs")

async def create_initial_items(conn):
    """Create initial item templates"""
    items = [
        # Weapons
        {
            'name': 'Training Sword',
            'item_type': 'weapon',
            'slot': 'weapon',
            'rarity': 'elite',
            'level_requirement': 1,
            'attack_bonus': 10,
            'description': 'A basic sword for new warriors'
        },
        {
            'name': 'Steel Blade',
            'item_type': 'weapon',
            'slot': 'weapon',
            'rarity': 'brutal',
            'level_requirement': 10,
            'attack_bonus': 25,
            'critical_hit_bonus': 2.0,
            'description': 'A well-crafted steel sword with sharp edges'
        },
        {
            'name': 'War Shattered Grenade Launcher',
            'item_type': 'weapon',
            'slot': 'weapon',
            'rarity': 'godly',
            'level_requirement': 50,
            'attack_bonus': 250,
            'rage_per_hour_bonus': 100,
            'exp_per_hour_bonus': 50,
            'rampage_bonus': 50,
            'max_rage_bonus': 1200,
            'critical_hit_bonus': 6.0,
            'description': 'A devastating weapon of war'
        },
        
        # Armor
        {
            'name': 'Cloth Shirt',
            'item_type': 'chest',
            'slot': 'chest',
            'rarity': 'elite',
            'level_requirement': 1,
            'hp_bonus': 25,
            'description': 'Basic cloth protection'
        },
        {
            'name': 'Leather Armor',
            'item_type': 'chest',
            'slot': 'chest',
            'rarity': 'brutal',
            'level_requirement': 5,
            'hp_bonus': 75,
            'fire_resist_bonus': 10,
            'kinetic_resist_bonus': 10,
            'description': 'Sturdy leather armor with basic protection'
        },
        {
            'name': 'Black Kings Guard',
            'item_type': 'chest',
            'slot': 'chest',
            'rarity': 'king',
            'level_requirement': 40,
            'elemental_attack_bonus': 75,
            'hp_bonus': 775,
            'holy_resist_bonus': 55,
            'arcane_resist_bonus': 55,
            'fire_resist_bonus': 55,
            'kinetic_resist_bonus': 55,
            'shadow_resist_bonus': 55,
            'gold_per_turn_bonus': 333,
            'rage_per_hour_bonus': 395,
            'exp_per_hour_bonus': 315,
            'rampage_bonus': 50,
            'max_rage_bonus': 4343,
            'critical_hit_bonus': 13.0,
            'description': 'Legendary armor of the Black King\'s elite guard'
        },
        
        # Accessories
        {
            'name': 'Basic Ring',
            'item_type': 'ring',
            'slot': 'ring',
            'rarity': 'elite',
            'level_requirement': 1,
            'attack_bonus': 5,
            'hp_bonus': 10,
            'description': 'A simple ring with minor enchantments'
        },
        {
            'name': 'Power Amulet',
            'item_type': 'accessory',
            'slot': 'accessory',
            'rarity': 'brutal',
            'level_requirement': 15,
            'elemental_attack_bonus': 30,
            'max_rage_bonus': 200,
            'rage_per_hour_bonus': 25,
            'description': 'An amulet pulsing with magical energy'
        },
        
        # Boots
        {
            'name': 'Leather Boots',
            'item_type': 'boots',
            'slot': 'boots',
            'rarity': 'elite',
            'level_requirement': 1,
            'hp_bonus': 15,
            'description': 'Comfortable leather boots for adventuring'
        },
        {
            'name': 'Speed Boots',
            'item_type': 'boots',
            'slot': 'boots',
            'rarity': 'godly',
            'level_requirement': 30,
            'hp_bonus': 150,
            'rage_per_hour_bonus': 50,
            'exp_per_hour_bonus': 50,
            'description': 'Enchanted boots that increase movement and energy'
        }
    ]
    
    for item in items:
        await conn.execute(
            """INSERT INTO item_templates (
                name, item_type, slot, rarity, level_requirement,
                attack_bonus, hp_bonus, chaos_damage_bonus, vile_damage_bonus, elemental_attack_bonus,
                fire_resist_bonus, kinetic_resist_bonus, arcane_resist_bonus, holy_resist_bonus, shadow_resist_bonus,
                elemental_resist_bonus, rage_per_hour_bonus, exp_per_hour_bonus, gold_per_turn_bonus,
                max_rage_bonus, critical_hit_bonus, rampage_bonus,
                can_transfer, max_transfers_per_day, is_raidbound, description
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26)
            ON CONFLICT (name) DO UPDATE SET
            item_type = EXCLUDED.item_type,
            slot = EXCLUDED.slot,
            rarity = EXCLUDED.rarity,
            level_requirement = EXCLUDED.level_requirement,
            attack_bonus = EXCLUDED.attack_bonus,
            hp_bonus = EXCLUDED.hp_bonus,
            description = EXCLUDED.description""",
            item['name'], item['item_type'], item['slot'], item['rarity'], item['level_requirement'],
            item.get('attack_bonus', 0), item.get('hp_bonus', 0), item.get('chaos_damage_bonus', 0),
            item.get('vile_damage_bonus', 0), item.get('elemental_attack_bonus', 0),
            item.get('fire_resist_bonus', 0), item.get('kinetic_resist_bonus', 0),
            item.get('arcane_resist_bonus', 0), item.get('holy_resist_bonus', 0),
            item.get('shadow_resist_bonus', 0), item.get('elemental_resist_bonus', 0),
            item.get('rage_per_hour_bonus', 0), item.get('exp_per_hour_bonus', 0),
            item.get('gold_per_turn_bonus', 0), item.get('max_rage_bonus', 0),
            item.get('critical_hit_bonus', 0.0), item.get('rampage_bonus', 0),
            item.get('can_transfer', True), item.get('max_transfers_per_day', 3),
            item.get('is_raidbound', False), item['description']
        )
    
    print("✓ Created initial item templates")

async def setup_game():
    """Main setup function"""
    print("🎮 Setting up Outwar RPG Game...")
    
    # Connect to database
    conn = await asyncpg.connect(Config.DATABASE_URL)
    
    try:
        # Create initial game data
        zone_ids = await create_initial_zones(conn)
        room_ids = await create_initial_rooms(conn, zone_ids)
        await create_initial_npcs(conn, room_ids)
        await create_initial_items(conn)
        
        print("\n✅ Game setup completed successfully!")
        print("\nYou can now:")
        print("1. Run the game server: python main.py")
        print("2. Visit http://127.0.0.1:8000 to play")
        print("3. Register a new account and create your first character")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        raise
    
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(setup_game())