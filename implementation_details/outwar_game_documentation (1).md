# Outwar Game Systems & Detailed UI Documentation

## Main Game Interface Layout

### Top Navigation Bar
```
Background: Dark gradient (black to dark gray)
Height: ~40px
Layout: Horizontal tabs with rounded corners

Tab Structure (left to right):
1. "Explore World" - Orange/gold gradient button, currently active
2. "Dungeons" - Inactive, dark background
3. "Challenges" - Inactive, dark background  
4. "All docs" - Inactive, dark background
5. "News" - Inactive, dark background
6. "Discord" - Inactive, dark background, rightmost

Visual Style:
- Active tab: Bright orange/gold gradient with white text
- Inactive tabs: Dark gray/black with muted text
- Tab borders: Subtle rounded corners
- Text: White, small caps font
```

### Header Status Bar
```
Background: Golden/yellow gradient bar
Height: ~30px
Content Layout (left to right):

Player Info Section:
- Username: "XaocLv" in white text
- Health indicator: Small red circle icon
- Clock icon: Shows "5:26am" 
- Level display: "Level: 53"
- Experience: "EXP: 11,723,366"
- Resource bar: "RAGE: 16,038" with yellow/green gradient fill

Right Side Icons:
- Series of small circular icons (appears to be quick access buttons)
- Each icon ~20px diameter
- Icons appear to represent different game functions
```

### Main Content Area Layout (3-Column Structure)

#### Left Sidebar (Navigation Menu)
```
Width: ~180px
Background: Dark gray/black gradient
Border: Subtle dark border

Menu Items (top to bottom):
━━━━━━━━━━━━━━━━━━━━
📁 MY RGA
🏠 HOME  
👤 CHARACTER          ▶
🛒 MARKETPLACE        ▶
🏆 RANKINGS
⚡ ACTIONS            ▶
👥 CREW               ▶
🎰 CASINO             ▶
🏅 CHALLENGES
🌍 WORLD

Visual Styling:
- Each item: ~35px height
- Icons: 16px, left-aligned
- Text: White, 12px font
- Arrow indicators (▶): Right-aligned for expandable menus
- Hover state: Subtle highlight
- Active state: Different background color

Bottom Section:
"GET POINTS + TOKENS" button
- Yellow/gold gradient background
- Black text
- Rounded corners
- ~150px width
```

#### Center Content Area (Primary Game View)
```
Width: ~600px (flexible)
Background: Dark theme with content-specific backgrounds

Underground Casino Section:
┌─────────────────────────────────────┐
│ - Underground Casino -              │
│                                     │
│ [Room Map Display]                  │
│ ┌─────────────────┐                │
│ │ ASCII-style map │                │
│ │ showing room    │                │
│ │ layout with     │                │
│ │ walls and       │                │
│ │ pathways        │                │
│ └─────────────────┘                │
│                                     │
│ Navigation Controls:                │
│ [W]           [bag icon]            │
│ [◀] [S] [▶]   [my vault]           │
│              [profile] [stats]      │
│                                     │
│ Hotkeys: Equipment, Quickpack,      │
│ Quests                              │
└─────────────────────────────────────┘

Room Details Section:
┌─────────────────────────────────────┐
│ - Room Details: 329 -               │
│                                     │
│ [Large room illustration]           │
│ ┌─────────────────────────────────┐ │
│ │ Detailed scene showing:         │ │
│ │ - Casino interior with tables   │ │
│ │ - NPCs and characters          │ │
│ │ - Environmental details        │ │
│ │ - Interactive elements         │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Action Buttons Row:                 │
│ [Supplies] [Treasury] [Dungeons]    │
│ [Wilderness]                        │
│                                     │
│ NPC List:                          │
│ 👤 High Roller     [ATTACK]        │
│    Level 20                        │
│ 👤 High Roller     [ATTACK]        │
│    Level 20                        │
│ 👤 High Roller     [ATTACK]        │
│    Level 20                        │
│ 👤 High Roller     [ATTACK]        │
│    Level 20                        │
│ 👤 High Roller     [ATTACK]        │
│    Level 20                        │
│ 👤 The Boss        [RAID!]         │
│    Level 22                        │
└─────────────────────────────────────┘
```

