-- Core database schema for Outwar-style MMORPG

-- User accounts (RGA system)
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_preferred BOOLEAN DEFAULT 0
);

-- Character classes
CREATE TABLE IF NOT EXISTS character_classes (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    attack_bonus REAL DEFAULT 0.0,
    defense_bonus REAL DEFAULT 0.0,
    rage_per_turn_bonus REAL DEFAULT 0.0,
    max_rage_bonus REAL DEFAULT 0.0
);

-- Insert default classes
INSERT OR IGNORE INTO character_classes (id, name, attack_bonus, defense_bonus, rage_per_turn_bonus, max_rage_bonus) VALUES
(1, 'Gangster', 0.05, 0.10, 0.0, 0.0),
(2, 'Monster', 0.0, 0.0, 0.05, 0.10),
(3, 'Pop Star', 0.025, 0.05, 0.025, 0.05);

-- Factions (unlocked at level 91)
CREATE TABLE IF NOT EXISTS factions (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    damage_type TEXT,
    bonus_per_loyalty REAL DEFAULT 0.0
);

INSERT OR IGNORE INTO factions (id, name, description, damage_type, bonus_per_loyalty) VALUES
(1, 'Alvar Liberation', 'Survivors of the Astral Dimension war', 'elemental', 0.01),
(2, 'Delruk Alliance', 'Members of Diamond City and nearby lands', 'attack_vile', 0.02),
(3, 'Vordyn Rebellion', 'Formed on Veldara during Thanox reign', 'chaos', 0.02);

-- Characters
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    name TEXT UNIQUE NOT NULL,
    class_id INTEGER NOT NULL,
    level INTEGER DEFAULT 1,
    experience BIGINT DEFAULT 0,
    gold BIGINT DEFAULT 1000,
    rage_current INTEGER DEFAULT 100,
    rage_max INTEGER DEFAULT 100,
    hit_points_current INTEGER DEFAULT 100,
    hit_points_max INTEGER DEFAULT 100,
    
    -- Combat stats
    attack INTEGER DEFAULT 10,
    chaos_damage INTEGER DEFAULT 0,
    vile_damage INTEGER DEFAULT 0,
    fire_damage INTEGER DEFAULT 0,
    kinetic_damage INTEGER DEFAULT 0,
    arcane_damage INTEGER DEFAULT 0,
    holy_damage INTEGER DEFAULT 0,
    shadow_damage INTEGER DEFAULT 0,
    
    -- Resistances
    fire_resist INTEGER DEFAULT 0,
    kinetic_resist INTEGER DEFAULT 0,
    arcane_resist INTEGER DEFAULT 0,
    holy_resist INTEGER DEFAULT 0,
    shadow_resist INTEGER DEFAULT 0,
    
    -- Special stats
    wilderness_level INTEGER DEFAULT 1,
    god_slayer_level INTEGER DEFAULT 0,
    total_power INTEGER DEFAULT 0,
    
    -- Faction system (level 91+)
    faction_id INTEGER,
    alvar_loyalty INTEGER DEFAULT 0,
    delruk_loyalty INTEGER DEFAULT 0,
    vordyn_loyalty INTEGER DEFAULT 0,
    faction_changes_this_month INTEGER DEFAULT 0,
    
    -- Location
    current_room_id INTEGER DEFAULT 1,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (account_id) REFERENCES accounts(id),
    FOREIGN KEY (class_id) REFERENCES character_classes(id),
    FOREIGN KEY (faction_id) REFERENCES factions(id)
);

-- Equipment slots and items
CREATE TABLE IF NOT EXISTS equipment_slots (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    slot_type TEXT NOT NULL
);

INSERT OR IGNORE INTO equipment_slots (id, name, slot_type) VALUES
(1, 'head', 'armor'),
(2, 'chest', 'armor'),
(3, 'legs', 'armor'),
(4, 'boots', 'armor'),
(5, 'weapon', 'weapon'),
(6, 'shield', 'shield'),
(7, 'accessory1', 'accessory'),
(8, 'accessory2', 'accessory'),
(9, 'ring1', 'ring'),
(10, 'ring2', 'ring');

