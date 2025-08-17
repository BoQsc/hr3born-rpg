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
        
        # Get real server statistics
        result = await database.queries.count_total_characters(conn)
        total_characters = result['total'] if result else 0
        # Simulate more realistic numbers based on actual data
        players_online = min(total_characters, max(3, int(total_characters * 0.3)))  # 30% online
        active_battles = max(0, int(players_online * 0.1))  # 10% of online players in battles
        market_trades = max(0, int(players_online * 0.2))  # 20% active in marketplace
    
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
            
            /* Minimap Container */
            .minimap {{ 
                max-width: 100%; 
                display: flex; 
                flex-direction: column; 
                align-items: center; 
                margin: 10px auto; 
                background: transparent;
            }}
            
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
                            <div style="margin: 5px 0; color: #ccc;">🔥 <a href="/character/3" style="color: #ffd700; text-decoration: none; font-weight: bold;">WorkingHero</a> defeated <span style="color: #ff8888;">Bandit Leader</span> (+2,500 exp)</div>
                            <div style="margin: 5px 0; color: #ccc;">💰 <a href="/character/4" style="color: #32cd32; text-decoration: none; font-weight: bold;">SuccessHero</a> sold <span style="color: #ff8c00;">Mythic Sword</span> for 50,000g</div>
                            <div style="margin: 5px 0; color: #ccc;">⚔️ <a href="/character/1" style="color: #ff6666; text-decoration: none; font-weight: bold;">TestChar</a> attacked <a href="/character/5" style="color: #87ceeb; text-decoration: none; font-weight: bold;">EquippedHero</a></div>
                            <div style="margin: 5px 0; color: #ccc;">🏆 <a href="/character/6" style="color: #ffd700; text-decoration: none; font-weight: bold;">NewTestChar</a> reached level 15</div>
                            <div style="margin: 5px 0; color: #ccc;">🎲 <a href="/character/2" style="color: #ff8c00; text-decoration: none; font-weight: bold;">FinalTest</a> won 25,000g at the casino</div>
                            <div style="margin: 5px 0; color: #ccc;">🌟 <a href="/character/7" style="color: #87ceeb; text-decoration: none; font-weight: bold;">boberhunter</a> completed quest "Dragon's Lair"</div>
                        </div>
                    </div>
                </div>
                
                <!-- Server Info Section -->
                <div class="room-section">
                    <div class="section-title">- Server Status -</div>
                    <div class="room-content" style="font-size: 11px;">
                        <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                            <span>Players Online:</span>
                            <span style="color: #32cd32; font-weight: bold;">{players_online}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                            <span>Active Battles:</span>
                            <span style="color: #ff6666; font-weight: bold;">{active_battles}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin: 5px 0;">
                            <span>Market Trades:</span>
                            <span style="color: #ffd700; font-weight: bold;">{market_trades}</span>
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
        
        // Keyboard hotkeys
        document.addEventListener('keydown', function(event) {{
            // Only trigger if not in an input field
            if (event.target.tagName.toLowerCase() !== 'input' && event.target.tagName.toLowerCase() !== 'textarea') {{
                switch(event.key.toLowerCase()) {{
                    case 'e':
                        event.preventDefault();
                        openFloatingWindow('equipment');
                        break;
                    case 'b':
                        event.preventDefault();
                        window.location.href = '/inventory';
                        break;
                    case 'q':
                        event.preventDefault();
                        window.location.href = '/quests';
                        break;
                    case 'w':
                        event.preventDefault();
                        move('north');
                        break;
                    case 'a':
                        event.preventDefault();
                        move('west');
                        break;
                    case 's':
                        event.preventDefault();
                        move('south');
                        break;
                    case 'd':
                        event.preventDefault();
                        move('east');
                        break;
                }}
            }}
        }});
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