#### Right Sidebar (Quest Helper)
```
Width: ~200px
Background: Dark gray gradient

Quest Helper Panel:
┌───────────────────────────┐
│ QUEST HELPER              │
│                           │
│ [Search for a Quest Mob]  │
│                           │
│ Current Target:           │
│ ┌─────────────────────┐   │
│ │ 🧙 Magitious Demise │   │
│ │                     │   │
│ │ Auto    Teleport    │   │
│ │ Attacker            │   │
│ │                     │   │
│ │ Status: 402/403 kills│   │
│ └─────────────────────┘   │
│                           │
│ Quest Log                 │
└───────────────────────────┘

Styling:
- Header: Bright text on dark background
- Search button: Interactive, rounded
- Target display: Card-style layout
- Status indicators: Color-coded
- Progress tracking: Numerical displays
```

## Character Profile Interface

### Profile Header
```
Layout: Two-column header with character info

Left Section:
┌──────────────────────────────────────────┐
│ rap2Lv                                   │
│ 10 Profile Hits                          │
│                                          │
│ [Large Character Portrait]               │
│ ┌────────────────────────────────────┐   │
│ │ Anime-style character illustration │   │
│ │ with detailed artwork             │   │
│ │ Background: Red/black gradient     │   │
│ └────────────────────────────────────┘   │
└──────────────────────────────────────────┘

Right Section (Action Buttons):
┌─────────────────────────────────────┐
│ ⚔️ ATTACK    💎 TRADE              │
│ ✉️ MESSAGE   👥 CREW INV           │
│ ➕ ADD ALLY  ⚔️ ADD ENEMY          │
│ ❌ BLOCK     💰 TREASURY           │
└─────────────────────────────────────┘

Button Styling:
- Icon + text layout
- Rounded rectangular buttons
- Color-coded by function type
- Hover states with subtle animations
```

### Skills Section
```
Section Header: "SKILLS:" in bold white text
Content: Currently empty/no skills displayed
Background: Dark panel consistent with theme
```

### Player Info Panel
```
┌─────────────────────────────────────────────┐
│ PLAYER INFO                                 │
│                                             │
│ CHARACTER CLASS      Level 56 Pop star     │
│ TOTAL EXPERIENCE     16,955,862             │
│ GROWTH YESTERDAY     28,992                 │
│ TOTAL POWER          6,022                  │
│ ATTACK               1,189                  │
│ HIT POINTS           4,833                  │
│ CHAOS DAMAGE         0                      │
│ ELEMENTAL ATTACK     150                    │
│ ELEMENTAL RESIST     600                    │
│ WILDERNESS LEVEL     11                     │
│ GOD SLAYER LEVEL     0                      │
│ PARENT               None                   │
│ FACTION              None ( )               │
│                                             │
│ Leader of Animosity Familia                │
│ ████████████████████████████████████████    │
│ (Progress bar - yellow/gold gradient)       │
└─────────────────────────────────────────────┘

Styling:
- Two-column layout: Label | Value
- Labels: Left-aligned, white text, bold
- Values: Right-aligned, colored by type
- Progress bar: Full-width, gradient fill
- Consistent spacing and typography
```

### Personal Allies Section
```
┌─────────────────────────────────────────┐
│ PERSONAL ALLIES (2)                     │
│                                         │
│ [Large character portrait placeholder]  │
│ ┌─────────────────────────────────────┐ │
│ │ Anime-style character art           │ │
│ │ Purple/pink theme                   │ │
│ │ Professional illustration style     │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ N/A                                     │
└─────────────────────────────────────────┘
```

## Equipment Interface

### Equipment Grid Layout
```
┌─────────────────────────────────────────┐
│ EQUIPMENT                               │
│                                         │
│ Main Equipment Grid (3x4):              │
│ ┌───┐ ┌───┐ ┌───┐                      │
│ │ 💎│ │🔮 │ │🏹 │  Top Row             │
│ └───┘ └───┘ └───┘                      │
│ ┌───┐ ┌───┐ ┌───┐                      │
│ │🔫 │ │👕 │ │🛡️ │  Middle Row          │
│ └───┘ └───┘ └───┘                      │
│ ┌───┐ ┌───┐ ┌───┐                      │
│ │💍 │ │👖 │ │💍 │  Bottom Row          │
│ └───┘ └───┘ └───┘                      │
│      ┌───┐                             │
│      │👢 │     Boots (centered)        │
│      └───┘                             │
│                                         │
│ Quick Access Slots (5 slots):           │
│ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐         │
│ │   │ │   │ │🟢 │ │   │ │   │         │
│ └───┘ └───┘ └───┘ └───┘ └───┘         │
└─────────────────────────────────────────┘

Slot Specifications:
- Each slot: 64x64 pixels
- Border: 2px dark gray when empty
- Border: 2px gold when occupied
- Background: Dark gray gradient
- Item icons: High-resolution, centered
- Tooltips: Appear on hover
```

