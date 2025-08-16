import asyncpg
import aiosql
from pathlib import Path

async def init_db(app):
    """Initialize database connection and queries"""
    config = app['config']
    
    # Create connection pool
    app['db'] = await asyncpg.create_pool(
        config.DATABASE_URL,
        min_size=5,
        max_size=20
    )
    
    # Load SQL queries
    queries_path = Path(__file__).parent / "sql"
    app['queries'] = aiosql.from_path(queries_path, "asyncpg")
    
    # Create tables if they don't exist
    await create_tables(app)

async def close_db(app):
    """Close database connections"""
    if 'db' in app:
        await app['db'].close()

async def create_tables(app):
    """Create all necessary tables"""
    db = app['db']
    
    async with db.acquire() as conn:
        # Create tables in order of dependencies
        await conn.execute("""
            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
            CREATE EXTENSION IF NOT EXISTS "citext";
        """)
        
        # Users/Accounts table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                username CITEXT UNIQUE NOT NULL,
                email CITEXT UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_preferred_player BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_login TIMESTAMP WITH TIME ZONE,
                points INTEGER DEFAULT 0,
                character_slots INTEGER DEFAULT 25
            );
        """)
        
        # Crews/Guilds table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS crews (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                leader_id UUID REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                vault_capacity INTEGER DEFAULT 100,
                has_two_way_vault BOOLEAN DEFAULT FALSE,
                member_limit INTEGER DEFAULT 20
            );
        """)
        
        # Characters table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                name VARCHAR(50) UNIQUE NOT NULL,
                character_class VARCHAR(20) NOT NULL CHECK (character_class IN ('gangster', 'monster', 'popstar')),
                level INTEGER DEFAULT 1 CHECK (level >= 1 AND level <= 95),
                experience BIGINT DEFAULT 0,
                experience_yesterday INTEGER DEFAULT 0,
                
                -- Combat stats
                attack INTEGER DEFAULT 10,
                hit_points INTEGER DEFAULT 100,
                current_hp INTEGER DEFAULT 100,
                chaos_damage INTEGER DEFAULT 0,
                vile_damage INTEGER DEFAULT 0,
                elemental_attack INTEGER DEFAULT 0,
                elemental_resist INTEGER DEFAULT 0,
                wilderness_level INTEGER DEFAULT 0,
                god_slayer_level INTEGER DEFAULT 0,
                
                -- Resistances
                fire_resist INTEGER DEFAULT 0,
                kinetic_resist INTEGER DEFAULT 0,
                arcane_resist INTEGER DEFAULT 0,
                holy_resist INTEGER DEFAULT 0,
                shadow_resist INTEGER DEFAULT 0,
                
                -- Resources
                gold BIGINT DEFAULT 100,
                rage INTEGER DEFAULT 0,
                max_rage INTEGER DEFAULT 1000,
                rage_per_hour INTEGER DEFAULT 50,
                exp_per_hour INTEGER DEFAULT 50,
                gold_per_turn INTEGER DEFAULT 0,
                
                -- Combat bonuses
                critical_hit_chance DECIMAL(5,2) DEFAULT 0,
                rampage_bonus INTEGER DEFAULT 0,
                
                -- Social
                parent_id UUID REFERENCES characters(id) ON DELETE SET NULL,
                faction VARCHAR(20) CHECK (faction IN ('alvar', 'delruk', 'vordyn') OR faction IS NULL),
                crew_id UUID REFERENCES crews(id) ON DELETE SET NULL,
                crew_rank VARCHAR(20) DEFAULT 'member',
                
                -- Faction loyalty (0-10 for each faction)
                alvar_loyalty INTEGER DEFAULT 0 CHECK (alvar_loyalty >= 0 AND alvar_loyalty <= 10),
                delruk_loyalty INTEGER DEFAULT 0 CHECK (delruk_loyalty >= 0 AND delruk_loyalty <= 10),
                vordyn_loyalty INTEGER DEFAULT 0 CHECK (vordyn_loyalty >= 0 AND vordyn_loyalty <= 10),
                
                -- Location
                current_room_id UUID,
                current_zone VARCHAR(50) DEFAULT 'diamond_city',
                
                -- Timestamps
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_resource_update TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                faction_change_last_used TIMESTAMP WITH TIME ZONE,
                
                UNIQUE(user_id, name)
            );
        """)
        
        # World zones and rooms
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS zones (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                min_level INTEGER DEFAULT 1,
                zone_type VARCHAR(30) DEFAULT 'normal'
            );
            
            CREATE TABLE IF NOT EXISTS rooms (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                zone_id UUID NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
                room_number INTEGER,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                room_type VARCHAR(30) DEFAULT 'normal',
                has_npcs BOOLEAN DEFAULT FALSE,
                has_shops BOOLEAN DEFAULT FALSE,
                is_safe BOOLEAN DEFAULT TRUE,
                exits JSONB DEFAULT '{}',
                special_features JSONB DEFAULT '{}'
            );
        """)
        
        # Items and equipment
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS item_templates (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name VARCHAR(100) NOT NULL,
                item_type VARCHAR(30) NOT NULL,
                slot VARCHAR(20),
                rarity VARCHAR(20) DEFAULT 'elite',
                level_requirement INTEGER DEFAULT 1,
                
                -- Base stats
                attack_bonus INTEGER DEFAULT 0,
                hp_bonus INTEGER DEFAULT 0,
                chaos_damage_bonus INTEGER DEFAULT 0,
                vile_damage_bonus INTEGER DEFAULT 0,
                elemental_attack_bonus INTEGER DEFAULT 0,
                
                -- Resistances
                fire_resist_bonus INTEGER DEFAULT 0,
                kinetic_resist_bonus INTEGER DEFAULT 0,
                arcane_resist_bonus INTEGER DEFAULT 0,
                holy_resist_bonus INTEGER DEFAULT 0,
                shadow_resist_bonus INTEGER DEFAULT 0,
                elemental_resist_bonus INTEGER DEFAULT 0,
                
                -- Resource generation
                rage_per_hour_bonus INTEGER DEFAULT 0,
                exp_per_hour_bonus INTEGER DEFAULT 0,
                gold_per_turn_bonus INTEGER DEFAULT 0,
                max_rage_bonus INTEGER DEFAULT 0,
                
                -- Combat bonuses
                critical_hit_bonus DECIMAL(5,2) DEFAULT 0,
                rampage_bonus INTEGER DEFAULT 0,
                
                -- Meta properties
                can_transfer BOOLEAN DEFAULT TRUE,
                max_transfers_per_day INTEGER DEFAULT 3,
                is_raidbound BOOLEAN DEFAULT FALSE,
                
                description TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Character items (instances of item templates)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS character_items (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
                item_template_id UUID NOT NULL REFERENCES item_templates(id),
                
                -- Item state
                equipped_slot VARCHAR(20),
                is_equipped BOOLEAN DEFAULT FALSE,
                inventory_position INTEGER,
                
                -- Transfer tracking
                transfers_today INTEGER DEFAULT 0,
                last_transfer_date DATE DEFAULT CURRENT_DATE,
                transfer_history JSONB DEFAULT '[]',
                
                -- Augments and modifications
                augments JSONB DEFAULT '[]',
                custom_stats JSONB DEFAULT '{}',
                
                acquired_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Crew vault items
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS crew_vault_items (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                crew_id UUID NOT NULL REFERENCES crews(id) ON DELETE CASCADE,
                item_template_id UUID NOT NULL REFERENCES item_templates(id),
                deposited_by UUID REFERENCES characters(id) ON DELETE SET NULL,
                vault_position INTEGER,
                deposited_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                -- Item state (same as character items)
                augments JSONB DEFAULT '[]',
                custom_stats JSONB DEFAULT '{}'
            );
        """)
        
        # NPCs
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS npcs (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name VARCHAR(100) NOT NULL,
                npc_type VARCHAR(30) DEFAULT 'enemy',
                level INTEGER DEFAULT 1,
                room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
                
                -- Combat stats (same structure as characters)
                attack INTEGER DEFAULT 10,
                hit_points INTEGER DEFAULT 100,
                max_hp INTEGER DEFAULT 100,
                chaos_damage INTEGER DEFAULT 0,
                vile_damage INTEGER DEFAULT 0,
                elemental_attack INTEGER DEFAULT 0,
                
                -- Resistances
                fire_resist INTEGER DEFAULT 0,
                kinetic_resist INTEGER DEFAULT 0,
                arcane_resist INTEGER DEFAULT 0,
                holy_resist INTEGER DEFAULT 0,
                shadow_resist INTEGER DEFAULT 0,
                elemental_resist INTEGER DEFAULT 0,
                
                -- Loot and rewards
                gold_reward INTEGER DEFAULT 0,
                exp_reward INTEGER DEFAULT 0,
                loot_table JSONB DEFAULT '[]',
                
                -- Respawn
                respawn_time INTEGER DEFAULT 3600,
                last_killed TIMESTAMP WITH TIME ZONE,
                
                -- Special properties
                is_boss BOOLEAN DEFAULT FALSE,
                is_raid_boss BOOLEAN DEFAULT FALSE,
                faction_requirement VARCHAR(20),
                
                description TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Combat logs
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS combat_logs (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                attacker_id UUID REFERENCES characters(id) ON DELETE SET NULL,
                defender_id UUID REFERENCES characters(id) ON DELETE SET NULL,
                npc_id UUID REFERENCES npcs(id) ON DELETE SET NULL,
                
                combat_type VARCHAR(20) NOT NULL CHECK (combat_type IN ('pvp', 'pve')),
                winner_id UUID,
                
                -- Combat details
                log_entries JSONB NOT NULL DEFAULT '[]',
                total_damage_dealt INTEGER DEFAULT 0,
                total_damage_received INTEGER DEFAULT 0,
                duration_seconds INTEGER,
                
                -- Rewards
                exp_gained INTEGER DEFAULT 0,
                gold_gained INTEGER DEFAULT 0,
                items_gained JSONB DEFAULT '[]',
                
                started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                ended_at TIMESTAMP WITH TIME ZONE
            );
        """)
        
        # Quests
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS quest_templates (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name VARCHAR(100) NOT NULL,
                description TEXT,
                quest_type VARCHAR(30) DEFAULT 'kill',
                
                -- Requirements
                min_level INTEGER DEFAULT 1,
                required_faction VARCHAR(20),
                prerequisite_quests JSONB DEFAULT '[]',
                
                -- Objectives
                objectives JSONB NOT NULL DEFAULT '[]',
                
                -- Rewards
                exp_reward INTEGER DEFAULT 0,
                gold_reward INTEGER DEFAULT 0,
                item_rewards JSONB DEFAULT '[]',
                faction_loyalty_reward JSONB DEFAULT '{}',
                
                -- Quest availability
                is_daily BOOLEAN DEFAULT FALSE,
                is_repeatable BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE TABLE IF NOT EXISTS character_quests (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
                quest_template_id UUID NOT NULL REFERENCES quest_templates(id),
                
                status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'failed', 'abandoned')),
                progress JSONB DEFAULT '{}',
                
                started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                completed_at TIMESTAMP WITH TIME ZONE,
                
                UNIQUE(character_id, quest_template_id)
            );
        """)
        
        # Personal allies/enemies
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS character_relationships (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
                target_character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
                relationship_type VARCHAR(20) NOT NULL CHECK (relationship_type IN ('ally', 'enemy', 'blocked')),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                
                UNIQUE(character_id, target_character_id)
            );
        """)
        
        # Sessions and authentication
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                token_hash VARCHAR(255) NOT NULL,
                expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_used TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                ip_address INET,
                user_agent TEXT
            );
        """)
        
        # Game events and logs
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS game_events (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                event_type VARCHAR(50) NOT NULL,
                character_id UUID REFERENCES characters(id) ON DELETE SET NULL,
                target_character_id UUID REFERENCES characters(id) ON DELETE SET NULL,
                crew_id UUID REFERENCES crews(id) ON DELETE SET NULL,
                
                event_data JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Create indexes for performance
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_characters_user_id ON characters(user_id);
            CREATE INDEX IF NOT EXISTS idx_characters_crew_id ON characters(crew_id);
            CREATE INDEX IF NOT EXISTS idx_characters_faction ON characters(faction);
            CREATE INDEX IF NOT EXISTS idx_characters_level ON characters(level);
            CREATE INDEX IF NOT EXISTS idx_characters_current_room ON characters(current_room_id);
            CREATE INDEX IF NOT EXISTS idx_character_items_character_id ON character_items(character_id);
            CREATE INDEX IF NOT EXISTS idx_character_items_equipped ON character_items(character_id, is_equipped);
            CREATE INDEX IF NOT EXISTS idx_crew_vault_items_crew_id ON crew_vault_items(crew_id);
            CREATE INDEX IF NOT EXISTS idx_npcs_room_id ON npcs(room_id);
            CREATE INDEX IF NOT EXISTS idx_combat_logs_participants ON combat_logs(attacker_id, defender_id);
            CREATE INDEX IF NOT EXISTS idx_character_quests_character_id ON character_quests(character_id);
            CREATE INDEX IF NOT EXISTS idx_character_quests_status ON character_quests(character_id, status);
            CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
            CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(token_hash);
            CREATE INDEX IF NOT EXISTS idx_game_events_character_id ON game_events(character_id);
            CREATE INDEX IF NOT EXISTS idx_game_events_type_time ON game_events(event_type, created_at);
        """)

async def get_db_connection(app):
    """Get a database connection from the pool"""
    return app['db'].acquire()