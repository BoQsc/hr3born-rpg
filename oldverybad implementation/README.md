# Outwar RPG Game

A comprehensive browser-based MMORPG inspired by the classic Outwar game, built with Python aiohttp and aiosql.

## Features Implemented

- **Character System**: 3 classes (Gangster, Monster, Pop Star) with unique bonuses
- **Equipment System**: Full item management with stats, rarity, and transfer limits
- **Combat System**: PvP and PvE combat with damage calculation and resistances
- **Crew/Guild System**: Crew creation, management, and shared vault
- **World Navigation**: Zone and room-based movement system
- **Resource Generation**: Hourly experience, rage, and gold generation
- **User Authentication**: JWT-based authentication with sessions
- **Real-time Features**: Redis-based caching and state management

## Technology Stack

- **Backend**: Python 3.8+ with aiohttp
- **Database**: PostgreSQL with aiosql
- **Caching**: Redis
- **Frontend**: HTML/CSS/JavaScript
- **Authentication**: JWT tokens

## Setup Instructions

### Prerequisites

1. Python 3.8 or higher
2. PostgreSQL 12 or higher
3. Redis server

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Setup PostgreSQL database:
```sql
CREATE DATABASE outwar_game;
CREATE USER outwar_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE outwar_game TO outwar_user;
```

3. Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env` with your database and Redis configurations:
```
DATABASE_URL=postgresql://outwar_user:your_password@localhost:5432/outwar_game
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
DEBUG=True
HOST=127.0.0.1
PORT=8000
```

4. Run the application:
```bash
python main.py
```

5. Open your browser and go to http://127.0.0.1:8000

## Game Features

### Character Classes

- **Gangster**: +5% Attack, +10% Defense - Balanced fighter with strong defense
- **Monster**: +5% Rage Per Turn, +10% Max Rage - Resource specialist with high rage pools
- **Pop Star**: +2.5% Attack, +5% Defense, +2.5% Rage Per Turn, +5% Max Rage - Jack-of-all-trades

### Equipment System

- **Equipment Slots**: 10 main slots (3x3 grid + boots) plus 5 quick slots
- **Item Rarity**: Elite → Brutal → Godly → King → Mythic
- **Stat Bonuses**: Attack, HP, resistances, resource generation
- **Transfer System**: Daily limits on item transfers between characters

### Combat System

- **Damage Types**: Physical, Fire, Kinetic, Arcane, Holy, Shadow, Chaos, Vile
- **Resistances**: Element-specific resistance system
- **Critical Hits**: Percentage-based critical strike chances
- **Combat Log**: Detailed battle logging with all actions

### Crew System

- **Crew Creation**: Form guilds with up to 20 members
- **Crew Vault**: Shared storage system (100 items capacity)
- **Item Management**: Award and delete items from vault
- **Leadership**: Crew leader and rank system

### Resource Generation

- **Hourly Generation**: Automatic rage and experience generation
- **Turn-based Gold**: Gold generation from equipment
- **Background Tasks**: Automated resource processing

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/logout` - User logout

### Characters
- `POST /api/characters` - Create character
- `GET /api/characters` - Get user's characters
- `GET /api/characters/{id}` - Get character details
- `PUT /api/characters/{id}/faction` - Change faction
- `GET /api/characters/{id}/stats` - Get character stats

### Equipment
- `GET /api/characters/{id}/items` - Get character items
- `GET /api/characters/{id}/equipment` - Get equipped items
- `POST /api/characters/{id}/items/{item_id}/equip` - Equip item
- `POST /api/characters/{id}/items/{item_id}/unequip` - Unequip item

### Combat
- `POST /api/combat/pvp` - Initiate PvP combat
- `POST /api/combat/pve` - Initiate PvE combat
- `GET /api/combat/history/{id}` - Get combat history

### World
- `GET /api/world/zones` - Get all zones
- `GET /api/world/rooms/{id}` - Get room details
- `GET /api/world/rooms/{id}/npcs` - Get NPCs in room
- `POST /api/characters/{id}/move` - Move character

### Crews
- `POST /api/crews` - Create crew
- `GET /api/crews/{id}` - Get crew details
- `GET /api/crews/{id}/vault` - Get crew vault items
- `POST /api/crews/{id}/vault/deposit` - Deposit item
- `POST /api/crews/{id}/vault/award` - Award item

## Database Schema

The game uses a comprehensive PostgreSQL schema with the following main tables:

- `users` - User accounts and authentication
- `characters` - Character data and stats
- `crews` - Guild/crew information
- `item_templates` - Item definitions
- `character_items` - Character inventories
- `crew_vault_items` - Crew shared storage
- `npcs` - Non-player characters
- `combat_logs` - Battle history
- `quest_templates` - Quest definitions
- `zones` and `rooms` - World structure

## Development

### Background Tasks

The game runs several background tasks:

- **Resource Generation**: Processes hourly resource generation for active characters
- **NPC Respawn**: Manages NPC respawn timers
- **Session Cleanup**: Removes expired sessions and old data
- **Daily Reset**: Resets daily counters and quest progress

### Caching Strategy

Redis is used for:

- User session management
- Character stat caching
- Combat state tracking
- Room player lists
- Resource generation locks
- Daily transfer count tracking

### Security Features

- JWT token authentication
- Password hashing with bcrypt
- SQL injection prevention with parameterized queries
- Input validation and sanitization
- Rate limiting via transfer restrictions

## Future Enhancements

Potential additions for the complete Outwar experience:

- **Faction System**: Level 91+ faction mechanics
- **Quest System**: Comprehensive quest and mission system
- **Raid System**: Group raids against powerful bosses
- **PvP Rankings**: Competitive leaderboards
- **Event System**: Periodic game events
- **Real-time Chat**: WebSocket-based communication
- **Market System**: Player trading marketplace
- **Skills System**: Character abilities and specializations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is for educational purposes. Original Outwar game concept belongs to Rampid Interactive.