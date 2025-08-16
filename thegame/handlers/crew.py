from aiohttp import web, web_request

from database import get_db
from handlers.auth import require_login
from handlers.character import get_current_character

async def crew_main(request: web_request.Request):
    """Main crew interface"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        # Check if character is in a crew
        crew_data = await database.queries.get_crew_by_character(conn, character_id=character.id)
        
        if crew_data:
            # Character is in a crew - show crew interface
            crew_members = await database.queries.get_crew_members(conn, crew_id=crew_data['id'])
            
            # Build member list
            members_html = ""
            for member in crew_members:
                role_color = "#ff6600" if member['role'] == 'leader' else "#00aa00" if member['role'] == 'officer' else "#ccc"
                members_html += f"""
                <div class="member-card">
                    <div class="member-info">
                        <strong>{member['name']}</strong><br>
                        Level {member['level']} {member['class_name']}<br>
                        <span style="color: {role_color};">{member['role'].title()}</span>
                    </div>
                    <div class="member-joined">
                        Joined: {member['joined_at'][:10]}
                    </div>
                </div>
                """
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Crew - {crew_data['name']}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }}
                    .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }}
                    .title {{ color: #ff6600; }}
                    .nav {{ display: flex; gap: 15px; }}
                    .nav a {{ color: #ff6600; text-decoration: none; padding: 10px 15px; background: #333; border-radius: 5px; }}
                    .crew-info {{ background: #333; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                    .crew-name {{ color: #ff6600; font-size: 2em; margin-bottom: 10px; }}
                    .members-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; }}
                    .member-card {{ background: #444; padding: 15px; border-radius: 8px; }}
                    .member-info {{ margin-bottom: 10px; }}
                    .member-joined {{ font-size: 0.9em; color: #ccc; }}
                    .actions {{ margin: 20px 0; display: flex; gap: 15px; }}
                    .btn {{ padding: 10px 20px; background: #ff6600; color: white; text-decoration: none; border-radius: 5px; }}
                    .btn:hover {{ background: #ff8833; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1 class="title">CREW INTERFACE</h1>
                    <div class="nav">
                        <a href="/crew/vault">VAULT</a>
                        <a href="/game">GAME</a>
                    </div>
                </div>
                
                <div class="crew-info">
                    <div class="crew-name">{crew_data['name']}</div>
                    <p>{crew_data['description'] or 'No description provided.'}</p>
                    <p><strong>Leader:</strong> {crew_data['leader_name']}</p>
                    <p><strong>Members:</strong> {len(crew_members)}/{crew_data['max_members']}</p>
                    <p><strong>Vault Capacity:</strong> {crew_data['vault_capacity']} items</p>
                </div>
                
                <h3>CREW MEMBERS</h3>
                <div class="members-grid">
                    {members_html}
                </div>
            </body>
            </html>
            """
            
        else:
            # Character is not in a crew - show join/create options
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Crew System</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }}
                    .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }}
                    .title {{ color: #ff6600; }}
                    .nav a {{ color: #ff6600; text-decoration: none; padding: 10px 15px; background: #333; border-radius: 5px; margin-left: 10px; }}
                    .crew-options {{ max-width: 600px; margin: 0 auto; text-align: center; }}
                    .option-card {{ background: #333; padding: 30px; border-radius: 10px; margin: 20px 0; }}
                    .option-card h3 {{ color: #ff6600; margin-top: 0; }}
                    .btn {{ display: inline-block; padding: 15px 30px; background: #ff6600; color: white; text-decoration: none; border-radius: 5px; margin: 10px; }}
                    .btn:hover {{ background: #ff8833; }}
                    .btn-alt {{ background: #00aa00; }}
                    .btn-alt:hover {{ background: #00cc00; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1 class="title">CREW SYSTEM</h1>
                    <div class="nav">
                        <a href="/game">BACK TO GAME</a>
                    </div>
                </div>
                
                <div class="crew-options">
                    <div class="option-card">
                        <h3>CREATE A CREW</h3>
                        <p>Start your own crew and lead other players in adventures!</p>
                        <a href="/crew/create" class="btn btn-alt">CREATE CREW</a>
                    </div>
                    
                    <div class="option-card">
                        <h3>JOIN A CREW</h3>
                        <p>Find and join an existing crew to participate in group activities.</p>
                        <a href="#" class="btn">BROWSE CREWS</a>
                    </div>
                </div>
            </body>
            </html>
            """
    
    return web.Response(text=html, content_type='text/html')

async def create_crew_page(request: web_request.Request):
    """Crew creation form"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    error = request.query.get('error', '')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Create Crew</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }}
            .container {{ max-width: 600px; margin: 0 auto; }}
            .title {{ text-align: center; color: #ff6600; margin-bottom: 30px; }}
            .form-group {{ margin: 20px 0; }}
            label {{ display: block; margin-bottom: 5px; }}
            input, textarea {{ width: 100%; padding: 10px; border: none; border-radius: 5px; background: #555; color: white; }}
            textarea {{ height: 100px; resize: vertical; }}
            .btn {{ width: 100%; padding: 15px; background: #ff6600; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 1.1em; }}
            .btn:hover {{ background: #ff8833; }}
            .error {{ color: #ff4444; text-align: center; margin: 10px 0; }}
            .back {{ text-align: center; margin: 20px 0; }}
            .back a {{ color: #ff6600; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2 class="title">CREATE CREW</h2>
            
            {f'<div class="error">{error}</div>' if error else ''}
            
            <form method="post">
                <div class="form-group">
                    <label>Crew Name:</label>
                    <input type="text" name="name" required minlength="3" maxlength="30">
                </div>
                
                <div class="form-group">
                    <label>Description:</label>
                    <textarea name="description" placeholder="Describe your crew's purpose and goals..." maxlength="500"></textarea>
                </div>
                
                <button type="submit" class="btn">CREATE CREW</button>
            </form>
            
            <div class="back">
                <a href="/crew">← Back to Crew System</a>
            </div>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def create_crew(request: web_request.Request):
    """Process crew creation"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    data = await request.post()
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if not name or len(name) < 3:
        raise web.HTTPFound('/crew/create?error=Crew name must be at least 3 characters')
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        try:
            # Check if character is already in a crew
            existing_crew = await database.queries.get_crew_by_character(conn, character_id=character.id)
            if existing_crew:
                raise web.HTTPFound('/crew/create?error=You are already in a crew')
            
            # Create crew
            await database.queries.create_crew(conn, name=name, leader_id=character.id, description=description or None)
            
            # Get the crew ID (SQLite doesn't return it directly)
            new_crew = await conn.execute("SELECT id FROM crews WHERE name = :name AND leader_id = :leader_id", {"name": name, "leader_id": character.id})
            crew_row = await new_crew.fetchone()
            crew_id = crew_row[0]
            
            # Add character as leader
            await database.queries.join_crew(conn, crew_id=crew_id, character_id=character.id, role='leader')
            
            await conn.commit()
            raise web.HTTPFound('/crew')
            
        except web.HTTPFound:
            # Re-raise HTTP redirects (like the success redirect)
            raise
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise web.HTTPFound('/crew/create?error=Crew name already exists')
            raise web.HTTPFound('/crew/create?error=Crew creation failed')

async def join_crew(request: web_request.Request):
    """Join an existing crew"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    crew_id = int(request.match_info['crew_id'])
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        # Check if character is already in a crew
        existing_crew = await database.queries.get_crew_by_character(conn, character_id=character.id)
        if existing_crew:
            raise web.HTTPBadRequest(text="Already in a crew")
        
        # Check crew exists and has space
        crew_check = await conn.execute("SELECT max_members FROM crews WHERE id = :crew_id", {"crew_id": crew_id})
        crew_data = await crew_check.fetchone()
        if not crew_data:
            raise web.HTTPNotFound()
        
        # Count current members
        member_count = await conn.execute("SELECT COUNT(*) FROM crew_members WHERE crew_id = :crew_id", {"crew_id": crew_id})
        count = await member_count.fetchone()
        
        if count[0] >= crew_data[0]:
            raise web.HTTPBadRequest(text="Crew is full")
        
        # Join crew
        await database.queries.join_crew(conn, crew_id=crew_id, character_id=character.id, role='member')
        await conn.commit()
    
    raise web.HTTPFound('/crew')

async def crew_vault(request: web_request.Request):
    """Crew vault interface"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        # Check if character is in a crew
        crew_data = await database.queries.get_crew_by_character(conn, character_id=character.id)
        if not crew_data:
            raise web.HTTPFound('/crew')
        
        # Get vault contents
        vault_items = await database.queries.get_crew_vault(conn, crew_data['id'])
    
    # Build vault items HTML
    vault_html = ""
    for item in vault_items:
        vault_html += f"""
        <div class="vault-item" style="border-color: {item['color']}">
            <div class="item-name" style="color: {item['color']}">{item['name']}</div>
            <div class="item-info">
                Quantity: {item['quantity']}<br>
                Deposited by: {item['deposited_by_name'] or 'Unknown'}<br>
                Date: {item['deposited_at'][:10]}
            </div>
            <form method="post" action="/crew/vault/award/{item['id']}" style="margin-top: 10px;">
                <button type="submit" class="btn-xs">AWARD TO ME</button>
            </form>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Crew Vault - {crew_data['name']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }}
            .title {{ color: #ff6600; }}
            .nav {{ display: flex; gap: 15px; }}
            .nav a {{ color: #ff6600; text-decoration: none; padding: 10px 15px; background: #333; border-radius: 5px; }}
            .vault-info {{ background: #333; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
            .vault-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; }}
            .vault-item {{ background: #444; border: 2px solid; border-radius: 8px; padding: 15px; }}
            .item-name {{ font-weight: bold; margin-bottom: 10px; }}
            .item-info {{ font-size: 0.9em; margin-bottom: 10px; }}
            .btn-xs {{ padding: 5px 10px; font-size: 0.8em; background: #ff6600; color: white; border: none; border-radius: 3px; cursor: pointer; }}
            .btn-xs:hover {{ background: #ff8833; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 class="title">CREW VAULT - {crew_data['name']}</h1>
            <div class="nav">
                <a href="/crew">CREW HOME</a>
                <a href="/game">GAME</a>
            </div>
        </div>
        
        <div class="vault-info">
            <h3>Vault Status</h3>
            <p><strong>Capacity:</strong> {len(vault_items)}/{crew_data['vault_capacity']} items</p>
            <p><strong>Two-way Vault:</strong> {'Enabled' if crew_data['has_two_way_vault'] else 'Disabled'}</p>
        </div>
        
        <h3>VAULT CONTENTS</h3>
        <div class="vault-grid">
            {vault_html if vault_html else '<p>Vault is empty.</p>'}
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')