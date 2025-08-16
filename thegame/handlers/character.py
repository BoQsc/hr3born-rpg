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
    """Character detail page"""
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
    total_equipment_stats = {
        'attack': sum(eq.attack for eq in equipment.values()),
        'hit_points': sum(eq.hit_points for eq in equipment.values()),
        'chaos_damage': sum(eq.chaos_damage for eq in equipment.values()),
        'vile_damage': sum(eq.vile_damage for eq in equipment.values()),
        'fire_damage': sum(eq.fire_damage for eq in equipment.values()),
        'kinetic_damage': sum(eq.kinetic_damage for eq in equipment.values()),
        'arcane_damage': sum(eq.arcane_damage for eq in equipment.values()),
        'holy_damage': sum(eq.holy_damage for eq in equipment.values()),
        'shadow_damage': sum(eq.shadow_damage for eq in equipment.values()),
        'fire_resist': sum(eq.fire_resist for eq in equipment.values()),
        'kinetic_resist': sum(eq.kinetic_resist for eq in equipment.values()),
        'arcane_resist': sum(eq.arcane_resist for eq in equipment.values()),
        'holy_resist': sum(eq.holy_resist for eq in equipment.values()),
        'shadow_resist': sum(eq.shadow_resist for eq in equipment.values()),
    }
    
    # Build equipment grid HTML
    slots = ['head', 'chest', 'legs', 'boots', 'weapon', 'shield', 'accessory1', 'accessory2', 'ring1', 'ring2']
    equipment_grid = ""
    
    for slot in slots:
        eq = equipment.get(slot)
        if eq and eq.item_id:
            item_html = f"""
            <div class="equipment-slot filled" style="border-color: {eq.rarity_color}">
                <div class="item-name" style="color: {eq.rarity_color}">{eq.item_name}</div>
                <div class="item-stats">
                    {f'ATK: {eq.attack}' if eq.attack > 0 else ''}
                    {f'HP: {eq.hit_points}' if eq.hit_points > 0 else ''}
                </div>
                <form method="post" action="/unequip/{eq.slot_id}" style="margin-top: 5px;">
                    <button type="submit" class="btn-xs">UNEQUIP</button>
                </form>
            </div>
            """
        else:
            item_html = f"""
            <div class="equipment-slot empty">
                <div class="slot-name">{slot.upper()}</div>
                <div class="empty-text">Empty</div>
            </div>
            """
        equipment_grid += item_html
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{character.name} - Character Details</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }}
            .title {{ color: #ff6600; }}
            .nav {{ display: flex; gap: 15px; }}
            .nav a {{ color: #ff6600; text-decoration: none; padding: 10px 15px; background: #333; border-radius: 5px; }}
            .character-info {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }}
            .stats-panel {{ background: #333; padding: 20px; border-radius: 10px; }}
            .stat-row {{ display: flex; justify-content: space-between; margin: 5px 0; padding: 5px 0; border-bottom: 1px solid #555; }}
            .equipment-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }}
            .equipment-slot {{ background: #444; border: 2px solid #666; border-radius: 8px; padding: 10px; text-align: center; min-height: 80px; }}
            .equipment-slot.filled {{ border-color: #00aa00; }}
            .equipment-slot.empty {{ border-style: dashed; }}
            .item-name {{ font-weight: bold; margin-bottom: 5px; }}
            .item-stats {{ font-size: 0.8em; }}
            .btn-xs {{ padding: 3px 6px; font-size: 0.7em; background: #ff6600; color: white; border: none; border-radius: 3px; cursor: pointer; }}
            .btn {{ padding: 8px 15px; background: #ff6600; color: white; border: none; border-radius: 5px; text-decoration: none; cursor: pointer; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 class="title">{character.name} - Level {character.level} {character.class_name}</h1>
            <div class="nav">
                <a href="/characters">CHARACTERS</a>
                <a href="/inventory">INVENTORY</a>
                <a href="/game">GAME</a>
            </div>
        </div>
        
        <div class="character-info">
            <div class="stats-panel">
                <h3>CHARACTER STATS</h3>
                <div class="stat-row"><span>Level:</span><span>{character.level}</span></div>
                <div class="stat-row"><span>Experience:</span><span>{character.experience:,}</span></div>
                <div class="stat-row"><span>Gold:</span><span>{character.gold:,}</span></div>
                <div class="stat-row"><span>Total Power:</span><span>{character.total_power:,}</span></div>
                
                <h4>Combat Stats</h4>
                <div class="stat-row"><span>Attack:</span><span>{character.attack} + {total_equipment_stats['attack']} = {character.attack + total_equipment_stats['attack']}</span></div>
                <div class="stat-row"><span>Hit Points:</span><span>{character.hit_points_current}/{character.hit_points_max + total_equipment_stats['hit_points']}</span></div>
                <div class="stat-row"><span>Rage:</span><span>{character.rage_current}/{character.rage_max}</span></div>
                
                <h4>Damage Types</h4>
                <div class="stat-row"><span>Fire:</span><span>{character.fire_damage + total_equipment_stats['fire_damage']}</span></div>
                <div class="stat-row"><span>Kinetic:</span><span>{character.kinetic_damage + total_equipment_stats['kinetic_damage']}</span></div>
                <div class="stat-row"><span>Arcane:</span><span>{character.arcane_damage + total_equipment_stats['arcane_damage']}</span></div>
                <div class="stat-row"><span>Holy:</span><span>{character.holy_damage + total_equipment_stats['holy_damage']}</span></div>
                <div class="stat-row"><span>Shadow:</span><span>{character.shadow_damage + total_equipment_stats['shadow_damage']}</span></div>
                <div class="stat-row"><span>Chaos:</span><span>{character.chaos_damage + total_equipment_stats['chaos_damage']}</span></div>
                <div class="stat-row"><span>Vile:</span><span>{character.vile_damage + total_equipment_stats['vile_damage']}</span></div>
                
                <h4>Resistances</h4>
                <div class="stat-row"><span>Fire:</span><span>{character.fire_resist + total_equipment_stats['fire_resist']}</span></div>
                <div class="stat-row"><span>Kinetic:</span><span>{character.kinetic_resist + total_equipment_stats['kinetic_resist']}</span></div>
                <div class="stat-row"><span>Arcane:</span><span>{character.arcane_resist + total_equipment_stats['arcane_resist']}</span></div>
                <div class="stat-row"><span>Holy:</span><span>{character.holy_resist + total_equipment_stats['holy_resist']}</span></div>
                <div class="stat-row"><span>Shadow:</span><span>{character.shadow_resist + total_equipment_stats['shadow_resist']}</span></div>
            </div>
            
            <div class="stats-panel">
                <h3>EQUIPMENT</h3>
                <div class="equipment-grid">
                    {equipment_grid}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

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