# Outwar Clone - MMO RPG Game

A browser-based sci-fi MMORPG inspired by the classic Outwar game, built with Python aiohttp and minimal dependencies.

## Features

### Core Systems
- **Character System**: 3 classes (Gangster, Monster, Pop Star) with unique bonuses
- **Equipment System**: 10 equipment slots with rarity tiers (Elite → Mythic)
- **Combat System**: PvP combat with complex damage calculations
- **World Navigation**: Room-based movement through multiple zones
- **Crew System**: Guilds with shared vaults and group activities
- **Level Progression**: 95 levels with exponential experience requirements

### Game Mechanics
- **Damage Types**: Physical, elemental (Fire/Kinetic/Arcane/Holy/Shadow), Chaos, Vile
- **Resistances**: Elemental damage mitigation system
- **Resource Management**: Health, Rage, Experience, Gold
- **Faction System**: Unlocks at level 91 with loyalty bonuses
- **Auto-healing**: Characters recover HP and rage over time

## Installation

1. **Install Python 3.8+**

2. **Install dependencies:**
   ```bash
   cd thegame
   pip install -r requirements.txt
   ```

3. **Run the game:**
   ```bash
   python main.py
   ```

4. **Access the game:**
   - Open browser to http://localhost:8080
   - Register a new account
   - Create your first character
   - Start playing!

## Architecture

### Tech Stack
- **aiohttp**: Async web server
- **aiosql**: SQL query management  
- **sqlite3**: Database (can upgrade to PostgreSQL)
- **aiohttp-session**: Session management

### Project Structure
```
thegame/
├── main.py              # Server entry point
├── database.py          # Database setup and management
├── models/              # Data models and game logic
├── handlers/            # HTTP request handlers
│   ├── auth.py         # Authentication
│   ├── character.py    # Character management
│   ├── world.py        # World navigation
│   ├── combat.py       # Combat system
│   └── crew.py         # Guild system
├── services/            # Business logic services
├── sql/                 # Database schema and queries
└── static/              # Frontend assets
```

## Game Classes

### Gangster
- **Focus**: Defense-oriented
- **Bonuses**: +5% Attack, +10% Defense
- **Playstyle**: Balanced attacker with superior defense

### Monster  
- **Focus**: Rage generation specialist
- **Bonuses**: +5% Rage Per Turn, +10% Max Rage
- **Playstyle**: Resource-heavy combat with high rage pools

### Pop Star
- **Focus**: Balanced hybrid
- **Bonuses**: +2.5% Attack, +5% Defense, +2.5% Rage Per Turn, +5% Max Rage
- **Playstyle**: Jack-of-all-trades with moderate bonuses

## Equipment Rarity

1. **Elite** (Gray) - Basic equipment
2. **Brutal** (Green) - 1.5x power multiplier
3. **Godly** (Blue) - 2x power multiplier  
4. **King** (Orange) - 3x power multiplier
5. **Mythic** (Pink) - 5x power multiplier

## Combat System

### Damage Calculation
- Base attack vs target resistances
- Elemental damage types with specific resistances
- Chaos and Vile damage (bypass resistances)
- Critical hits and special effects
- ±20% damage variance for realism

### PvP Combat
- Experience and gold rewards/penalties
- Rage consumption for attacks
- Counter-attacks when defender survives
- Combat logging and history

## Development

### Database Schema
- Comprehensive character progression system
- Equipment and inventory management
- Crew/guild functionality with vaults
- Combat logging and session management
- Room-based world with connections

### Security Features
- Password hashing with PBKDF2
- Session-based authentication
- SQL injection prevention with parameterized queries
- Input validation and sanitization

### Performance Features
- Async/await throughout for scalability
- Connection pooling with aiosqlite
- Background tasks for cleanup and healing
- Efficient database queries with indexes

## Extending the Game

The codebase is designed for easy extension:

1. **New Equipment**: Add items to database with stats
2. **New Zones**: Create rooms and connections in database  
3. **New Features**: Add handlers and update routes
4. **New Combat Types**: Extend damage calculation system
5. **Event System**: Add time-based events and rewards

## Production Deployment

For production use:
1. Switch to PostgreSQL database
2. Add Redis for session storage  
3. Implement proper logging
4. Add rate limiting and anti-cheat measures
5. Use reverse proxy (nginx) for static files
6. Set up SSL/TLS certificates

## Contributing

The game follows the original Outwar design philosophy:
- Complex character progression
- Equipment-driven power scaling
- Social guild mechanics
- Competitive PvP combat
- Long-term player retention through progression systems

Feel free to contribute new features, balance changes, or optimizations!