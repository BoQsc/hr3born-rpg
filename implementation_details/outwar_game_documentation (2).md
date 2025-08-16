# Outwar Game Systems Documentation

## Overview
Outwar is a browser-based MMORPG featuring character progression, equipment systems, crew mechanics, combat, and world exploration. The game combines traditional RPG elements with social features and persistent progression.

## Core Character System

### Character Stats Structure
```
Primary Stats:
- Level: Character progression level (observed: Level 56)
- Character Class: Descriptive titles (e.g., "Pop star")
- Total Experience: Cumulative experience points (16,955,862)
- Growth Yesterday: Daily experience gain tracking (28,992)
- Total Power: Overall character strength rating (6,022)

Combat Stats:
- Attack: Base attack power (1,189)
- Hit Points: Health/HP pool (4,833)
- Chaos Damage: Special damage type (0 in example)
- Elemental Attack: Magic-based attack power (150)
- Elemental Resist: Magic damage resistance (600)
- Wilderness Level: Outdoor exploration capability (11)
- God Slayer Level: End-game content progression (0)

Social Stats:
- Parent: Mentorship system reference (None)
- Faction: Guild/alliance affiliation (None)
- Personal Allies: Friend list capacity (2 shown)
```

### Character Progression
- Experience-based leveling system
- Daily experience tracking for progress monitoring
- Multiple progression tracks (Wilderness Level, God Slayer Level)
- Class titles that change based on progression

## Equipment System

### Equipment Slots Layout (3x3 + additional slots)
```
Top Row:    [Accessory] [Head/Neck] [Accessory]
Middle Row: [Weapon]    [Chest]     [Shield]
Bottom Row: [Ring]      [Legs]      [Ring]
Additional: [Boots] (centered below)
Extra Slots: [5 additional inventory/quick slots]
```

### Item Statistics Framework

#### Weapon Example: War Shattered Grenade Launcher
```
Item Type: [Slot - Weapon]
Base Stats:
- +250 ATK (Attack Power)
- +100 rage per hr (Resource Generation)
- +50 exp per hr (Experience Generation)
- +5% rampage (Percentage Bonus)
- +1,200 max rage (Resource Pool)
- +6% critical hit (Critical Strike Chance)

Meta Properties:
- Hand Change Limit: "Can change hands 1 more time today"
- Rarity/Quality indicators
```

#### Armor Example: Black Kings Guard
```
Item Type: [Slot - Body]
Defensive Stats:
- +75 Arcane (Magical Defense)
- +775 HP (Health Points)
- +55 Holy Resist (Resistance Type)
- +55 Arcane Resist
- +55 Fire Resist
- +55 Kinetic Resist
- +55 Shadow Resist

Economic Stats:
- +333 gold per turn (Income Generation)
- +395 rage per hr (Resource Generation)
- +315 exp per hr (Experience Generation)

Combat Stats:
- +50 rampage (Combat Bonus)
- +4,343 max rage (Resource Pool)
- +13% critical hit (Critical Chance)

Meta Properties:
- Hand Change Limit: Daily transfer restrictions
```

### Equipment Mechanics
- **Stat Bonuses**: Items provide flat and percentage-based bonuses
- **Resource Generation**: Items generate gold, rage, and experience per hour/turn
- **Resistance System**: Multiple damage types with specific resistances
- **Transfer Restrictions**: Items have daily trade/transfer limits
- **Critical Hit System**: Percentage-based critical strike chances

## Resource Systems

### Primary Resources
1. **Experience Points**: Character progression currency
2. **Gold**: Economic currency for transactions
3. **Rage**: Combat resource with maximum pool and hourly regeneration
4. **Hit Points**: Health system for survival

### Resource Generation
- **Per Hour**: Continuous passive generation from equipment
- **Per Turn**: Turn-based resource generation
- **Combat Rewards**: Direct gains from defeating enemies

## World and Navigation System

### World Structure: Diamond City Example
- **Multi-Zone Layout**: Large interconnected world map
- **Location Types**:
  - Residential areas (various building types)
  - Commercial zones (shops, services)
  - Special locations (Gates of Stoneraven)
  - Portal/transport points
  - Wilderness areas

### Area Navigation System
- **Room-Based Movement**: Discrete room navigation
- **Room Types**:
  - Regular rooms (numbered 1-36+)
  - Subways (fast travel)
  - Rare holes (special encounters)
  - Waterways (alternative routes)
  - Entrances/exits
  - Trainer locations
  - Special facilities

### Location Categories
```
Training Ground, Wastelands, Dusty Glass Tavern, Dominic's Restaurant
Rancid Wasteland Camp, Subway Outlets, DC Enforcers, Soundweaver Academy
City Hall, Underground Casino, Slaughter View Construction, Fat Tony's Night Club
Fight Arena, Various numbered areas, Transport systems
```

