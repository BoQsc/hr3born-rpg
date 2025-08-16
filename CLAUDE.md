# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Outwar-inspired MMORPG built with Python aiohttp, featuring character progression, PvP combat, equipment systems, and crew/guild mechanics. The game uses SQLite for development and is designed for browser-based play.

## Development Commands

### Running the Game
```bash
cd thegame
python main.py
```
Server runs on http://localhost:8082 (note: port changed from README's 8080)

### Installing Dependencies
```bash
cd thegame
pip install -r requirements.txt
```

### Database Management
The database initializes automatically on first run. To reset:
```bash
# Delete the database file and restart server
rm thegame/game.db
python main.py
```

## Architecture Overview

### Core Components

**Database Layer**: Uses aiosql for SQL query management with SQLite backend. All queries are stored in `sql/queries.sql` with named parameters (`:parameter_name` format, not `?` positional).

**Handler Pattern**: Each major system has its own handler module:
- `auth.py`: User authentication and sessions
- `character.py`: Character creation, equipment, inventory
- `world.py`: Room navigation and world state
- `combat.py`: PvP combat system with damage calculations
- `crew.py`: Guild/crew system with shared vaults

**Model Layer**: Business logic in `models/character.py` with dataclass-based Character model containing combat calculations, equipment stats, and progression logic.

**Async Context Managers**: Database connections use custom context manager pattern:
```python
async with database.get_connection_context() as conn:
    # Database operations
```

### Critical Technical Details

**Query Annotations**: aiosql queries require specific annotations:
- `^` suffix for single-row returns (e.g., `get_character_by_id^`)
- `!` suffix for insert/update operations (e.g., `create_character!`)
- No suffix for multi-row returns

**Parameter Format**: All SQL queries use named parameters (`:param_name`) for aiosql compatibility. Never use positional parameters (`?`).

**Exception Handling**: HTTP redirects (`web.HTTPFound`) must be handled separately from other exceptions in handlers to avoid redirect loops.

**Session Management**: Uses aiohttp-session with SimpleCookieStorage. Characters are selected via `session['character_id']`.

### Game Systems Architecture

**Character Progression**: 3 classes (Gangster, Monster, Pop Star) with unique stat bonuses. Level cap at 95 with exponential XP requirements.

**Equipment System**: 10 equipment slots with rarity tiers (Elite→Mythic). Items have complex stat arrays including damage types and resistances.

**Combat System**: Damage calculation includes base attack, elemental damage types, resistances, and ±20% variance. Counter-attacks occur when defender survives.

**Crew System**: Hierarchical guild structure with leader/officer/member roles. Shared vault system with item deposits/awards.

### Database Schema Key Points

**Characters Table**: Tracks current HP/rage, equipment, location, and progression stats.

**Equipment Slots**: 10 slots (head, chest, legs, boots, weapon, shield, accessory1, accessory2, ring1, ring2) with foreign keys to items.

**Items System**: Rarity-based with power multipliers. Each item has full stat arrays for damage types and resistances.

**Crew Tables**: `crews` for guild data, `crew_members` for membership with roles, `crew_vault` for shared storage.

### Common Patterns

**Error Handling**: Handlers redirect with error messages in query parameters: `raise web.HTTPFound('/page?error=message')`

**Character Context**: Most handlers start with:
```python
await require_login(request)
character = await get_current_character(request)
if not character:
    raise web.HTTPFound('/characters')
```

**Database Queries**: Always use named parameters and proper connection context:
```python
async with database.get_connection_context() as conn:
    result = await database.queries.query_name(conn, param_name=value)
```

## Testing Approach

System testing follows complete user workflows:
1. Registration → Login → Character Creation → Equipment → Navigation → Combat → Crews

When testing database operations, verify both the handler response and actual database state changes.

## Important Constraints

- Use only the dependencies in requirements.txt
- SQLite is used for development (not PostgreSQL as mentioned in some docs)
- Session storage uses SimpleCookieStorage (not Redis)
- Server port is 8082 (not 8080 as in some documentation)
- All SQL queries must use named parameters for aiosql compatibility