### Item Tooltip System

#### Weapon Tooltip Example
```
┌─────────────────────────────────────────┐
│ War Shattered Grenade Launcher          │
│ [Slot - Weapon]                         │
│                                         │
│ +250 ATK                                │
│ +100 rage per hr                        │
│ +50 exp per hr                          │
│ +5% rampage                             │
│ +1,200 max rage                         │
│ +6% critical hit                        │
│                                         │
│ Can change hands 1 more time today      │
└─────────────────────────────────────────┘

Styling:
- Background: Dark semi-transparent
- Border: Gold/orange gradient
- Title: White, bold, 14px
- Slot type: Gray italics, 10px
- Stats: Color-coded by type
  - Green: Positive bonuses
  - Blue: Special effects
  - Orange: Percentage bonuses
- Footer text: Yellow warning color
- Shadow: Subtle drop shadow
```

#### Armor Tooltip Example
```
┌─────────────────────────────────────────┐
│ Black Kings Guard                       │
│ [Slot - Body]                           │
│                                         │
│ +75 Arcane                              │
│ +775 HP                                 │
│ +55 Holy Resist                         │
│ +55 Arcane Resist                       │
│ +55 Fire Resist                         │
│ +55 Kinetic Resist                      │
│ +55 Shadow Resist                       │
│ +333 gold per turn                      │
│ +395 rage per hr                        │
│ +315 exp per hr                         │
│ +50 rampage                             │
│ +4,343 max rage                         │
│ +13% critical hit                       │
│                                         │
│ Can change hands 1 more time today      │
└─────────────────────────────────────────┘
```

### Skill Crests Section
```
┌─────────────────────────────────────────┐
│ SKILL CRESTS                            │
│                                         │
│ ┌───┐ ┌───┐ ┌───┐ ┌───┐                │
│ │   │ │   │ │   │ │   │                │
│ └───┘ └───┘ └───┘ └───┘                │
└─────────────────────────────────────────┘

Currently: All slots empty
Styling: Same as equipment slots
```

### Masteries Section
```
┌─────────────────────────────────────────┐
│ MASTERIES                               │
│                                         │
│ OVERALL MASTERY                         │
│ ████████████████████████████████░░░░    │
│                                         │
│ ATTACK MASTERY                          │
│ ████████████████████████████░░░░░░░░    │
└─────────────────────────────────────────┘

Progress Bar Styling:
- Width: Full panel width
- Height: 20px
- Fill: Blue gradient
- Background: Dark gray
- Rounded corners: 5px
- Percentage indicators: Implied by fill level
```

## World Map Interface

### Diamond City World Map
```
Header Section:
┌─────────────────────────────────────────┐
│ Diamond City                            │
│ Y.65                                    │
│                                         │
│ Start playing Outwar - create a FREE    │
│ character at Outwar.com, Click Here.    │
│                                         │
│ Original map is located at              │
│ http://ylts.planet.ee/dcmap/            │
└─────────────────────────────────────────┘

Map Legend:
┌─────────────────────────────────────────┐
│ ☐ God(s)         🟫 Szecian Badlands   │
│ 🟫 Street        🟫 Lower Badlands     │
│ ⬜ Room          ⬛ Upper Badlands     │
│ 🟩 Subway        ⬜ Rare hole          │
│ 🟧 Trainer       ⬜ Waterway           │
│ 🟦 Water         🟥 New Area/Room      │
│ 🟨 Entrance      🟩 New Wilderness Gods │
│ ☐ Needs key                           │
└─────────────────────────────────────────┘

Visual Map Layout:
- Large grid-based map display
- Color-coded tiles per legend
- Clickable room navigation
- Zoom and pan capabilities
- Current location indicator
- Route planning visual aids
```