## Combat System

### Battle Interface
- **Opponent Matching**: Player vs Player or Player vs NPC
- **Visual Combat Display**: Character portraits during battle
- **Health Bars**: Real-time health tracking
- **Battle Results**: Win/loss determination with rewards

### Combat Mechanics
```
Damage Types:
- Arcane Damage (75 points observed)
- Kinetic Damage (71 points observed)
- Physical Damage (46, 667 points observed)

Combat Flow:
1. Attack/Defense rounds
2. Damage calculation with resistances
3. Critical hit applications
4. Battle resolution
5. Reward distribution
```

### Combat Log System
```
Sample Combat Log:
- High Roller blocked rap2Lv's attack!
- rap2Lv hit High Roller for 75 arcane damage!
- rap2Lv hit High Roller for 71 kinetic damage!
- High Roller hit rap2Lv for 46 damage!
- rap2Lv hit High Roller for 667 damage!
- rap2Lv hit High Roller for 69 arcane damage!
- rap2Lv hit High Roller for 64 kinetic damage!
- rap2Lv has defeated High Roller!
```

### Battle Rewards
- **Strength Gain**: Character progression (0 in example)
- **Gold Rewards**: Economic gains (2 gold shown)
- **Experience**: Combat experience points

## Crew/Guild System

### Crew Structure
- **Crew Name**: "Animosity Familia" (example)
- **Leadership Roles**: "Leader of Animosity Familia"
- **Crew Vault**: Shared storage system
- **Member Management**: Add/remove crew members

### Crew Vault System
```
Storage Capacity: 100 items maximum (9/100 shown in use)
Item Management:
- Award System: Distribute items to crew members
- Deletion System: Remove items with confirmation
- Sorting Options: Alphabetical/Newest organization

Award Mechanics:
- Select items from vault
- Choose recipient crew member
- Award confirmation system
- Item transfer logging

Deletion Mechanics:
- Item selection for deletion
- Confirmation checkbox requirement
- Batch deletion capability
- Deletion log tracking
```

## Quest and Exploration Systems

### Quest Helper Interface
- **NPC Targeting**: "Search for a Quest Mob"
- **Quest Types**: Various mission categories
- **Progress Tracking**: Quest completion monitoring
- **Reward Systems**: Experience and item rewards

### Exploration Mechanics
- **Room Discovery**: Systematic area exploration
- **NPC Encounters**: Combat and quest NPCs
- **Loot Systems**: Item drops and treasure
- **Area Progression**: Unlocking new zones

## Economic Systems

### Currency Types
- **Gold**: Primary economic currency
- **Items**: Equipment-based economy
- **Resources**: Rage, experience as tradeable commodities

### Economic Activities
- **Underground Casino**: Gambling mechanics
- **Item Trading**: Player-to-player economy
- **Crew Economy**: Shared resource management
- **Equipment Upgrades**: Resource investment systems

## User Interface Systems

### Navigation Menus
```
Primary Navigation:
- MY RGA (Account management)
- HOME (Main area)
- CHARACTER (Stats and progression)
- MARKETPLACE (Economic hub)
- RANKINGS (Competitive standings)
- ACTIONS (Available activities)
- CREW (Guild management)
- CASINO (Gambling activities)
- CHALLENGES (Competitive content)
- WORLD (Exploration hub)
```

### Character Interface
- **Profile Display**: Comprehensive stat presentation
- **Equipment Management**: Drag-and-drop item system
- **Skill Progression**: Advancement tracking
- **Social Features**: Ally and communication systems

## Technical Implementation Considerations

### Data Persistence
- **Character Data**: Stats, equipment, progression
- **World State**: Room layouts, NPC positions
- **Economic Data**: Market prices, transactions
- **Social Data**: Crew memberships, relationships

### Real-Time Elements
- **Resource Generation**: Hourly/turn-based updates
- **Combat Resolution**: Interactive battle systems
- **Chat Systems**: Real-time communication
- **Market Updates**: Dynamic economic changes

### Scalability Features
- **Multi-Zone Architecture**: Expandable world system
- **Crew Management**: Scalable guild systems
- **Equipment Variety**: Extensive item database
- **Progressive Content**: Expandable level ranges

## Game Balance Framework

### Power Scaling
- **Linear Progression**: Consistent advancement curves
- **Equipment Dependencies**: Gear-based power increases
- **Resource Management**: Limited daily/hourly actions
- **Social Benefits**: Crew-based advantages

### Competitive Elements
- **Player vs Player**: Direct combat systems
- **Rankings**: Competitive leaderboards
- **Resource Competition**: Limited rare items
- **Territory Control**: Area-based advantages

This documentation provides a comprehensive foundation for reimplementing the core systems of Outwar, maintaining the complexity and depth that made the original game engaging while providing clear technical specifications for development.