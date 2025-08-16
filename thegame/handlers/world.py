from aiohttp import web, web_request
from typing import Dict, List

from database import get_db
from handlers.auth import require_login
from handlers.character import get_current_character

async def game_main(request: web_request.Request):
    """Main game interface"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    database = await get_db()
    async with database.get_connection() as conn:
        # Get current room info
        room_info = await database.queries.get_room_info(conn, character.current_room_id)
        connections = await database.queries.get_room_connections(conn, character.current_room_id)
        characters_in_room = await database.queries.get_characters_in_room(conn, character.current_room_id)
    
    # Build movement options
    movement_html = ""
    for connection in connections:
        movement_html += f"""
        <form method="post" action="/move/{connection['direction']}" style="display: inline; margin: 5px;">
            <button type="submit" class="btn-move">{connection['direction'].upper()}</button>
        </form>
        """
    
    # Build character list (excluding current character)
    characters_html = ""
    for char in characters_in_room:
        if char['id'] != character.id:
            characters_html += f"""
            <div class="character-card">
                <div class="char-info">
                    <strong>{char['name']}</strong><br>
                    Level {char['level']} {char['class_name']}<br>
                    Power: {char['total_power']:,}
                </div>
                <div class="char-actions">
                    <form method="post" action="/attack/{char['id']}" style="display: inline;">
                        <button type="submit" class="btn-attack">ATTACK</button>
                    </form>
                </div>
            </div>
            """
    
    if not characters_html:
        characters_html = "<p>No other players in this area.</p>"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Game - {character.name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background: #1a1a1a; color: #fff; }}
            .game-layout {{ display: grid; grid-template-columns: 250px 1fr 300px; grid-template-rows: 60px 1fr; height: 100vh; }}
            
            .header {{ grid-column: 1 / -1; background: #333; padding: 15px; display: flex; justify-content: space-between; align-items: center; }}
            .header h1 {{ margin: 0; color: #ff6600; font-size: 1.5em; }}
            .header .nav {{ display: flex; gap: 15px; }}
            .header .nav a {{ color: #ff6600; text-decoration: none; padding: 8px 15px; background: #555; border-radius: 5px; }}
            
            .sidebar {{ background: #2a2a2a; padding: 20px; overflow-y: auto; }}
            .sidebar h3 {{ color: #ff6600; margin-top: 0; }}
            .stat-bar {{ margin: 10px 0; }}
            .stat-label {{ display: flex; justify-content: space-between; font-size: 0.9em; }}
            .stat-progress {{ width: 100%; height: 20px; background: #555; border-radius: 10px; margin-top: 5px; }}
            .stat-fill {{ height: 100%; border-radius: 10px; }}
            .hp-fill {{ background: #ff4444; }}
            .rage-fill {{ background: #4444ff; }}
            .exp-fill {{ background: #44ff44; }}
            
            .main-area {{ background: #333; padding: 20px; overflow-y: auto; }}
            .room-info {{ background: #444; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
            .room-name {{ color: #ff6600; font-size: 1.5em; margin-bottom: 10px; }}
            .movement {{ margin: 20px 0; }}
            .btn-move {{ padding: 8px 15px; margin: 5px; background: #00aa00; color: white; border: none; border-radius: 5px; cursor: pointer; }}
            .btn-move:hover {{ background: #00cc00; }}
            
            .players-area {{ background: #2a2a2a; padding: 20px; overflow-y: auto; }}
            .character-card {{ background: #444; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #ff6600; }}
            .char-info {{ margin-bottom: 10px; }}
            .btn-attack {{ padding: 5px 10px; background: #ff4444; color: white; border: none; border-radius: 3px; cursor: pointer; }}
            .btn-attack:hover {{ background: #ff6666; }}
        </style>
    </head>
    <body>
        <div class="game-layout">
            <div class="header">
                <h1>{character.name} - Level {character.level}</h1>
                <div class="nav">
                    <a href="/character/{character.id}">CHARACTER</a>
                    <a href="/inventory">INVENTORY</a>
                    <a href="/crew">CREW</a>
                    <a href="/combat/history">COMBAT</a>
                    <a href="/characters">CHARACTERS</a>
                </div>
            </div>
            
            <div class="sidebar">
                <h3>CHARACTER STATUS</h3>
                
                <div class="stat-bar">
                    <div class="stat-label">
                        <span>Hit Points</span>
                        <span>{character.hit_points_current}/{character.hit_points_max}</span>
                    </div>
                    <div class="stat-progress">
                        <div class="stat-fill hp-fill" style="width: {(character.hit_points_current/character.hit_points_max)*100:.1f}%;"></div>
                    </div>
                </div>
                
                <div class="stat-bar">
                    <div class="stat-label">
                        <span>Rage</span>
                        <span>{character.rage_current}/{character.rage_max}</span>
                    </div>
                    <div class="stat-progress">
                        <div class="stat-fill rage-fill" style="width: {(character.rage_current/character.rage_max)*100:.1f}%;"></div>
                    </div>
                </div>
                
                <div class="stat-bar">
                    <div class="stat-label">
                        <span>Experience</span>
                        <span>{character.experience:,}</span>
                    </div>
                    <div class="stat-progress">
                        <div class="stat-fill exp-fill" style="width: {min(100, (character.experience % 1000) / 10):.1f}%;"></div>
                    </div>
                </div>
                
                <div style="margin-top: 20px;">
                    <p><strong>Gold:</strong> {character.gold:,}</p>
                    <p><strong>Total Power:</strong> {character.total_power:,}</p>
                    <p><strong>Attack:</strong> {character.get_effective_attack()}</p>
                </div>
            </div>
            
            <div class="main-area">
                <div class="room-info">
                    <div class="room-name">{room_info['name']}</div>
                    <p>{room_info['description']}</p>
                    <p><em>Zone: {room_info['zone_name']}</em></p>
                </div>
                
                <div class="movement">
                    <h4>Movement Options:</h4>
                    {movement_html if movement_html else '<p>No exits available.</p>'}
                </div>
            </div>
            
            <div class="players-area">
                <h3>PLAYERS IN AREA</h3>
                {characters_html}
            </div>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def room_detail(request: web_request.Request):
    """Detailed view of a specific room"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    room_id = int(request.match_info['room_id'])
    
    database = await get_db()
    async with database.get_connection() as conn:
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
    async with database.get_connection() as conn:
        # Get possible connections from current room
        connections = await database.queries.get_room_connections(conn, character.current_room_id)
        
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
        await database.queries.move_character(conn, target_room, character.id)
        await conn.commit()
    
    raise web.HTTPFound('/game')