-- Item rarity system
CREATE TABLE IF NOT EXISTS item_rarities (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    color TEXT,
    power_multiplier REAL DEFAULT 1.0
);

INSERT OR IGNORE INTO item_rarities (id, name, color, power_multiplier) VALUES
(1, 'Elite', '#888888', 1.0),
(2, 'Brutal', '#00ff00', 1.5),
(3, 'Godly', '#0088ff', 2.0),
(4, 'King', '#ff8800', 3.0),
(5, 'Mythic', '#ff0088', 5.0);

-- Items/Equipment
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slot_id INTEGER NOT NULL,
    rarity_id INTEGER NOT NULL,
    level_requirement INTEGER DEFAULT 1,
    
    -- Combat stats
    attack INTEGER DEFAULT 0,
    hit_points INTEGER DEFAULT 0,
    chaos_damage INTEGER DEFAULT 0,
    vile_damage INTEGER DEFAULT 0,
    fire_damage INTEGER DEFAULT 0,
    kinetic_damage INTEGER DEFAULT 0,
    arcane_damage INTEGER DEFAULT 0,
    holy_damage INTEGER DEFAULT 0,
    shadow_damage INTEGER DEFAULT 0,
    
    -- Resistances
    fire_resist INTEGER DEFAULT 0,
    kinetic_resist INTEGER DEFAULT 0,
    arcane_resist INTEGER DEFAULT 0,
    holy_resist INTEGER DEFAULT 0,
    shadow_resist INTEGER DEFAULT 0,
    
    -- Special stats
    critical_hit_percent REAL DEFAULT 0.0,
    rampage_percent REAL DEFAULT 0.0,
    rage_per_hour INTEGER DEFAULT 0,
    experience_per_hour INTEGER DEFAULT 0,
    gold_per_turn INTEGER DEFAULT 0,
    max_rage INTEGER DEFAULT 0,
    
    -- Transfer system
    max_transfers INTEGER DEFAULT 10,
    transfer_cost_points INTEGER DEFAULT 1,
    
    -- Metadata
    description TEXT,
    is_raidbound BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (slot_id) REFERENCES equipment_slots(id),
    FOREIGN KEY (rarity_id) REFERENCES item_rarities(id)
);

-- Character equipment (what each character has equipped)
CREATE TABLE IF NOT EXISTS character_equipment (
    character_id INTEGER NOT NULL,
    slot_id INTEGER NOT NULL,
    item_id INTEGER,
    
    PRIMARY KEY (character_id, slot_id),
    FOREIGN KEY (character_id) REFERENCES characters(id),
    FOREIGN KEY (slot_id) REFERENCES equipment_slots(id),
    FOREIGN KEY (item_id) REFERENCES items(id)
);

-- Character inventory
CREATE TABLE IF NOT EXISTS character_inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    transfers_remaining INTEGER,
    
    FOREIGN KEY (character_id) REFERENCES characters(id),
    FOREIGN KEY (item_id) REFERENCES items(id)
);

-- Crews/Guilds
CREATE TABLE IF NOT EXISTS crews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    leader_id INTEGER NOT NULL,
    description TEXT,
    max_members INTEGER DEFAULT 20,
    vault_capacity INTEGER DEFAULT 100,
    has_two_way_vault BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (leader_id) REFERENCES characters(id)
);

-- Crew membership
CREATE TABLE IF NOT EXISTS crew_members (
    crew_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    role TEXT DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (crew_id, character_id),
    FOREIGN KEY (crew_id) REFERENCES crews(id),
    FOREIGN KEY (character_id) REFERENCES characters(id)
);

