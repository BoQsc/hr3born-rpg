from aiohttp import web, web_request
from typing import Dict, List

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
            .status-icon {{ width: 16px; height: 16px; border-radius: 50%; background: #333; }}
            
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
            .room-section {{ background: #2d2d2d; border: 1px solid #555; border-radius: 8px; margin-bottom: 20px; }}
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
            .npc-list {{ }}
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
            <div class="nav-tab">Dungeons</div>
            <div class="nav-tab">Challenges</div>
            <div class="nav-tab">All docs</div>
            <div class="nav-tab">News</div>
            <div class="nav-tab">Discord</div>
        </div>
        
        <!-- Header Status Bar -->
        <div class="status-bar">
            <div class="status-left">
                <span>{character.name}</span>
                <span>🔴</span>
                <span>🕐 {character.id % 12 + 1}:{(character.id * 7) % 60:02d}am</span>
                <span>Level: {character.level}</span>
                <span>EXP: {character.experience:,}</span>
                <span>RAGE: {character.rage_current}</span>
            </div>
            <div class="status-right">
                <div class="status-icon"></div>
                <div class="status-icon"></div>
                <div class="status-icon"></div>
                <div class="status-icon"></div>
            </div>
        </div>
        
        <!-- Main Game Container -->
        <div class="game-container">
            <!-- Left Sidebar -->
            <div class="left-sidebar">
                <div class="menu-section">
                    <div class="menu-item"><span class="menu-icon">📁</span>MY RGA</div>
                    <div class="menu-item active"><span class="menu-icon">🏠</span>HOME</div>
                    <div class="menu-item"><span class="menu-icon">👤</span>CHARACTER <span style="margin-left: auto;">▶</span></div>
                    <div class="menu-item"><span class="menu-icon">🛒</span>MARKETPLACE <span style="margin-left: auto;">▶</span></div>
                    <div class="menu-item"><span class="menu-icon">🏆</span>RANKINGS</div>
                    <div class="menu-item"><span class="menu-icon">⚡</span>ACTIONS <span style="margin-left: auto;">▶</span></div>
                    <div class="menu-item"><span class="menu-icon">👥</span>CREW <span style="margin-left: auto;">▶</span></div>
                    <div class="menu-item"><span class="menu-icon">🎰</span>CASINO <span style="margin-left: auto;">▶</span></div>
                    <div class="menu-item"><span class="menu-icon">🏅</span>CHALLENGES</div>
                    <div class="menu-item"><span class="menu-icon">🌍</span>WORLD</div>
                </div>
                <div class="get-points-btn">GET POINTS + TOKENS</div>
            </div>
            
            <!-- Center Content -->
            <div class="center-content">
                <!-- Underground Casino Section -->
                <div class="room-section">
                    <div class="section-title">- {room_info['zone_name']} -</div>
                    <div class="room-content">
                        <div class="minimap">{minimap_html}</div>
                        
                        <div class="movement-controls">
                            {movement_controls}
                        </div>
                        
                        <div class="hotkeys">
                            <button class="hotkey-btn">🎒 bag</button>
                            <button class="hotkey-btn">🏛️ my vault</button>
                            <button class="hotkey-btn">👤 profile</button>
                            <button class="hotkey-btn">📊 stats</button>
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
                            <button class="action-btn">Supplies</button>
                            <button class="action-btn">Treasury</button>
                            <button class="action-btn">Dungeons</button>
                            <button class="action-btn">Wilderness</button>
                        </div>
                        
                        <div class="npc-list">
                            {npcs_html}
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Right Sidebar -->
            <div class="right-sidebar">
                <div class="quest-helper">
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
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

def generate_minimap(current_room_id, connections):
    """Generate ASCII-style minimap"""
    # Simple 5x3 grid minimap centered on current room
    minimap = [
        ['░', '░', '░', '░', '░'],
        ['░', '?', '█', '?', '░'],
        ['░', '░', '░', '░', '░']
    ]
    
    # Mark current room
    minimap[1][2] = '◆'  # Current position
    
    # Add connections
    connection_map = {
        'north': (0, 2),
        'south': (2, 2),
        'east': (1, 3),
        'west': (1, 1),
        'northeast': (0, 3),
        'northwest': (0, 1),
        'southeast': (2, 3),
        'southwest': (2, 1)
    }
    
    for conn in connections:
        direction = conn['direction'].lower()
        if direction in connection_map:
            y, x = connection_map[direction]
            minimap[y][x] = '□'  # Available room
    
    # Convert to string
    result = ""
    for row in minimap:
        result += ' '.join(row) + '\n'
    
    return result

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