### Area-Specific Map (DCI Map)
```
┌─────────────────────────────────────────┐
│ Outwar Secrets DCI Map                  │
│                                         │
│ File    Outwar Secrets                  │
│                                         │
│ Legend:                                 │
│ 🟩 Subways                              │
│ 🟦 Rooms                                │
│ 🟥 Rare Holes                           │
│ 🟪 Waterways                            │
│                                         │
│ Room Number: 6                          │
│ Street Name: Wastelands Entrance        │
└─────────────────────────────────────────┘

Detailed Room List:
1. Training Ground        15. Subway Outlet (Broadway Street)
2. Wastelands            16. Broken Buildings
3. Dusty Glass Tavern    17. Subway Station
4. Dominic's Restaurant  18. Concert Hall
5. Rancid Wasteland Camp 19. Sound Lab
6. Subway Outlet         20. Dunkin Donuts
7. DC Enforcers         21. Terrance Statue
8. Soundweaver Academy  22. Hall of Fame
9. City Hall            23. C Blocks
10. Blackheart's Bank   24. Stag Warehouse
11. Underground Casino  25. Boat House
12. Slaughter View      26. Sunken Boat
13. Fat Tony's Night Club 27. Gunsmoke Boat
14. Fight Arena         28. Boat to Stizzy
                        (continues to 36+)
```

## Crew/Guild Interface

### Crew Vault Header
```
┌─────────────────────────────────────────┐
│ 🔵 Animosity Familia                    │
│                                         │
│ [Edit Crew ▼] [Actions ▼] [Storage ▼]   │
│ [Accomplishments ▼]                     │
│                                         │
│ Currently Storing 9 / 100 Items        │
└─────────────────────────────────────────┘

Dropdown Menu Styling:
- Purple/blue gradient buttons
- White text with dropdown arrows
- Rounded corners
- Consistent spacing
```

### Vault Grid Display
```
┌─────────────────────────────────────────┐
│ Crew Vault                              │
│ Order By: Alphabetical | Newest         │
│                                         │
│ Item Grid (10x10):                      │
│ 🏆🏆🏆🏆🏆🏆🏆🏆🏆 ⬜                  │
│ ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜                    │
│ ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜                    │
│ ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜                    │
│ ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜                    │
│ ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜                    │
│ ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜                    │
│ ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜                    │
│ ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜                    │
│ ⬜⬜⬜⬜                                │
└─────────────────────────────────────────┘

Grid Specifications:
- 100 total slots (10x10 + 4 additional)
- Each slot: 48x48 pixels
- 2px spacing between slots
- Items: Gold trophy icons (identical)
- Empty slots: Dark gray background
- Hover effect: Subtle highlight
```

### Vault Management Panel
```
Left Side - Award Item:
┌─────────────────────────────────────────┐
│ Award Item                              │
│                                         │
│ To award an item to a crew member,      │
│ click the item(s) you would like to     │
│ award above, then select the crew       │
│ member to award it to below            │
│                                         │
│ Member Dropdown:                        │
│ ┌─────────────────────────────────────┐ │
│ │ alfoLv                          ▼   │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Award Items]                           │
│                                         │
│ View awarded item log                   │
│                                         │
│ Note: To deposit an item into your      │
│ crew's vault, your crew must have       │
│ the Two Way Vault upgrade from the      │
│ Treasury.                               │
└─────────────────────────────────────────┘

Right Side - Delete Items:
┌─────────────────────────────────────────┐
│ Delete Items                            │
│                                         │
│ To delete an item from the vault,       │
│ click the item(s) you would like to     │
│ delete above, check the check box,      │
│ then click the delete items button      │
│ below.                                  │
│                                         │
│ ☐ I would like to delete the           │
│   selected items.                       │
│                                         │
│ [Delete Items]                          │
│                                         │
│ View deleted item log                   │
└─────────────────────────────────────────┘

Button Styling:
- Blue gradient background
- White text, bold
- Rounded corners (8px radius)
- Disabled state when conditions not met
```

## Combat Interface