def generate_minimap(current_room_id, connections):
    """Generate street-based city minimap with walkable paths"""
    available_directions = [conn['direction'].lower() for conn in connections]
    
    # 10x10 grid for proper city layout
    grid_size = 10
    center = 4  # Current location at center
    
    # Initialize grid - all streets by default for walkable city
    grid = [['street' for _ in range(grid_size)] for _ in range(grid_size)]
    
    # Add buildings and landmarks at intersections (even positions)
    landmarks = {
        (0, 0): 'building', (0, 2): 'park', (0, 4): 'building', (0, 6): 'shop', (0, 8): 'building',
        (2, 0): 'shop', (2, 2): 'building', (2, 6): 'building', (2, 8): 'park',
        (4, 0): 'building', (4, 2): 'park', (4, 6): 'shop', (4, 8): 'building',
        (6, 0): 'park', (6, 2): 'building', (6, 6): 'building', (6, 8): 'shop',
        (8, 0): 'building', (8, 2): 'shop', (8, 4): 'building', (8, 6): 'park', (8, 8): 'building'
    }
    
    # Place buildings and landmarks
    for (row, col), landmark_type in landmarks.items():
        if 0 <= row < grid_size and 0 <= col < grid_size:
            grid[row][col] = landmark_type
    
    # Place special destinations based on available directions
    destinations = {
        'north': (0, center, 'cityhall'),      # City Hall to the north
        'south': (8, center, 'arena'),         # Arena to the south  
        'east': (center, 8, 'casino'),         # Casino to the east
        'west': (center, 0, 'marketplace'),    # Marketplace to the west
        'northeast': (0, 8, 'temple'),         # Temple northeast
        'northwest': (0, 0, 'barracks'),       # Barracks northwest
        'southeast': (8, 8, 'tavern'),         # Tavern southeast
        'southwest': (8, 0, 'bank')            # Bank southwest
    }
    
    # Add destination buildings for available directions
    for direction in available_directions:
        if direction in destinations:
            dest_row, dest_col, dest_type = destinations[direction]
            if 0 <= dest_row < grid_size and 0 <= dest_col < grid_size:
                grid[dest_row][dest_col] = dest_type
    
    # Mark current location
    grid[center][center] = 'current'
    
    # Create walkable paths to accessible destinations
    for direction in available_directions:
        if direction in destinations:
            dest_row, dest_col, _ = destinations[direction]
            
            # Create path from center to destination
            current_row, current_col = center, center
            
            # Step towards destination
            while current_row != dest_row or current_col != dest_col:
                if current_row < dest_row:
                    current_row += 1
                elif current_row > dest_row:
                    current_row -= 1
                    
                if current_col < dest_col:
                    current_col += 1
                elif current_col > dest_col:
                    current_col -= 1
                
                # Mark path as walkable street (don't overwrite buildings)
                if 0 <= current_row < grid_size and 0 <= current_col < grid_size:
                    if grid[current_row][current_col] not in ['current'] + list(landmarks.values()) + [dest[2] for dest in destinations.values()]:
                        grid[current_row][current_col] = 'path'
    
    # Mark immediate adjacent streets as highlighted paths
    for direction in available_directions:
        if direction == 'north' and center-1 >= 0:
            grid[center-1][center] = 'path'
        elif direction == 'south' and center+1 < grid_size:
            grid[center+1][center] = 'path'
        elif direction == 'east' and center+1 < grid_size:
            grid[center][center+1] = 'path'
        elif direction == 'west' and center-1 >= 0:
            grid[center][center-1] = 'path'
        elif direction == 'northeast' and center-1 >= 0 and center+1 < grid_size:
            grid[center-1][center+1] = 'path'
        elif direction == 'northwest' and center-1 >= 0 and center-1 >= 0:
            grid[center-1][center-1] = 'path'
        elif direction == 'southeast' and center+1 < grid_size and center+1 < grid_size:
            grid[center+1][center+1] = 'path'
        elif direction == 'southwest' and center+1 < grid_size and center-1 >= 0:
            grid[center+1][center-1] = 'path'
    
    # Build minimap with proper container sizing
    minimap_html = f'''
    <div style="
        display: grid; 
        grid-template-columns: repeat({grid_size}, 1fr); 
        grid-template-rows: repeat({grid_size}, 1fr);
        width: 300px; 
        height: 300px; 
        gap: 1px; 
        background: #2a2a2a; 
        padding: 10px; 
        border-radius: 8px; 
        border: 2px solid #666;
        margin: 0 auto;
    ">'''
    
    symbols = {
        'current': '👤',
        'street': '⬜',
        'path': '🟨',
        'building': '🏢',
        'park': '🌳',
        'shop': '🏪',
        'cityhall': '🏛️',
        'arena': '🏟️',
        'casino': '🎰',
        'marketplace': '🛒',
        'temple': '⛪',
        'barracks': '🏰',
        'tavern': '🍺',
        'bank': '🏦'
    }
    
    for row in range(grid_size):
        for col in range(grid_size):
            cell_type = grid[row][col]
            symbol = symbols.get(cell_type, '❓')
            
            # Determine if cell is clickable
            is_clickable = False
            direction = None
            
            # Check if this is a destination reachable in one of the available directions
            for dir_name in available_directions:
                if dir_name in destinations:
                    dest_row, dest_col, dest_type = destinations[dir_name]
                    if row == dest_row and col == dest_col:
                        is_clickable = True
                        direction = dir_name
                        break
            
            # Only make tiles clickable that correspond to actual available room connections
            if not is_clickable and cell_type in ['path', 'street']:
                # Calculate relative position to determine direction
                row_diff = row - center
                col_diff = col - center
                
                # Only make immediately adjacent tiles clickable (1 step away)
                if abs(row_diff) <= 1 and abs(col_diff) <= 1 and (row_diff != 0 or col_diff != 0):
                    # Determine direction based on position
                    if row_diff == -1 and col_diff == 0:
                        direction = 'north'
                    elif row_diff == 1 and col_diff == 0:
                        direction = 'south'
                    elif row_diff == 0 and col_diff == 1:
                        direction = 'east'
                    elif row_diff == 0 and col_diff == -1:
                        direction = 'west'
                    elif row_diff == -1 and col_diff == 1:
                        direction = 'northeast'
                    elif row_diff == -1 and col_diff == -1:
                        direction = 'northwest'
                    elif row_diff == 1 and col_diff == 1:
                        direction = 'southeast'
                    elif row_diff == 1 and col_diff == -1:
                        direction = 'southwest'
                    
                    # Only make it clickable if this direction is actually available in the database
                    if direction and direction in available_directions:
                        is_clickable = True
            
            # Style based on cell type
            if cell_type == 'current':
                style = 'background: linear-gradient(45deg, #ffd700, #ffeb3b); color: #000; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 16px; border: 2px solid #ff8c00; box-shadow: 0 0 8px rgba(255, 215, 0, 0.8);'
            elif cell_type == 'path':
                style = 'background: linear-gradient(45deg, #90ee90, #32cd32); color: #000; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 12px; border: 1px solid #00aa00;'
                if is_clickable:
                    style += ' cursor: pointer; box-shadow: 0 0 6px rgba(50, 205, 50, 0.7);'
            elif cell_type == 'street':
                style = 'background: #666; color: #999; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 10px; border: 1px solid #777;'
                if is_clickable:
                    style += ' cursor: pointer; box-shadow: 0 0 4px rgba(150, 150, 150, 0.6); border-color: #999;'
            elif cell_type in ['cityhall', 'arena', 'casino', 'marketplace', 'temple', 'barracks', 'tavern', 'bank']:
                # Special destinations - make them stand out and clickable if accessible
                style = 'background: linear-gradient(45deg, #4169e1, #1e90ff); color: #fff; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 14px; border: 2px solid #0066cc;'
                if is_clickable:
                    style += ' cursor: pointer; box-shadow: 0 0 10px rgba(65, 105, 225, 0.8);'
            else:
                # Regular buildings, parks, shops
                style = 'background: #4a4a4a; color: #888; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 12px; border: 1px solid #555;'
            
            onclick = f'onclick="move(\'{direction}\')"' if is_clickable else ''
            title = f'title="{cell_type.replace("_", " ").title()}"'
            if is_clickable:
                if cell_type == 'street':
                    title = f'title="Walk {direction} down the street"'
                elif cell_type == 'path':
                    title = f'title="Follow path {direction}"'
                else:
                    title = f'title="Go {direction} to {cell_type.replace("_", " ").title()}"'
            
            minimap_html += f'<div style="{style}" {onclick} {title}>{symbol}</div>'
    
    minimap_html += '</div>'
    minimap_html += '<div style="text-align: center; font-size: 11px; color: #aaa; margin-top: 8px;">🌟 Diamond City Streets - Click any adjacent street, path, or building to walk around</div>'
    
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
        console.log('Attempting to move:', direction);
        
        fetch('/move/' + direction, {
            method: 'POST',
            credentials: 'same-origin'  // Include session cookies
        })
        .then(response => {
            console.log('Movement response:', response.status, response.type);
            
            // Server always redirects on successful movement
            if (response.redirected || response.status === 302 || response.type === 'opaqueredirect') {
                console.log('Movement successful, reloading page');
                // Follow the redirect by reloading
                window.location.reload();
            } else if (response.status === 400) {
                console.error('Invalid direction');
                alert('Cannot move in that direction');
            } else if (response.status === 401 || response.status === 403) {
                console.error('Authentication error');
                window.location.href = '/login';
            } else {
                console.error('Unexpected response:', response.status);
                response.text().then(text => {
                    console.error('Response text:', text);
                    alert('Movement failed: ' + text);
                });
            }
        })
        .catch(error => {
            console.error('Movement network error:', error);
            alert('Network error during movement: ' + error.message);
        });
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
    try:
        await require_login(request)
        character = await get_current_character(request)
        
        if not character:
            print(f"[MOVEMENT] No character found, redirecting to character selection")
            raise web.HTTPFound('/characters')
        
        direction = request.match_info['direction'].lower()
        print(f"[MOVEMENT] Character {character.name} attempting to move {direction} from room {character.current_room_id}")
        
        database = await get_db()
        async with database.get_connection_context() as conn:
            # Get possible connections from current room
            connections = await database.queries.get_room_connections(conn, room_id=character.current_room_id)
            available_directions = [conn['direction'].lower() for conn in connections]
            print(f"[MOVEMENT] Available directions from room {character.current_room_id}: {available_directions}")
            
            # Find the connection for this direction
            target_room = None
            for connection in connections:
                if connection['direction'].lower() == direction:
                    target_room = connection['to_room_id']
                    break
            
            if not target_room:
                print(f"[MOVEMENT] Invalid direction '{direction}' from room {character.current_room_id}")
                raise web.HTTPBadRequest(text=f"Cannot move {direction} from this location")
            
            print(f"[MOVEMENT] Moving character {character.id} from room {character.current_room_id} to room {target_room}")
            
            # Move character
            await database.queries.move_character(conn, room_id=target_room, character_id=character.id)
            await conn.commit()
            
            print(f"[MOVEMENT] Movement successful! Character now in room {target_room}")
        
        raise web.HTTPFound('/game')
        
    except Exception as e:
        print(f"[MOVEMENT ERROR] {type(e).__name__}: {e}")
        raise
