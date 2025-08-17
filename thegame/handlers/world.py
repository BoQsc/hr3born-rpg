from aiohttp import web, web_request
from typing import Dict, List
import random

from database import get_db
from handlers.auth import require_login
from handlers.character import get_current_character

async def game_main(request: web_request.Request):
    """Main game interface - Outwar style"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        # Get current room info
        room_info = await database.queries.get_room_info(conn, room_id=character.current_room_id)
        connections = await database.queries.get_room_connections(conn, room_id=character.current_room_id)
        characters_in_room = await database.queries.get_characters_in_room(conn, room_id=character.current_room_id)
    
    # Build ASCII-style mini map
    minimap_html = generate_minimap(character.current_room_id, connections)
    
    # Build WASD movement controls
    movement_controls = generate_movement_controls(connections)
    
    # Build NPC/Character list in room
    npcs_html = ""
    for char in characters_in_room:
        if char['id'] != character.id:
            npcs_html += f"""
            <div class="npc-entry">
                <div class="npc-info">
                    <span class="npc-icon">👤</span>
                    <span class="npc-name">{char['name']}</span>
                </div>
                <div class="npc-level">Level {char['level']}</div>
                <form method="post" action="/attack/{char['id']}" style="display: inline;">
                    <button type="submit" class="btn-attack">ATTACK</button>
                </form>
            </div>
            """
    
    # Add some sample NPCs for better UI demonstration
    sample_npcs = [
        {"name": "High Roller", "level": 20},
        {"name": "High Roller", "level": 20},
        {"name": "High Roller", "level": 20},
        {"name": "High Roller", "level": 20},
        {"name": "The Boss", "level": 22, "special": True}
    ]
    
    for npc in sample_npcs:
        action_btn = "RAID!" if npc.get("special") else "ATTACK"
        btn_class = "btn-raid" if npc.get("special") else "btn-attack"
        npcs_html += f"""
        <div class="npc-entry">
            <div class="npc-info">
                <span class="npc-icon">👤</span>
                <span class="npc-name">{npc['name']}</span>
            </div>
            <div class="npc-level">Level {npc['level']}</div>
            <button class="{btn_class}">{action_btn}</button>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Outwar Clone - {character.name}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: Arial, sans-serif; background: #1a1a1a; color: #ffffff; }}
            
            /* Top Navigation */
            .top-nav {{ background: linear-gradient(180deg, #000 0%, #333 100%); height: 40px; display: flex; }}
            .nav-tab {{ padding: 8px 20px; color: #ccc; cursor: pointer; border-radius: 8px 8px 0 0; }}
            .nav-tab.active {{ background: linear-gradient(180deg, #ff8c00 0%, #ffd700 100%); color: #000; font-weight: bold; }}
            
            /* Header Status Bar */
            .status-bar {{ background: linear-gradient(180deg, #ffd700 0%, #ff8c00 100%); height: 30px; padding: 5px 15px; display: flex; justify-content: space-between; align-items: center; color: #000; font-size: 11px; font-weight: bold; }}
            .status-left {{ display: flex; gap: 15px; align-items: center; }}
            .status-right {{ display: flex; gap: 10px; }}
            
            /* Status Bar Interactive Elements */
            .character-name {{ cursor: pointer; padding: 2px 6px; border-radius: 3px; transition: all 0.2s; }}
            .character-name:hover {{ background: rgba(0,0,0,0.1); transform: scale(1.05); }}
            
            .level-stat, .exp-stat, .rage-stat {{ cursor: help; padding: 2px 4px; border-radius: 3px; transition: all 0.2s; }}
            .level-stat:hover, .exp-stat:hover, .rage-stat:hover {{ background: rgba(0,0,0,0.1); }}
            
            .status-icon {{ width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; cursor: pointer; border-radius: 3px; transition: all 0.2s; font-size: 10px; }}
            .status-icon:hover {{ background: rgba(0,0,0,0.1); transform: scale(1.1); }}
            
            /* Character Dropdown */
            .character-dropdown {{ position: absolute; top: 30px; left: 15px; background: #333; border: 1px solid #666; border-radius: 5px; padding: 10px; min-width: 200px; display: none; z-index: 1000; }}
            .character-dropdown.show {{ display: block; }}
            .dropdown-item {{ color: white; padding: 8px 12px; cursor: pointer; border-radius: 3px; }}
            .dropdown-item:hover {{ background: #555; }}
            
            /* Floating Windows */
            .floating-window {{ position: fixed; background: #2d2d2d; border: 2px solid #666; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); z-index: 1000; display: none; min-width: 300px; }}
            .floating-window.show {{ display: block; }}
            .window-header {{ background: #444; padding: 8px 12px; border-radius: 6px 6px 0 0; display: flex; justify-content: space-between; align-items: center; cursor: move; }}
            .window-title {{ color: #ffd700; font-weight: bold; }}
            .window-close {{ color: #ff4444; cursor: pointer; font-size: 16px; }}
            .window-close:hover {{ color: #ff6666; }}
            .window-content {{ padding: 15px; color: white; }}
            
            /* Main Layout */
            .game-container {{ display: flex; height: calc(100vh - 70px); }}
            
            /* Left Sidebar */
            .left-sidebar {{ width: 180px; background: linear-gradient(180deg, #2d2d2d 0%, #1a1a1a 100%); border-right: 1px solid #555; }}
            .menu-section {{ border-bottom: 1px solid #444; }}
            .menu-item {{ padding: 8px 15px; display: flex; align-items: center; gap: 10px; cursor: pointer; font-size: 11px; }}
            .menu-item:hover {{ background: #333; }}
            .menu-item.active {{ background: #444; }}
            .menu-icon {{ width: 16px; text-align: center; }}
            .get-points-btn {{ margin: 15px 10px; padding: 8px; background: linear-gradient(180deg, #ffd700 0%, #ff8c00 100%); color: #000; text-align: center; border-radius: 5px; cursor: pointer; font-size: 10px; font-weight: bold; }}
            
            /* Center Content */
            .center-content {{ flex: 1; padding: 20px; background: #333; }}
            .rooms-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
            .room-section {{ background: #2d2d2d; border: 1px solid #555; border-radius: 8px; }}
            .room-section.full-width {{ margin-bottom: 20px; }}
            .section-title {{ background: #444; padding: 10px 15px; border-radius: 8px 8px 0 0; font-weight: bold; text-align: center; }}
            .room-content {{ padding: 20px; }}
            
            /* Minimap */
            .minimap {{ width: 200px; height: 150px; background: #1a1a1a; border: 2px solid #666; font-family: 'Courier New', monospace; font-size: 10px; line-height: 1; padding: 5px; margin: 10px auto; white-space: pre; }}
            
            /* Movement Controls */
            .movement-controls {{ display: flex; flex-direction: column; align-items: center; gap: 5px; margin: 15px 0; }}
            .movement-row {{ display: flex; gap: 5px; }}
            .move-btn {{ width: 30px; height: 30px; background: #00aa00; color: white; border: none; border-radius: 3px; cursor: pointer; font-weight: bold; }}
            .move-btn:hover {{ background: #00cc00; }}
            .move-btn:disabled {{ background: #666; cursor: not-allowed; }}
            
            /* Hotkeys */
            .hotkeys {{ display: flex; gap: 10px; justify-content: center; margin-top: 15px; }}
            .hotkey-btn {{ padding: 5px 10px; background: #666; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 9px; }}
            .hotkey-btn:hover {{ background: #777; }}
            
            /* Room Details */
            .room-image {{ width: 100%; height: 200px; background: linear-gradient(45deg, #4a4a4a, #666); border: 2px solid #888; display: flex; align-items: center; justify-content: center; color: #ccc; margin-bottom: 15px; }}
            
            /* Action Buttons */
            .action-buttons {{ display: flex; gap: 10px; justify-content: center; margin-bottom: 20px; flex-wrap: wrap; }}
            .action-btn {{ padding: 8px 15px; background: #444; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 11px; }}
            .action-btn:hover {{ background: #555; }}
            
            /* NPC List */
            .npc-list {{ max-height: 200px; overflow-y: auto; border: 1px solid #555; border-radius: 5px; background: #1a1a1a; }}
            .npc-entry {{ display: flex; justify-content: space-between; align-items: center; padding: 8px; border-bottom: 1px solid #444; }}
            .npc-info {{ display: flex; align-items: center; gap: 8px; }}
            .npc-icon {{ font-size: 16px; }}
            .npc-name {{ font-size: 11px; }}
            .npc-level {{ font-size: 10px; color: #ccc; }}
            .btn-attack {{ padding: 3px 8px; background: #ff4444; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 9px; }}
            .btn-attack:hover {{ background: #ff6666; }}
            .btn-raid {{ padding: 3px 8px; background: #ff8800; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 9px; font-weight: bold; }}
            .btn-raid:hover {{ background: #ffaa00; }}
            
            /* Right Sidebar */
            .right-sidebar {{ width: 200px; background: linear-gradient(180deg, #2d2d2d 0%, #1a1a1a 100%); border-left: 1px solid #555; padding: 15px; }}
            .quest-helper {{ background: #333; border: 1px solid #555; border-radius: 5px; padding: 10px; }}
            .quest-header {{ text-align: center; font-weight: bold; margin-bottom: 10px; font-size: 11px; }}
            .quest-search {{ width: 100%; padding: 5px; background: #444; border: 1px solid #666; border-radius: 3px; color: white; font-size: 10px; margin-bottom: 10px; }}
            .quest-target {{ background: #444; border: 1px solid #666; border-radius: 3px; padding: 8px; text-align: center; font-size: 10px; }}
            .quest-status {{ margin-top: 5px; font-size: 9px; color: #ccc; }}
        </style>
    </head>
    <body>
        <!-- Top Navigation -->
        <div class="top-nav">
            <div class="nav-tab active">Explore World</div>
            <div class="nav-tab" onclick="window.location.href='/challenges'">Challenges</div>
            <div class="nav-tab" onclick="window.location.href='/marketplace'">Marketplace</div>
            <div class="nav-tab" onclick="window.location.href='/rankings'">Rankings</div>
            <div class="nav-tab" onclick="window.location.href='/casino'">Casino</div>
            <div class="nav-tab" onclick="window.location.href='/wilderness'">Wilderness</div>
        </div>
        
        <!-- Header Status Bar -->
        <div class="status-bar">
            <div class="status-left">
                <span class="character-name" onclick="showCharacterDropdown()" title="Click to switch characters">{character.name}</span>
                <span class="status-indicator" title="Online">🔴</span>
                <span class="game-time" title="Current game time">🕐 {character.id % 12 + 1}:{(character.id * 7) % 60:02d}am</span>
                <span class="level-stat" title="Experience to next level: {character.experience_needed_for_next_level():,} XP">Level: {character.level}</span>
                <span class="exp-stat" title="Total Experience Points earned">EXP: {character.experience:,}</span>
                <span class="rage-stat" title="Current Rage: {character.rage_current}/{character.rage_max} | Rage regenerates over time">RAGE: {character.rage_current}</span>
            </div>
            <div class="status-right">
                <div class="status-icon equipment-icon" onclick="openFloatingWindow('equipment')" title="Equipment Manager - Manage your gear and weapons">⚔️</div>
                <div class="status-icon inventory-icon" onclick="openFloatingWindow('inventory')" title="Backpack - View and organize your items">🎒</div>
                <div class="status-icon stats-icon" onclick="openFloatingWindow('stats')" title="Character Stats - Detailed character information">📊</div>
                <div class="status-icon tools-icon" onclick="openFloatingWindow('tools')" title="Game Tools - Quick access utilities">🔧</div>
            </div>
        </div>
        
        <!-- Main Game Container -->
        <div class="game-container">
            <!-- Left Sidebar -->
            <div class="left-sidebar">
                <div class="menu-section">
                    <div class="menu-item" onclick="window.location.href='/character/{character.id}'"><span class="menu-icon">📁</span>MY RGA</div>
                    <div class="menu-item active"><span class="menu-icon">🏠</span>HOME</div>
                    <div class="menu-item" onclick="window.location.href='/character/{character.id}'"><span class="menu-icon">👤</span>CHARACTER <span style="margin-left: auto;">▶</span></div>
                    <div class="menu-item" onclick="window.location.href='/marketplace'"><span class="menu-icon">🛒</span>MARKETPLACE <span style="margin-left: auto;">▶</span></div>
                    <div class="menu-item" onclick="window.location.href='/rankings'"><span class="menu-icon">🏆</span>RANKINGS</div>
                    <div class="menu-item" onclick="showActionsMenu()"><span class="menu-icon">⚡</span>ACTIONS <span style="margin-left: auto;">▶</span></div>
                    <div class="menu-item" onclick="window.location.href='/crew'"><span class="menu-icon">👥</span>CREW <span style="margin-left: auto;">▶</span></div>
                    <div class="menu-item" onclick="window.location.href='/casino'"><span class="menu-icon">🎰</span>CASINO <span style="margin-left: auto;">▶</span></div>
                    <div class="menu-item" onclick="window.location.href='/challenges'"><span class="menu-icon">🏅</span>CHALLENGES</div>
                    <div class="menu-item" onclick="window.location.href='/wilderness'"><span class="menu-icon">🌍</span>WILDERNESS</div>
                    {f'<div class="menu-item" onclick="window.location.href=\'/factions\'"><span class="menu-icon">⚔️</span>FACTIONS</div>' if character.level >= 91 else ''}
                </div>
                <div class="get-points-btn" onclick="alert('Points & Tokens system coming soon! This will allow you to purchase premium upgrades and special items.')">GET POINTS + TOKENS</div>
            </div>
            
            <!-- Center Content -->
            <div class="center-content">
                <!-- Main Room Sections Grid -->
                <div class="rooms-grid">
                    <!-- Room Navigation Section -->
                    <div class="room-section">
                        <div class="section-title">- {room_info['zone_name']} -</div>
                        <div class="room-content">
                            <div class="minimap">{minimap_html}</div>
                            
                            <div class="movement-controls">
                                {movement_controls}
                            </div>
                            
                            <div class="hotkeys">
                                <button class="hotkey-btn" onclick="window.location.href='/inventory'">🎒 bag</button>
                                <button class="hotkey-btn" onclick="window.location.href='/crew/vault'">🏛️ my vault</button>
                                <button class="hotkey-btn" onclick="window.location.href='/character/{character.id}'">👤 profile</button>
                                <button class="hotkey-btn" onclick="window.location.href='/rankings'">📊 stats</button>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Room Details Section -->
                    <div class="room-section">
                        <div class="section-title">- Room Details: {character.current_room_id} -</div>
                        <div class="room-content">
                            <div class="room-image">
                                {room_info['name']}<br>
                                <small>{room_info['description']}</small>
                            </div>
                            
                            <div class="action-buttons">
                                <button class="action-btn" onclick="window.location.href='/supplies'">Supplies</button>
                                <button class="action-btn" onclick="window.location.href='/treasury'">Treasury</button>
                                <button class="action-btn" onclick="window.location.href='/challenges'">Dungeons</button>
                                <button class="action-btn" onclick="window.location.href='/wilderness'">Wilderness</button>
                            </div>
                            
                            <div class="npc-list">
                                {npcs_html}
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Recent Activity Section -->
                <div class="room-section full-width">
                    <div class="section-title">- Recent Activity -</div>
                    <div class="room-content">
                        <div style="font-size: 11px; line-height: 1.3;">
                            <div style="margin: 5px 0; color: #ccc;">🔥 <span style="color: #ffd700;">WorkingHero</span> defeated <span style="color: #ff8888;">Bandit Leader</span> (+2,500 exp)</div>
                            <div style="margin: 5px 0; color: #ccc;">💰 <span style="color: #32cd32;">SuccessHero</span> sold <span style="color: #ff8c00;">Mythic Sword</span> for 50,000g</div>
                            <div style="margin: 5px 0; color: #ccc;">⚔️ <span style="color: #ff6666;">TestChar</span> attacked <span style="color: #87ceeb;">EquippedHero</span></div>
                            <div style="margin: 5px 0; color: #ccc;">🏆 <span style="color: #ffd700;">NewTestChar</span> reached level 15</div>
                            <div style="margin: 5px 0; color: #ccc;">🎲 <span style="color: #ff8c00;">FinalTest</span> won 25,000g at the casino</div>
                            <div style="margin: 5px 0; color: #ccc;">🌟 <span style="color: #87ceeb;">boberhunter</span> completed quest "Dragon's Lair"</div>
                        </div>
                    </div>
                </div>
                
                <!-- Server Info Section -->
                <div class="room-section">
                    <div class="section-title">- Server Status -</div>
                    <div class="room-content" style="font-size: 11px;">
                        <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                            <span>Players Online:</span>
                            <span style="color: #32cd32; font-weight: bold;">{random.randint(45, 78)}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                            <span>Active Battles:</span>
                            <span style="color: #ff6666; font-weight: bold;">{random.randint(3, 12)}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                            <span>Market Trades:</span>
                            <span style="color: #ffd700; font-weight: bold;">{random.randint(15, 45)}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                            <span>Server Uptime:</span>
                            <span style="color: #87ceeb; font-weight: bold;">99.8%</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Right Sidebar -->
            <div class="right-sidebar">
                <div class="quest-helper" onclick="window.location.href='/quests'" style="cursor: pointer;">
                    <div class="quest-header">QUEST HELPER</div>
                    <input type="text" class="quest-search" placeholder="Search for a Quest Mob">
                    <div class="quest-target">
                        <div>🧙 Current Target</div>
                        <div style="margin: 10px 0;">
                            <div>Auto Attacker</div>
                            <div>Teleport</div>
                        </div>
                        <div class="quest-status">Status: 0/1 kills</div>
                    </div>
                    <div style="margin-top: 15px; text-align: center; font-size: 10px;">Quest Log</div>
                </div>
            </div>
        </div>
        
        <script>
        function showActionsMenu() {{
            const actions = [
                'Equipment Manager',
                'Inventory Organizer', 
                'Auto-Battle Settings',
                'Trade Center',
                'Quick Stats',
                'Character Settings'
            ];
            
            let actionList = 'Available Actions:\\n\\n';
            actions.forEach((action, index) => {{
                actionList += `${{index + 1}}. ${{action}}\\n`;
            }});
            actionList += '\\nChoose an action (1-6):';
            
            const choice = prompt(actionList);
            
            if (choice) {{
                switch(choice) {{
                    case '1':
                        window.location.href = '/inventory';
                        break;
                    case '2':
                        window.location.href = '/inventory';
                        break;
                    case '3':
                        alert('Auto-Battle: Currently set to MANUAL mode. Configure your battle preferences here.');
                        break;
                    case '4':
                        window.location.href = '/marketplace';
                        break;
                    case '5':
                        window.location.href = '/character/{character.id}';
                        break;
                    case '6':
                        alert('Character Settings: Manage your privacy, notifications, and gameplay preferences.');
                        break;
                    default:
                        alert('Invalid selection.');
                }}
            }}
        }}
        
        function showCharacterDropdown() {{
            // Toggle character dropdown visibility
            let dropdown = document.querySelector('.character-dropdown');
            if (!dropdown) {{
                // Create dropdown if it doesn't exist
                dropdown = document.createElement('div');
                dropdown.className = 'character-dropdown';
                dropdown.innerHTML = `
                    <div class="dropdown-item" onclick="switchCharacter('{character.id}')">
                        <strong>{character.name}</strong> (Level {character.level}) - Current
                    </div>
                    <div class="dropdown-item" onclick="window.location.href='/characters'">
                        ➕ Create New Character
                    </div>
                    <div class="dropdown-item" onclick="window.location.href='/characters'">
                        🔄 Switch Character
                    </div>
                `;
                document.body.appendChild(dropdown);
            }}
            dropdown.classList.toggle('show');
        }}
        
        function switchCharacter(characterId) {{
            // Hide dropdown
            document.querySelector('.character-dropdown').classList.remove('show');
            if (characterId !== '{character.id}') {{
                window.location.href = '/characters';
            }}
        }}
        
        function openFloatingWindow(type) {{
            // Close any existing floating windows
            document.querySelectorAll('.floating-window').forEach(w => w.classList.remove('show'));
            
            let window = document.getElementById(type + 'Window');
            if (!window) {{
                // Create floating window
                window = document.createElement('div');
                window.id = type + 'Window';
                window.className = 'floating-window';
                window.style.left = '50%';
                window.style.top = '50%';
                window.style.transform = 'translate(-50%, -50%)';
                
                let content = '';
                switch(type) {{
                    case 'equipment':
                        content = `
                            <div class="window-header">
                                <span class="window-title">⚔️ Equipment Manager</span>
                                <span class="window-close" onclick="closeFloatingWindow('${{type}}')">&times;</span>
                            </div>
                            <div class="window-content">
                                <div style="text-align: center; padding: 20px;">
                                    <div style="margin-bottom: 15px;">🛡️ Equipment slots and stats</div>
                                    <div style="margin-bottom: 15px;">⚔️ Total damage: {character.get_total_elemental_damage()}</div>
                                    <div style="margin-bottom: 15px;">🛡️ Total defense: {character.get_effective_defense()}</div>
                                    <button onclick="window.location.href='/character/{character.id}'" style="padding: 8px 16px; background: #ffd700; color: #000; border: none; border-radius: 4px; cursor: pointer;">View Full Equipment</button>
                                </div>
                            </div>
                        `;
                        break;
                    case 'inventory':
                        content = `
                            <div class="window-header">
                                <span class="window-title">🎒 Inventory</span>
                                <span class="window-close" onclick="closeFloatingWindow('${{type}}')">&times;</span>
                            </div>
                            <div class="window-content">
                                <div style="text-align: center; padding: 20px;">
                                    <div style="margin-bottom: 15px;">📦 Quick inventory access</div>
                                    <div style="margin-bottom: 15px;">💰 Gold: {character.gold:,}</div>
                                    <div style="margin-bottom: 15px;">🎒 Items: Coming soon</div>
                                    <button onclick="window.location.href='/inventory'" style="padding: 8px 16px; background: #ffd700; color: #000; border: none; border-radius: 4px; cursor: pointer;">Open Full Inventory</button>
                                </div>
                            </div>
                        `;
                        break;
                    case 'stats':
                        content = `
                            <div class="window-header">
                                <span class="window-title">📊 Character Stats</span>
                                <span class="window-close" onclick="closeFloatingWindow('${{type}}')">&times;</span>
                            </div>
                            <div class="window-content">
                                <div style="padding: 20px;">
                                    <div style="margin-bottom: 10px;"><strong>Level:</strong> {character.level}</div>
                                    <div style="margin-bottom: 10px;"><strong>Experience:</strong> {character.experience:,}</div>
                                    <div style="margin-bottom: 10px;"><strong>Health:</strong> {character.hit_points_current}/{character.hit_points_max}</div>
                                    <div style="margin-bottom: 10px;"><strong>Rage:</strong> {character.rage_current}/{character.rage_max}</div>
                                    <div style="margin-bottom: 15px;"><strong>Power:</strong> {character.total_power:,}</div>
                                    <button onclick="window.location.href='/character/{character.id}'" style="padding: 8px 16px; background: #ffd700; color: #000; border: none; border-radius: 4px; cursor: pointer;">Detailed Stats</button>
                                </div>
                            </div>
                        `;
                        break;
                    case 'tools':
                        content = `
                            <div class="window-header">
                                <span class="window-title">🔧 Game Tools</span>
                                <span class="window-close" onclick="closeFloatingWindow('${{type}}')">&times;</span>
                            </div>
                            <div class="window-content">
                                <div style="padding: 20px;">
                                    <div style="margin-bottom: 10px;"><button onclick="window.location.href='/marketplace'" style="width: 100%; padding: 8px; background: #444; color: white; border: none; border-radius: 4px; cursor: pointer; margin-bottom: 5px;">🛒 Marketplace</button></div>
                                    <div style="margin-bottom: 10px;"><button onclick="window.location.href='/rankings'" style="width: 100%; padding: 8px; background: #444; color: white; border: none; border-radius: 4px; cursor: pointer; margin-bottom: 5px;">🏆 Rankings</button></div>
                                    <div style="margin-bottom: 10px;"><button onclick="window.location.href='/crew'" style="width: 100%; padding: 8px; background: #444; color: white; border: none; border-radius: 4px; cursor: pointer; margin-bottom: 5px;">👥 Crew</button></div>
                                    <div style="margin-bottom: 10px;"><button onclick="window.location.href='/quests'" style="width: 100%; padding: 8px; background: #444; color: white; border: none; border-radius: 4px; cursor: pointer; margin-bottom: 5px;">📜 Quests</button></div>
                                </div>
                            </div>
                        `;
                        break;
                }}
                
                window.innerHTML = content;
                document.body.appendChild(window);
                
                // Make window draggable
                makeDraggable(window);
            }}
            
            window.classList.add('show');
        }}
        
        function closeFloatingWindow(type) {{
            const window = document.getElementById(type + 'Window');
            if (window) {{
                window.classList.remove('show');
            }}
        }}
        
        function makeDraggable(element) {{
            let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
            const header = element.querySelector('.window-header');
            
            if (header) {{
                header.onmousedown = dragMouseDown;
            }}
            
            function dragMouseDown(e) {{
                e = e || window.event;
                e.preventDefault();
                pos3 = e.clientX;
                pos4 = e.clientY;
                document.onmouseup = closeDragElement;
                document.onmousemove = elementDrag;
            }}
            
            function elementDrag(e) {{
                e = e || window.event;
                e.preventDefault();
                pos1 = pos3 - e.clientX;
                pos2 = pos4 - e.clientY;
                pos3 = e.clientX;
                pos4 = e.clientY;
                element.style.top = (element.offsetTop - pos2) + "px";
                element.style.left = (element.offsetLeft - pos1) + "px";
                element.style.transform = 'none';
            }}
            
            function closeDragElement() {{
                document.onmouseup = null;
                document.onmousemove = null;
            }}
        }}
        
        // Close dropdowns/windows when clicking outside
        document.addEventListener('click', function(event) {{
            if (!event.target.closest('.character-name') && !event.target.closest('.character-dropdown')) {{
                const dropdown = document.querySelector('.character-dropdown');
                if (dropdown) {{
                    dropdown.classList.remove('show');
                }}
            }}
        }});
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

def generate_minimap(current_room_id, connections):
    """Generate visual minimap with CSS"""
    # Create a visual grid-based minimap
    available_directions = [conn['direction'].lower() for conn in connections]
    
    # Build minimap grid HTML
    minimap_html = f'''
    <div style="display: grid; grid-template-columns: repeat(5, 25px); grid-gap: 2px; justify-content: center; margin: 10px 0;">
        <!-- Row 1 -->
        <div class="minimap-cell unknown"></div>
        <div class="minimap-cell {'available' if 'north' in available_directions else 'unknown'}" title="North">{'🚪' if 'north' in available_directions else '⬛'}</div>
        <div class="minimap-cell unknown"></div>
        <div class="minimap-cell {'available' if 'northeast' in available_directions else 'unknown'}" title="Northeast">{'🚪' if 'northeast' in available_directions else '⬛'}</div>
        <div class="minimap-cell unknown"></div>
        
        <!-- Row 2 -->
        <div class="minimap-cell {'available' if 'northwest' in available_directions else 'unknown'}" title="Northwest">{'🚪' if 'northwest' in available_directions else '⬛'}</div>
        <div class="minimap-cell {'available' if 'west' in available_directions else 'unknown'}" title="West">{'🚪' if 'west' in available_directions else '⬛'}</div>
        <div class="minimap-cell current" title="Current Location">👤</div>
        <div class="minimap-cell {'available' if 'east' in available_directions else 'unknown'}" title="East">{'🚪' if 'east' in available_directions else '⬛'}</div>
        <div class="minimap-cell {'available' if 'southeast' in available_directions else 'unknown'}" title="Southeast">{'🚪' if 'southeast' in available_directions else '⬛'}</div>
        
        <!-- Row 3 -->
        <div class="minimap-cell unknown"></div>
        <div class="minimap-cell {'available' if 'south' in available_directions else 'unknown'}" title="South">{'🚪' if 'south' in available_directions else '⬛'}</div>
        <div class="minimap-cell unknown"></div>
        <div class="minimap-cell {'available' if 'southwest' in available_directions else 'unknown'}" title="Southwest">{'🚪' if 'southwest' in available_directions else '⬛'}</div>
        <div class="minimap-cell unknown"></div>
    </div>
    
    <style>
    .minimap-cell {{
        width: 25px;
        height: 25px;
        border: 1px solid #666;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
        border-radius: 3px;
    }}
    .minimap-cell.current {{
        background: linear-gradient(45deg, #ffd700, #ffeb3b);
        border-color: #ff8c00;
        color: #000;
        font-size: 12px;
        box-shadow: 0 0 8px rgba(255, 215, 0, 0.6);
    }}
    .minimap-cell.available {{
        background: linear-gradient(45deg, #32cd32, #90ee90);
        border-color: #00aa00;
        cursor: pointer;
    }}
    .minimap-cell.available:hover {{
        background: linear-gradient(45deg, #90ee90, #98fb98);
        transform: scale(1.1);
    }}
    .minimap-cell.unknown {{
        background: #333;
        border-color: #555;
        color: #666;
    }}
    </style>
    '''
    
    return minimap_html

def generate_movement_controls(connections):
    """Generate WASD movement controls"""
    # Check which directions are available
    available_directions = [conn['direction'].lower() for conn in connections]
    
    # Create movement buttons
    controls = """
    <div class="movement-row">
        <button class="move-btn" {w_state} onclick="move('north')">W</button>
    </div>
    <div class="movement-row">
        <button class="move-btn" {a_state} onclick="move('west')">A</button>
        <button class="move-btn" {s_state} onclick="move('south')">S</button>
        <button class="move-btn" {d_state} onclick="move('east')">D</button>
    </div>
    """.format(
        w_state="" if "north" in available_directions else "disabled",
        a_state="" if "west" in available_directions else "disabled", 
        s_state="" if "south" in available_directions else "disabled",
        d_state="" if "east" in available_directions else "disabled"
    )
    
    # Add JavaScript for movement
    controls += """
    <script>
    function move(direction) {
        fetch('/move/' + direction, {method: 'POST'})
        .then(() => location.reload());
    }
    </script>
    """
    
    return controls

async def room_detail(request: web_request.Request):
    """Detailed view of a specific room"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    room_id = int(request.match_info['room_id'])
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        room_info = await database.queries.get_room_info(conn, room_id)
        if not room_info:
            raise web.HTTPNotFound()
        
        connections = await database.queries.get_room_connections(conn, room_id)
        characters_in_room = await database.queries.get_characters_in_room(conn, room_id)
    
    # Build connections list
    connections_html = ""
    for connection in connections:
        connections_html += f"""
        <li><strong>{connection['direction'].title()}:</strong> <a href="/room/{connection['to_room_id']}">{connection['room_name']}</a></li>
        """
    
    # Build character list
    characters_html = ""
    for char in characters_in_room:
        characters_html += f"""
        <li>{char['name']} (Level {char['level']} {char['class_name']}, Power: {char['total_power']:,})</li>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{room_info['name']} - Room Details</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }}
            .title {{ color: #ff6600; }}
            .nav a {{ color: #ff6600; text-decoration: none; padding: 10px 15px; background: #333; border-radius: 5px; margin-left: 10px; }}
            .room-detail {{ background: #333; padding: 30px; border-radius: 10px; }}
            .room-name {{ color: #ff6600; font-size: 2em; margin-bottom: 15px; }}
            .section {{ margin: 25px 0; }}
            .section h3 {{ color: #ff6600; }}
            ul {{ list-style-type: none; padding-left: 0; }}
            li {{ background: #444; padding: 10px; margin: 5px 0; border-radius: 5px; }}
            a {{ color: #88ccff; text-decoration: none; }}
            a:hover {{ color: #aaddff; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 class="title">ROOM DETAILS</h1>
            <div class="nav">
                <a href="/game">BACK TO GAME</a>
            </div>
        </div>
        
        <div class="room-detail">
            <div class="room-name">{room_info['name']}</div>
            <p>{room_info['description']}</p>
            <p><em>Zone: {room_info['zone_name']} - {room_info['zone_description']}</em></p>
            
            <div class="section">
                <h3>Connections</h3>
                <ul>
                    {connections_html if connections_html else '<li>No connections available.</li>'}
                </ul>
            </div>
            
            <div class="section">
                <h3>Characters Present</h3>
                <ul>
                    {characters_html if characters_html else '<li>No characters in this room.</li>'}
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def move_character(request: web_request.Request):
    """Move character in specified direction"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    direction = request.match_info['direction'].lower()
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        # Get possible connections from current room
        connections = await database.queries.get_room_connections(conn, room_id=character.current_room_id)
        
        # Find the connection for this direction
        target_room = None
        for connection in connections:
            if connection['direction'].lower() == direction:
                target_room = connection['to_room_id']
                break
        
        if not target_room:
            # Invalid direction
            raise web.HTTPBadRequest(text="Invalid direction")
        
        # Move character
        await database.queries.move_character(conn, room_id=target_room, character_id=character.id)
        await conn.commit()
    
    raise web.HTTPFound('/game')