### Battle Screen Layout
```
┌─────────────────────────────────────────┐
│                rap2Lv                   │
│                  VS                     │
│              High Roller                │
│                                         │
│ ┌─────────────────┐ ┌─────────────────┐ │
│ │ [Left Portrait] │ │ [Right Portrait]│ │
│ │                 │ │                 │ │
│ │ Anime character │ │ Blonde character│ │
│ │ Red/black theme │ │ Light theme     │ │
│ │                 │ │                 │ │
│ │ ████████████    │ │ ████            │ │
│ │ Health Bar      │ │ Health Bar      │ │
│ └─────────────────┘ └─────────────────┘ │
│                                         │
│ Battle Result Box:                      │
│ ┌─────────────────────────────────────┐ │
│ │ You have won the battle!            │ │
│ │ rap2Lv gained 0 strength            │ │
│ │ 🟡 rap2Lv gained 2 gold!            │ │
│ │ Show Combat Log                     │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [RETURN TO WORLD]                       │
└─────────────────────────────────────────┘

Portrait Specifications:
- Size: 200x300 pixels each
- High-quality character artwork
- Health bars: Full width, gradient fills
- Dynamic health updates during combat
- Visual damage effects
```

### Combat Result Panel
```
┌─────────────────────────────────────────┐
│ Victory Message: "You have won the      │
│ battle!" - Large, white text            │
│                                         │
│ Rewards Section:                        │
│ • Strength Gain: "rap2Lv gained 0      │
│   strength" - Gray text (no gain)       │
│ • Gold Reward: "🟡 rap2Lv gained 2     │
│   gold!" - Yellow coin icon + text      │
│                                         │
│ Interactive Elements:                   │
│ • "Show Combat Log" - Clickable link    │
│ • Return button - Prominent placement   │
└─────────────────────────────────────────┘
```

### Combat Log Interface
```
┌─────────────────────────────────────────┐
│ Hide Combat Log                         │
│                                         │
│ High Roller blocked rap2Lv's attack!    │
│ rap2Lv hit High Roller for 75 arcane    │
│ damage!                                 │
│ rap2Lv hit High Roller for 71 kinetic   │
│ damage!                                 │
│ High Roller hit rap2Lv for 46 damage!   │
│ rap2Lv hit High Roller for 667 damage!  │
│ rap2Lv hit High Roller for 69 arcane    │
│ damage!                                 │
│ rap2Lv hit High Roller for 64 kinetic   │
│ damage!                                 │
│ rap2Lv has defeated High Roller!        │
└─────────────────────────────────────────┘

Log Entry Styling:
- Background: Semi-transparent dark
- Text: White, monospace font
- Damage numbers: Color-coded by type
- Critical hits: Bold/highlighted
- Block attempts: Different color
- Victory message: Emphasized styling
```

## Color Scheme & Typography

### Primary Color Palette
```
Background Colors:
- Primary Dark: #1a1a1a
- Secondary Dark: #2d2d2d
- Panel Background: #333333
- Accent Dark: #4a4a4a

Accent Colors:
- Gold/Yellow: #ffd700 (buttons, highlights)
- Orange: #ff8c00 (active tabs, warnings)
- Blue: #4169e1 (links, info elements)
- Green: #32cd32 (positive values, success)
- Red: #dc143c (negative values, danger)
- Purple: #8a2be2 (special items, magic)

Text Colors:
- Primary Text: #ffffff
- Secondary Text: #cccccc
- Muted Text: #888888
- Accent Text: #ffd700
```

### Typography System
```
Headers:
- Font: Arial/Helvetica, Bold
- Sizes: 16px (main), 14px (sub), 12px (small)
- Color: White or accent colors

Body Text:
- Font: Arial/Helvetica, Regular
- Size: 11px (primary), 10px (secondary)
- Line Height: 1.2em
- Color: White or light gray

UI Elements:
- Buttons: Bold, 11px, uppercase
- Links: Regular, 10px, colored
- Labels: Bold, 10px, right-aligned
- Values: Regular, 10px, left-aligned
```

### Interactive Element States
```
Button States:
- Normal: Gradient background, white text
- Hover: Slightly lighter gradient, subtle glow
- Active: Pressed effect, darker gradient
- Disabled: Grayed out, reduced opacity

Link States:
- Normal: Blue text, no underline
- Hover: Brighter blue, underline appears
- Visited: Slightly darker blue
- Active: Pressed state

Input Fields:
- Normal: Dark background, light border
- Focus: Highlighted border, glow effect
- Error: Red border, error styling
```

This documentation now provides pixel-perfect specifications for recreating the Outwar interface, including exact layouts, color codes, typography systems, and interactive behaviors.