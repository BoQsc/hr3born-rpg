from aiohttp import web, web_request
import aiohttp_session
from typing import Optional

from database import get_db
from handlers.auth import require_login
from models.character import Character, Equipment, InventoryItem

async def get_current_character(request: web_request.Request) -> Optional[Character]:
    """Get currently selected character from session"""
    import aiohttp_session
    session = await aiohttp_session.get_session(request)
    character_id = session.get('character_id')
    
    if not character_id:
        return None
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        result = await database.queries.get_character_by_id(conn, character_id=character_id)
        if result:
            return Character.from_db_row(result)
    return None

async def character_list(request: web_request.Request):
    """List all characters for account"""
    user = await require_login(request)
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        characters = await database.queries.get_characters_by_account(conn, account_id=user['id'])
        classes = await database.queries.get_all_classes(conn)
    
    current_char = await get_current_character(request)
    
    # Generate character cards
    char_cards = ""
    for char in characters:
        selected = "selected" if current_char and current_char.id == char['id'] else ""
        char_cards += f"""
        <div class="character-card {selected}">
            <h3>{char['name']}</h3>
            <p><strong>Class:</strong> {char['class_name']}</p>
            <p><strong>Level:</strong> {char['level']}</p>
            <p><strong>Power:</strong> {char['total_power']}</p>
            <p><strong>HP:</strong> {char['hit_points_current']}/{char['hit_points_max']}</p>
            <div class="char-actions">
                <form method="post" action="/character/{char['id']}/select" style="display:inline;">
                    <button type="submit" class="btn btn-sm">SELECT</button>
                </form>
                <a href="/character/{char['id']}" class="btn btn-sm">VIEW</a>
            </div>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Characters - Outwar Clone</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }}
            .title {{ color: #ff6600; }}
            .nav {{ display: flex; gap: 15px; }}
            .nav a {{ color: #ff6600; text-decoration: none; padding: 10px 15px; background: #333; border-radius: 5px; }}
            .nav a:hover {{ background: #555; }}
            .characters {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
            .character-card {{ background: #333; padding: 20px; border-radius: 10px; border: 2px solid transparent; }}
            .character-card.selected {{ border-color: #ff6600; }}
            .character-card h3 {{ margin-top: 0; color: #ff6600; }}
            .char-actions {{ margin-top: 15px; display: flex; gap: 10px; }}
            .btn {{ padding: 8px 15px; background: #ff6600; color: white; border: none; border-radius: 5px; text-decoration: none; cursor: pointer; }}
            .btn:hover {{ background: #ff8833; }}
            .btn-sm {{ padding: 5px 10px; font-size: 0.9em; }}
            .create-char {{ text-align: center; margin: 20px 0; }}
            .create-char a {{ display: inline-block; padding: 15px 30px; background: #00aa00; color: white; text-decoration: none; border-radius: 5px; font-size: 1.1em; }}
            .create-char a:hover {{ background: #00cc00; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 class="title">CHARACTERS</h1>
            <div class="nav">
                <a href="/game">GAME</a>
                <form method="post" action="/logout" style="display:inline;">
                    <button type="submit" class="btn">LOGOUT</button>
                </form>
            </div>
        </div>
        
        <div class="create-char">
            <a href="/character/create">CREATE NEW CHARACTER</a>
        </div>
        
        <div class="characters">
            {char_cards}
        </div>
        
        {f'<p style="text-align: center; color: #ccc;">Current Character: <strong>{current_char.name}</strong></p>' if current_char else '<p style="text-align: center; color: #ccc;">No character selected</p>'}
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def create_character_page(request: web_request.Request):
    """Character creation form"""
    await require_login(request)
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        classes = await database.queries.get_all_classes(conn)
    
    class_options = ""
    for char_class in classes:
        class_options += f"""
        <div class="class-option">
            <label>
                <input type="radio" name="class_id" value="{char_class['id']}" required>
                <div class="class-card">
                    <h3>{char_class['name']}</h3>
                    <p><strong>Attack Bonus:</strong> {char_class['attack_bonus']*100:.1f}%</p>
                    <p><strong>Defense Bonus:</strong> {char_class['defense_bonus']*100:.1f}%</p>
                    <p><strong>Rage Per Turn:</strong> {char_class['rage_per_turn_bonus']*100:.1f}%</p>
                    <p><strong>Max Rage:</strong> {char_class['max_rage_bonus']*100:.1f}%</p>
                </div>
            </label>
        </div>
        """
    
    error = request.query.get('error', '')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Create Character - Outwar Clone</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .title {{ text-align: center; color: #ff6600; margin-bottom: 30px; }}
            .form-group {{ margin: 20px 0; }}
            label {{ display: block; margin-bottom: 5px; }}
            input[type="text"] {{ width: 100%; padding: 10px; border: none; border-radius: 5px; background: #555; color: white; }}
            .class-selection {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }}
            .class-option input[type="radio"] {{ display: none; }}
            .class-card {{ padding: 15px; background: #333; border-radius: 10px; border: 2px solid transparent; cursor: pointer; }}
            .class-option input[type="radio"]:checked + .class-card {{ border-color: #ff6600; }}
            .class-card h3 {{ margin-top: 0; color: #ff6600; }}
            .btn {{ width: 100%; padding: 15px; background: #ff6600; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 1.1em; }}
            .btn:hover {{ background: #ff8833; }}
            .error {{ color: #ff4444; text-align: center; margin: 10px 0; }}
            .back {{ text-align: center; margin: 20px 0; }}
            .back a {{ color: #ff6600; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2 class="title">CREATE CHARACTER</h2>
            
            {f'<div class="error">{error}</div>' if error else ''}
            
            <form method="post">
                <div class="form-group">
                    <label>Character Name:</label>
                    <input type="text" name="name" required minlength="3" maxlength="20" pattern="[A-Za-z0-9_]+">
                    <small style="color: #ccc;">Letters, numbers, and underscores only</small>
                </div>
                
                <div class="form-group">
                    <label>Choose Class:</label>
                    <div class="class-selection">
                        {class_options}
                    </div>
                </div>
                
                <button type="submit" class="btn">CREATE CHARACTER</button>
            </form>
            
            <div class="back">
                <a href="/characters">← Back to Characters</a>
            </div>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def create_character(request: web_request.Request):
    """Process character creation"""
    user = await require_login(request)
    data = await request.post()
    name = data.get('name', '').strip()
    class_id = data.get('class_id')
    
    if not name or len(name) < 3:
        raise web.HTTPFound('/character/create?error=Character name must be at least 3 characters')
    
    if not class_id:
        raise web.HTTPFound('/character/create?error=Please select a character class')
    
    try:
        class_id = int(class_id)
    except:
        raise web.HTTPFound('/character/create?error=Invalid character class')
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        try:
            await database.queries.create_character(conn, account_id=user['id'], name=name, class_id=class_id)
            
            # Get the new character ID
            new_char = await conn.execute("SELECT id FROM characters WHERE name = :name AND account_id = :account_id", 
                                        {"name": name, "account_id": user['id']})
            char_row = await new_char.fetchone()
            char_id = char_row[0]
            
            # Give starter equipment
            from services.character_service import give_starter_equipment
            await give_starter_equipment(char_id)
            print(f"Character created with ID: {char_id}")
            
            await conn.commit()
            raise web.HTTPFound('/characters')
        except web.HTTPFound:
            # Re-raise HTTP redirects
            raise
        except Exception as e:
            print(f"Character creation error: {e}")
            print(f"Error type: {type(e)}")
            if "UNIQUE constraint failed" in str(e):
                raise web.HTTPFound('/character/create?error=Character name already exists')
            raise web.HTTPFound(f'/character/create?error=Character creation failed: {str(e)[:50]}')

async def select_character(request: web_request.Request):
    """Select active character"""
    await require_login(request)
    character_id = int(request.match_info['character_id'])
    
    import aiohttp_session
    session = await aiohttp_session.get_session(request)
    session['character_id'] = character_id
    
    raise web.HTTPFound('/characters')

async def character_detail(request: web_request.Request):
    """Character profile page - Outwar style"""
    await require_login(request)
    character_id = int(request.match_info['character_id'])
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        char_data = await database.queries.get_character_by_id(conn, character_id)
        if not char_data:
            raise web.HTTPNotFound()
        
        character = Character.from_db_row(char_data)
        
        # Get equipment
        equipment_data = await database.queries.get_character_equipment(conn, character_id)
        equipment = {}
        for eq in equipment_data:
            equipment[eq['slot_name']] = Equipment(
                slot_id=eq['slot_id'],
                slot_name=eq['slot_name'],
                item_id=eq['item_id'],
                item_name=eq['name'],
                rarity_name=eq['rarity_name'],
                rarity_color=eq['color'],
                attack=eq['attack'],
                hit_points=eq['hit_points'],
                chaos_damage=eq['chaos_damage'],
                vile_damage=eq['vile_damage'],
                fire_damage=eq['fire_damage'],
                kinetic_damage=eq['kinetic_damage'],
                arcane_damage=eq['arcane_damage'],
                holy_damage=eq['holy_damage'],
                shadow_damage=eq['shadow_damage'],
                fire_resist=eq['fire_resist'],
                kinetic_resist=eq['kinetic_resist'],
                arcane_resist=eq['arcane_resist'],
                holy_resist=eq['holy_resist'],
                shadow_resist=eq['shadow_resist'],
                critical_hit_percent=eq['critical_hit_percent'],
                rampage_percent=eq['rampage_percent'],
                rage_per_hour=eq['rage_per_hour'],
                experience_per_hour=eq['experience_per_hour'],
                gold_per_turn=eq['gold_per_turn'],
                max_rage=eq['max_rage']
            )
    
    # Calculate total stats from equipment
    total_attack = character.attack + sum(eq.attack for eq in equipment.values())
    total_hp = character.hit_points_max + sum(eq.hit_points for eq in equipment.values())
    total_chaos = character.chaos_damage + sum(eq.chaos_damage for eq in equipment.values())
    total_elemental = sum([
        character.fire_damage + sum(eq.fire_damage for eq in equipment.values()),
        character.kinetic_damage + sum(eq.kinetic_damage for eq in equipment.values()),
        character.arcane_damage + sum(eq.arcane_damage for eq in equipment.values()),
        character.holy_damage + sum(eq.holy_damage for eq in equipment.values()),
        character.shadow_damage + sum(eq.shadow_damage for eq in equipment.values())
    ])
    total_resist = sum([
        character.fire_resist + sum(eq.fire_resist for eq in equipment.values()),
        character.kinetic_resist + sum(eq.kinetic_resist for eq in equipment.values()),
        character.arcane_resist + sum(eq.arcane_resist for eq in equipment.values()),
        character.holy_resist + sum(eq.holy_resist for eq in equipment.values()),
        character.shadow_resist + sum(eq.shadow_resist for eq in equipment.values())
    ])
    
    # Build Outwar-style equipment grid (3x4 + boots + quick slots)
    equipment_grid_html = generate_equipment_grid(equipment)
    
    # Calculate experience growth (mock data)
    yesterday_growth = min(character.experience // 100, 99999)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{character.name} - Character Profile</title>
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
            
            /* Main Content */
            .main-container {{ padding: 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 30px; height: calc(100vh - 70px); }}
            
            /* Profile Section */
            .profile-section {{ background: #2d2d2d; border: 1px solid #555; border-radius: 8px; padding: 20px; }}
            .profile-header {{ display: flex; gap: 20px; margin-bottom: 20px; }}
            .profile-left {{ flex: 1; }}
            .profile-name {{ font-size: 18px; font-weight: bold; color: #ffd700; margin-bottom: 5px; }}
            .profile-hits {{ font-size: 11px; color: #ccc; margin-bottom: 15px; }}
            .character-portrait {{ width: 200px; height: 250px; background: linear-gradient(45deg, #8b0000, #000); border: 2px solid #888; display: flex; align-items: center; justify-content: center; color: #ccc; border-radius: 8px; }}
            
            .action-buttons {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
            .action-btn {{ padding: 8px 12px; background: linear-gradient(180deg, #444 0%, #333 100%); color: white; border: 1px solid #666; border-radius: 5px; cursor: pointer; font-size: 10px; text-align: center; }}
            .action-btn:hover {{ background: linear-gradient(180deg, #555 0%, #444 100%); }}
            .action-btn.attack {{ background: linear-gradient(180deg, #ff4444 0%, #cc3333 100%); }}
            .action-btn.trade {{ background: linear-gradient(180deg, #4444ff 0%, #3333cc 100%); }}
            
            /* Skills Section */
            .skills-section {{ background: #333; border: 1px solid #555; border-radius: 5px; padding: 15px; margin: 20px 0; }}
            .skills-header {{ font-weight: bold; margin-bottom: 10px; }}
            
            /* Player Info Panel */
            .player-info {{ background: #333; border: 1px solid #555; border-radius: 5px; padding: 15px; }}
            .info-header {{ font-weight: bold; margin-bottom: 15px; text-align: center; }}
            .info-row {{ display: flex; justify-content: space-between; margin: 5px 0; font-size: 11px; }}
            .info-label {{ color: #ccc; }}
            .info-value {{ color: #fff; font-weight: bold; }}
            .progress-bar {{ width: 100%; height: 15px; background: #444; border-radius: 3px; margin-top: 10px; overflow: hidden; }}
            .progress-fill {{ height: 100%; background: linear-gradient(90deg, #ffd700 0%, #ff8c00 100%); }}
            
            /* Equipment Section */
            .equipment-section {{ background: #2d2d2d; border: 1px solid #555; border-radius: 8px; padding: 20px; }}
            .equipment-header {{ font-weight: bold; margin-bottom: 15px; text-align: center; }}
            .equipment-grid {{ display: grid; grid-template-columns: repeat(3, 64px); gap: 2px; justify-content: center; margin-bottom: 20px; }}
            .equipment-slot {{ width: 64px; height: 64px; background: #444; border: 2px solid #666; border-radius: 5px; display: flex; align-items: center; justify-content: center; cursor: pointer; position: relative; }}
            .equipment-slot.filled {{ border-color: #ffd700; }}
            .equipment-slot.empty {{ border-style: dashed; }}
            .slot-icon {{ font-size: 24px; }}
            .item-tooltip {{ position: absolute; top: -5px; right: -5px; background: #000; color: #ffd700; padding: 2px 4px; border-radius: 3px; font-size: 8px; }}
            
            .quick-slots {{ display: flex; justify-content: center; gap: 2px; margin-top: 15px; }}
            .quick-slot {{ width: 48px; height: 48px; background: #444; border: 2px solid #666; border-radius: 3px; }}
            .quick-slot.filled {{ border-color: #00aa00; }}
            
            /* Skill Crests */
            .skill-crests {{ margin: 20px 0; }}
            .crest-grid {{ display: flex; justify-content: center; gap: 5px; }}
            .crest-slot {{ width: 40px; height: 40px; background: #444; border: 2px solid #666; border-radius: 3px; }}
            
            /* Masteries */
            .masteries {{ margin-top: 20px; }}
            .mastery-item {{ margin: 10px 0; }}
            .mastery-label {{ font-size: 11px; margin-bottom: 3px; }}
            .mastery-bar {{ width: 100%; height: 12px; background: #444; border-radius: 6px; overflow: hidden; }}
            .mastery-fill {{ height: 100%; background: linear-gradient(90deg, #4169e1 0%, #1e90ff 100%); }}
            
            /* Equipment Tooltips */
            .item-tooltip-container {{ position: absolute; background: rgba(0,0,0,0.95); border: 2px solid #ffd700; border-radius: 8px; padding: 10px; z-index: 1000; min-width: 200px; max-width: 300px; font-size: 11px; pointer-events: none; }}
            .tooltip-title {{ color: #ffd700; font-weight: bold; margin-bottom: 5px; border-bottom: 1px solid #555; padding-bottom: 3px; }}
            .tooltip-slot {{ color: #888; font-style: italic; margin-bottom: 8px; }}
            .tooltip-stats {{ margin: 5px 0; }}
            .stat-line {{ margin: 2px 0; }}
            .stat-positive {{ color: #32cd32; }}
            .stat-percentage {{ color: #ff8c00; }}
            .stat-special {{ color: #4169e1; }}
            .tooltip-footer {{ color: #ffd700; margin-top: 8px; border-top: 1px solid #555; padding-top: 5px; font-size: 10px; }}
        </style>
    </head>
    <body>
        <!-- Top Navigation -->
        <div class="top-nav">
            <div class="nav-tab">Explore World</div>
            <div class="nav-tab active">Character</div>
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
        
        <!-- Main Content -->
        <div class="main-container">
            <!-- Left Column -->
            <div>
                <!-- Profile Section -->
                <div class="profile-section">
                    <div class="profile-header">
                        <div class="profile-left">
                            <div class="profile-name">{character.name}</div>
                            <div class="profile-hits">{character.id} Profile Hits</div>
                            <div class="character-portrait">
                                Character Portrait<br>
                                <small>Level {character.level} {character.class_name}</small>
                            </div>
                        </div>
                        <div class="action-buttons">
                            <button class="action-btn attack">⚔️ ATTACK</button>
                            <button class="action-btn trade">💎 TRADE</button>
                            <button class="action-btn">✉️ MESSAGE</button>
                            <button class="action-btn">👥 CREW INV</button>
                            <button class="action-btn">➕ ADD ALLY</button>
                            <button class="action-btn">⚔️ ADD ENEMY</button>
                            <button class="action-btn">❌ BLOCK</button>
                            <button class="action-btn">💰 TREASURY</button>
                        </div>
                    </div>
                </div>
                
                <!-- Skills Section -->
                <div class="skills-section">
                    <div class="skills-header">SKILLS:</div>
                    <div style="color: #888; text-align: center; font-style: italic;">No skills learned yet</div>
                </div>
                
                <!-- Player Info Panel -->
                <div class="player-info">
                    <div class="info-header">PLAYER INFO</div>
                    <div class="info-row">
                        <span class="info-label">CHARACTER CLASS</span>
                        <span class="info-value">Level {character.level} {character.class_name}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">TOTAL EXPERIENCE</span>
                        <span class="info-value">{character.experience:,}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">GROWTH YESTERDAY</span>
                        <span class="info-value">{yesterday_growth:,}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">TOTAL POWER</span>
                        <span class="info-value">{character.total_power:,}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">ATTACK</span>
                        <span class="info-value">{total_attack:,}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">HIT POINTS</span>
                        <span class="info-value">{total_hp:,}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">CHAOS DAMAGE</span>
                        <span class="info-value">{total_chaos}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">ELEMENTAL ATTACK</span>
                        <span class="info-value">{total_elemental}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">ELEMENTAL RESIST</span>
                        <span class="info-value">{total_resist}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">WILDERNESS LEVEL</span>
                        <span class="info-value">{character.wilderness_level}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">GOD SLAYER LEVEL</span>
                        <span class="info-value">{character.god_slayer_level}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">PARENT</span>
                        <span class="info-value">None</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">FACTION</span>
                        <span class="info-value">{character.faction_name or 'None'} ( )</span>
                    </div>
                    
                    <div style="margin-top: 15px; text-align: center; font-size: 10px;">
                        Leader of Test Crew
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {min(100, character.level * 1.5)}%;"></div>
                    </div>
                </div>
                
                <!-- Personal Allies Section -->
                <div class="player-info" style="margin-top: 20px;">
                    <div class="info-header">PERSONAL ALLIES (0)</div>
                    <div class="character-portrait" style="width: 100%; height: 150px; margin-top: 10px;">
                        No Allies Yet
                    </div>
                </div>
            </div>
            
            <!-- Right Column - Equipment -->
            <div class="equipment-section">
                <div class="equipment-header">EQUIPMENT</div>
                
                {equipment_grid_html}
                
                <!-- Skill Crests -->
                <div class="skill-crests">
                    <div class="equipment-header" style="font-size: 12px;">SKILL CRESTS</div>
                    <div class="crest-grid">
                        <div class="crest-slot"></div>
                        <div class="crest-slot"></div>
                        <div class="crest-slot"></div>
                        <div class="crest-slot"></div>
                    </div>
                </div>
                
                <!-- Masteries -->
                <div class="masteries">
                    <div class="equipment-header" style="font-size: 12px;">MASTERIES</div>
                    <div class="mastery-item">
                        <div class="mastery-label">OVERALL MASTERY</div>
                        <div class="mastery-bar">
                            <div class="mastery-fill" style="width: {min(100, character.level * 1.2)}%;"></div>
                        </div>
                    </div>
                    <div class="mastery-item">
                        <div class="mastery-label">ATTACK MASTERY</div>
                        <div class="mastery-bar">
                            <div class="mastery-fill" style="width: {min(100, character.level * 0.8)}%;"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Tooltip Container -->
        <div id="tooltip" class="item-tooltip-container" style="display: none;"></div>
        
        <script>
        function showTooltip(event, itemId) {{
            const tooltipData = document.getElementById('tooltip-' + itemId);
            const tooltip = document.getElementById('tooltip');
            
            if (tooltipData && tooltip) {{
                tooltip.innerHTML = tooltipData.innerHTML;
                tooltip.style.display = 'block';
                tooltip.style.left = (event.pageX + 10) + 'px';
                tooltip.style.top = (event.pageY - 10) + 'px';
            }}
        }}
        
        function hideTooltip() {{
            const tooltip = document.getElementById('tooltip');
            if (tooltip) {{
                tooltip.style.display = 'none';
            }}
        }}
        
        // Move tooltip with mouse
        document.addEventListener('mousemove', function(event) {{
            const tooltip = document.getElementById('tooltip');
            if (tooltip && tooltip.style.display === 'block') {{
                tooltip.style.left = (event.pageX + 10) + 'px';
                tooltip.style.top = (event.pageY - 10) + 'px';
            }}
        }});
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

def generate_equipment_grid(equipment):
    """Generate Outwar-style equipment grid"""
    # Define slot layout according to Outwar documentation
    slot_layout = [
        ['accessory1', 'head', 'weapon'],      # Top row: 💎🔮🏹
        ['shield', 'chest', 'accessory2'],     # Middle row: 🔫👕🛡️  
        ['ring1', 'legs', 'ring2'],            # Bottom row: 💍👖💍
        ['', 'boots', '']                      # Boots row: centered
    ]
    
    slot_icons = {
        'head': '🔮',
        'chest': '👕', 
        'legs': '👖',
        'boots': '👢',
        'weapon': '🏹',
        'shield': '🛡️',
        'accessory1': '💎',
        'accessory2': '🛡️',
        'ring1': '💍',
        'ring2': '💍'
    }
    
    grid_html = '<div class="equipment-grid">'
    
    for row in slot_layout:
        for slot in row:
            if slot == '':
                # Empty grid space
                grid_html += '<div style="width: 64px; height: 64px;"></div>'
            else:
                eq = equipment.get(slot)
                if eq and eq.item_id:
                    # Build tooltip content
                    tooltip_content = build_item_tooltip(eq)
                    # Equipped item
                    grid_html += f'''
                    <div class="equipment-slot filled" onmouseover="showTooltip(event, '{eq.item_id}')" onmouseout="hideTooltip()">
                        <div class="slot-icon">{slot_icons.get(slot, '⚪')}</div>
                        <div class="item-tooltip">+{eq.attack + eq.hit_points}</div>
                        <div class="tooltip-data" id="tooltip-{eq.item_id}" style="display:none;">{tooltip_content}</div>
                    </div>
                    '''
                else:
                    # Empty slot
                    grid_html += f'''
                    <div class="equipment-slot empty">
                        <div class="slot-icon">{slot_icons.get(slot, '⚪')}</div>
                    </div>
                    '''
    
    grid_html += '</div>'
    
    # Add quick access slots
    grid_html += '''
    <div class="quick-slots">
        <div class="quick-slot"></div>
        <div class="quick-slot"></div>
        <div class="quick-slot filled"></div>
        <div class="quick-slot"></div>
        <div class="quick-slot"></div>
    </div>
    '''
    
    return grid_html

def build_item_tooltip(item):
    """Build Outwar-style item tooltip HTML"""
    # Determine if it's weapon or armor based on slot
    is_weapon = item.slot_name in ['weapon']
    is_armor = item.slot_name in ['head', 'chest', 'legs', 'boots', 'shield']
    
    tooltip_html = f'<div class="tooltip-title">{item.item_name}</div>'
    tooltip_html += f'<div class="tooltip-slot">[Slot - {item.slot_name.title()}]</div>'
    tooltip_html += '<div class="tooltip-stats">'
    
    # Add stats based on item type
    if item.attack > 0:
        tooltip_html += f'<div class="stat-line stat-positive">+{item.attack} ATK</div>'
    
    if item.hit_points > 0:
        tooltip_html += f'<div class="stat-line stat-positive">+{item.hit_points} HP</div>'
    
    # Add elemental damages
    if item.fire_damage > 0:
        tooltip_html += f'<div class="stat-line stat-positive">+{item.fire_damage} Fire</div>'
    if item.kinetic_damage > 0:
        tooltip_html += f'<div class="stat-line stat-positive">+{item.kinetic_damage} Kinetic</div>'
    if item.arcane_damage > 0:
        tooltip_html += f'<div class="stat-line stat-positive">+{item.arcane_damage} Arcane</div>'
    if item.holy_damage > 0:
        tooltip_html += f'<div class="stat-line stat-positive">+{item.holy_damage} Holy</div>'
    if item.shadow_damage > 0:
        tooltip_html += f'<div class="stat-line stat-positive">+{item.shadow_damage} Shadow</div>'
    if item.chaos_damage > 0:
        tooltip_html += f'<div class="stat-line stat-positive">+{item.chaos_damage} Chaos</div>'
    if item.vile_damage > 0:
        tooltip_html += f'<div class="stat-line stat-positive">+{item.vile_damage} Vile</div>'
    
    # Add resistances for armor
    if is_armor:
        if item.fire_resist > 0:
            tooltip_html += f'<div class="stat-line stat-positive">+{item.fire_resist} Fire Resist</div>'
        if item.kinetic_resist > 0:
            tooltip_html += f'<div class="stat-line stat-positive">+{item.kinetic_resist} Kinetic Resist</div>'
        if item.arcane_resist > 0:
            tooltip_html += f'<div class="stat-line stat-positive">+{item.arcane_resist} Arcane Resist</div>'
        if item.holy_resist > 0:
            tooltip_html += f'<div class="stat-line stat-positive">+{item.holy_resist} Holy Resist</div>'
        if item.shadow_resist > 0:
            tooltip_html += f'<div class="stat-line stat-positive">+{item.shadow_resist} Shadow Resist</div>'
    
    # Add special stats
    if item.rage_per_hour > 0:
        tooltip_html += f'<div class="stat-line stat-special">+{item.rage_per_hour} rage per hr</div>'
    if item.experience_per_hour > 0:
        tooltip_html += f'<div class="stat-line stat-special">+{item.experience_per_hour} exp per hr</div>'
    if item.gold_per_turn > 0:
        tooltip_html += f'<div class="stat-line stat-special">+{item.gold_per_turn} gold per turn</div>'
    if item.max_rage > 0:
        tooltip_html += f'<div class="stat-line stat-special">+{item.max_rage} max rage</div>'
    
    # Add percentage bonuses
    if item.critical_hit_percent > 0:
        tooltip_html += f'<div class="stat-line stat-percentage">+{item.critical_hit_percent}% critical hit</div>'
    if item.rampage_percent > 0:
        tooltip_html += f'<div class="stat-line stat-percentage">+{item.rampage_percent}% rampage</div>'
    
    tooltip_html += '</div>'
    
    # Add footer (transfer limit info)
    tooltip_html += '<div class="tooltip-footer">Can change hands 1 more time today</div>'
    
    return tooltip_html

async def inventory(request: web_request.Request):
    """Character inventory page"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        inventory_data = await database.queries.get_character_inventory(conn, character_id=character.id)
    
    # Group items by slot type
    items_by_slot = {}
    for item in inventory_data:
        slot = item['slot_name']
        if slot not in items_by_slot:
            items_by_slot[slot] = []
        items_by_slot[slot].append(InventoryItem(
            id=item['id'],
            item_id=item['item_id'],
            name=item['name'],
            slot_name=item['slot_name'],
            rarity_name=item['rarity_name'],
            rarity_color=item['color'],
            level_requirement=item['level_requirement'],
            quantity=item['quantity'],
            transfers_remaining=item['transfers_remaining'],
            attack=item['attack'],
            hit_points=item['hit_points']
        ))
    
    # Build inventory HTML
    inventory_html = ""
    for slot, items in items_by_slot.items():
        inventory_html += f"<h3>{slot.upper()}</h3><div class='item-grid'>"
        for item in items:
            can_equip = character.level >= item.level_requirement
            equip_button = f"""
            <form method="post" action="/equip/{item.item_id}" style="margin-top: 5px;">
                <button type="submit" class="btn-xs" {'disabled' if not can_equip else ''}>EQUIP</button>
            </form>
            """ if can_equip else f"<div class='req-level'>Req: Lv{item.level_requirement}</div>"
            
            inventory_html += f"""
            <div class="inventory-item" style="border-color: {item.rarity_color}">
                <div class="item-name" style="color: {item.rarity_color}">{item.name}</div>
                <div class="item-stats">
                    {f'ATK: {item.attack}' if item.attack > 0 else ''}
                    {f'HP: {item.hit_points}' if item.hit_points > 0 else ''}
                </div>
                {equip_button}
            </div>
            """
        inventory_html += "</div>"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Inventory - {character.name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }}
            .title {{ color: #ff6600; }}
            .nav {{ display: flex; gap: 15px; }}
            .nav a {{ color: #ff6600; text-decoration: none; padding: 10px 15px; background: #333; border-radius: 5px; }}
            .item-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }}
            .inventory-item {{ background: #333; border: 2px solid; border-radius: 8px; padding: 15px; }}
            .item-name {{ font-weight: bold; margin-bottom: 5px; }}
            .item-stats {{ font-size: 0.9em; margin-bottom: 10px; }}
            .btn-xs {{ padding: 5px 10px; font-size: 0.8em; background: #ff6600; color: white; border: none; border-radius: 3px; cursor: pointer; }}
            .btn-xs:disabled {{ background: #666; cursor: not-allowed; }}
            .req-level {{ font-size: 0.8em; color: #ff4444; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 class="title">INVENTORY - {character.name}</h1>
            <div class="nav">
                <a href="/character/{character.id}">CHARACTER</a>
                <a href="/game">GAME</a>
            </div>
        </div>
        
        <div class="inventory">
            {inventory_html if inventory_html else '<p>No items in inventory.</p>'}
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def equip_item(request: web_request.Request):
    """Equip an item from inventory"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    item_id = int(request.match_info['item_id'])
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        # Get item details
        inventory_items = await database.queries.get_character_inventory(conn, character_id=character.id)
        item = None
        for inv_item in inventory_items:
            if inv_item['item_id'] == item_id:
                item = inv_item
                break
        
        if not item:
            raise web.HTTPNotFound()
        
        # Check level requirement
        if character.level < item['level_requirement']:
            raise web.HTTPBadRequest()
        
        # Get item's slot
        # We need to get the slot_id from the items table
        item_details = await conn.execute("SELECT slot_id FROM items WHERE id = :item_id", {"item_id": item_id})
        item_detail = await item_details.fetchone()
        if not item_detail:
            raise web.HTTPNotFound()
        
        slot_id = item_detail[0]
        
        # Equip the item
        await database.queries.equip_item(conn, character_id=character.id, slot_id=slot_id, item_id=item_id)
        
        # Remove from inventory
        await database.queries.remove_from_inventory(conn, character_id=character.id, item_id=item_id)
        
        await conn.commit()
    
    raise web.HTTPFound('/inventory')

async def unequip_item(request: web_request.Request):
    """Unequip an item to inventory"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    slot_id = int(request.match_info['slot_id'])
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        # Get currently equipped item
        equipment = await database.queries.get_character_equipment(conn, character.id)
        equipped_item = None
        for eq in equipment:
            if eq['slot_id'] == slot_id:
                equipped_item = eq
                break
        
        if not equipped_item:
            raise web.HTTPNotFound()
        
        # Add to inventory
        await database.queries.add_to_inventory(conn, character.id, equipped_item['item_id'], 1, 10)
        
        # Remove from equipment
        await database.queries.unequip_item(conn, character.id, slot_id)
        
        await conn.commit()
    
    raise web.HTTPFound(f'/character/{character.id}')