-- Crew vault
CREATE TABLE IF NOT EXISTS crew_vault (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crew_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    deposited_by INTEGER,
    deposited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (crew_id) REFERENCES crews(id),
    FOREIGN KEY (item_id) REFERENCES items(id),
    FOREIGN KEY (deposited_by) REFERENCES characters(id)
);

-- World/Rooms system
CREATE TABLE IF NOT EXISTS zones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    min_level INTEGER DEFAULT 1,
    max_level INTEGER DEFAULT 95
);

INSERT OR IGNORE INTO zones (id, name, description, min_level, max_level) VALUES
(1, 'Diamond City', 'Main hub with multiple districts', 1, 95),
(2, 'Fire Dimension', 'Elemental plane of fire', 90, 95),
(3, 'Kinetic Dimension', 'Elemental plane of kinetic energy', 90, 95),
(4, 'Shadow Dimension', 'Elemental plane of shadow', 90, 95),
(5, 'Astral Ruins', 'High-level content area', 85, 95);

CREATE TABLE IF NOT EXISTS rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    zone_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    x INTEGER DEFAULT 0,
    y INTEGER DEFAULT 0,
    
    FOREIGN KEY (zone_id) REFERENCES zones(id)
);

-- Room connections
CREATE TABLE IF NOT EXISTS room_connections (
    from_room_id INTEGER NOT NULL,
    to_room_id INTEGER NOT NULL,
    direction TEXT NOT NULL,
    
    PRIMARY KEY (from_room_id, direction),
    FOREIGN KEY (from_room_id) REFERENCES rooms(id),
    FOREIGN KEY (to_room_id) REFERENCES rooms(id)
);

-- Insert some basic rooms
INSERT OR IGNORE INTO rooms (id, zone_id, name, description, x, y) VALUES
(1, 1, 'Diamond City Center', 'The heart of Diamond City', 0, 0),
(2, 1, 'Underground Casino', 'Gambling and entertainment district', -1, -1),
(3, 1, 'City Hall', 'Administrative center', 0, 1),
(4, 1, 'Fight Arena', 'Combat training and PvP area', 1, 0);

INSERT OR IGNORE INTO room_connections (from_room_id, to_room_id, direction) VALUES
(1, 2, 'southwest'),
(2, 1, 'northeast'),
(1, 3, 'north'),
(3, 1, 'south'),
(1, 4, 'east'),
(4, 1, 'west');

-- Combat log
CREATE TABLE IF NOT EXISTS combat_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attacker_id INTEGER NOT NULL,
    defender_id INTEGER,
    attacker_damage INTEGER DEFAULT 0,
    defender_damage INTEGER DEFAULT 0,
    attacker_hp_before INTEGER,
    attacker_hp_after INTEGER,
    defender_hp_before INTEGER,
    defender_hp_after INTEGER,
    winner_id INTEGER,
    experience_gained INTEGER DEFAULT 0,
    gold_gained INTEGER DEFAULT 0,
    combat_type TEXT DEFAULT 'pve',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (attacker_id) REFERENCES characters(id),
    FOREIGN KEY (defender_id) REFERENCES characters(id),
    FOREIGN KEY (winner_id) REFERENCES characters(id)
);

-- Sessions for web authentication
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    account_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_characters_account ON characters(account_id);
CREATE INDEX IF NOT EXISTS idx_characters_name ON characters(name);
CREATE INDEX IF NOT EXISTS idx_character_equipment_character ON character_equipment(character_id);
CREATE INDEX IF NOT EXISTS idx_character_inventory_character ON character_inventory(character_id);
CREATE INDEX IF NOT EXISTS idx_crew_members_character ON crew_members(character_id);
CREATE INDEX IF NOT EXISTS idx_sessions_account ON sessions(account_id);
CREATE INDEX IF NOT EXISTS idx_combat_logs_attacker ON combat_logs(attacker_id);
CREATE INDEX IF NOT EXISTS idx_combat_logs_defender ON combat_logs(defender_id);