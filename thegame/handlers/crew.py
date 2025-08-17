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
    """Crew vault interface - Outwar style"""
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
        vault_items = await database.queries.get_crew_vault(conn, crew_id=crew_data['id'])
        
        # Get crew members for award dropdown
        crew_members = await database.queries.get_crew_members(conn, crew_id=crew_data['id'])
    
    # Build vault grid (10x10 + 4 additional = 104 slots total)
    vault_grid_html = build_vault_grid(vault_items)
    
    # Build member dropdown options
    member_options = ""
    for member in crew_members:
        member_options += f'<option value="{member["id"]}">{member["name"]}</option>'
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Crew Vault - {crew_data['name']}</title>
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
            
            /* Main Container */
            .main-container {{ padding: 20px; }}
            
            /* Crew Header */
            .crew-header {{ background: #2d2d2d; border: 1px solid #555; border-radius: 8px; padding: 15px; margin-bottom: 20px; text-align: center; }}
            .crew-name {{ color: #4169e1; font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
            .crew-actions {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 10px; }}
            .dropdown-btn {{ padding: 5px 15px; background: linear-gradient(180deg, #8a2be2 0%, #6a1b9a 100%); color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 11px; }}
            .dropdown-btn:hover {{ background: linear-gradient(180deg, #9932cc 0%, #7b1fa2 100%); }}
            .vault-status {{ font-size: 12px; margin-top: 10px; }}
            
            /* Vault Grid */
            .vault-section {{ background: #2d2d2d; border: 1px solid #555; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
            .vault-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
            .vault-title {{ font-weight: bold; }}
            .sort-options {{ font-size: 11px; }}
            .sort-options select {{ background: #444; color: white; border: 1px solid #666; padding: 2px 5px; }}
            
            .vault-grid {{ display: grid; grid-template-columns: repeat(10, 48px); gap: 2px; justify-content: center; }}
            .vault-slot {{ width: 48px; height: 48px; background: #444; border: 2px solid #666; border-radius: 3px; display: flex; align-items: center; justify-content: center; cursor: pointer; }}
            .vault-slot.filled {{ border-color: #ffd700; }}
            .vault-slot.filled:hover {{ background: #555; }}
            .vault-slot.selected {{ border-color: #00ff00; background: #003300; }}
            .vault-icon {{ font-size: 24px; }}
            
            /* Management Panels */
            .management-panels {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .panel {{ background: #2d2d2d; border: 1px solid #555; border-radius: 8px; padding: 20px; }}
            .panel-title {{ font-weight: bold; margin-bottom: 15px; }}
            .panel-text {{ font-size: 11px; margin-bottom: 15px; line-height: 1.4; }}
            .member-dropdown {{ width: 100%; padding: 8px; background: #444; color: white; border: 1px solid #666; border-radius: 3px; margin-bottom: 10px; }}
            .action-btn {{ width: 100%; padding: 10px; background: linear-gradient(180deg, #4169e1 0%, #1e3a8a 100%); color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }}
            .action-btn:hover {{ background: linear-gradient(180deg, #5578ff 0%, #2563eb 100%); }}
            .action-btn:disabled {{ background: #666; cursor: not-allowed; }}
            .checkbox-row {{ margin: 10px 0; }}
            .checkbox-row input {{ margin-right: 8px; }}
            .log-link {{ color: #88ccff; text-decoration: underline; cursor: pointer; font-size: 11px; }}
            .note {{ background: #444; padding: 10px; border-radius: 3px; font-size: 10px; margin-top: 10px; }}
        </style>
    </head>
    <body>
        <!-- Top Navigation -->
        <div class="top-nav">
            <div class="nav-tab" onclick="window.location.href='/game'">Explore World</div>
            <div class="nav-tab" onclick="window.location.href='/challenges'">Challenges</div>
            <div class="nav-tab" onclick="window.location.href='/marketplace'">Marketplace</div>
            <div class="nav-tab" onclick="window.location.href='/rankings'">Rankings</div>
            <div class="nav-tab" onclick="window.location.href='/casino'">Casino</div>
            <div class="nav-tab" onclick="window.location.href='/wilderness'">Wilderness</div>
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
        
        <!-- Main Container -->
        <div class="main-container">
            <!-- Crew Header -->
            <div class="crew-header">
                <div class="crew-name">🔵 {crew_data['name']}</div>
                <div class="crew-actions">
                    <button class="dropdown-btn">Edit Crew ▼</button>
                    <button class="dropdown-btn">Actions ▼</button>
                    <button class="dropdown-btn">Storage ▼</button>
                    <button class="dropdown-btn">Accomplishments ▼</button>
                </div>
                <div class="vault-status">Currently Storing {len(vault_items)} / {crew_data['vault_capacity']} Items</div>
            </div>
            
            <!-- Vault Grid -->
            <div class="vault-section">
                <div class="vault-header">
                    <div class="vault-title">Crew Vault</div>
                    <div class="sort-options">
                        Order By: 
                        <select>
                            <option>Alphabetical</option>
                            <option>Newest</option>
                        </select>
                    </div>
                </div>
                
                <div class="vault-grid">
                    {vault_grid_html}
                </div>
            </div>
            
            <!-- Management Panels -->
            <div class="management-panels">
                <!-- Award Item Panel -->
                <div class="panel">
                    <div class="panel-title">Award Item</div>
                    <div class="panel-text">
                        To award an item to a crew member, click the item(s) you would like to award above, 
                        then select the crew member to award it to below
                    </div>
                    <div class="panel-text">Member Dropdown:</div>
                    <select class="member-dropdown" id="memberSelect">
                        <option value="">Select Member</option>
                        {member_options}
                    </select>
                    <button class="action-btn" onclick="awardItems()" disabled>Award Items</button>
                    <div class="log-link" style="margin-top: 10px;">View awarded item log</div>
                    <div class="note">
                        <strong>Note:</strong> To deposit an item into your crew's vault, your crew must have 
                        the Two Way Vault upgrade from the Treasury.
                    </div>
                </div>
                
                <!-- Delete Items Panel -->
                <div class="panel">
                    <div class="panel-title">Delete Items</div>
                    <div class="panel-text">
                        To delete an item from the vault, click the item(s) you would like to delete above, 
                        check the check box, then click the delete items button below.
                    </div>
                    <div class="checkbox-row">
                        <input type="checkbox" id="confirmDelete">
                        <label for="confirmDelete">I would like to delete the selected items.</label>
                    </div>
                    <button class="action-btn" onclick="deleteItems()" disabled>Delete Items</button>
                    <div class="log-link" style="margin-top: 10px;">View deleted item log</div>
                </div>
            </div>
        </div>
        
        <script>
        let selectedItems = new Set();
        
        function selectItem(slotIndex) {{
            const slot = document.querySelector(`[data-slot="${{slotIndex}}"]`);
            if (slot && slot.classList.contains('filled')) {{
                if (selectedItems.has(slotIndex)) {{
                    selectedItems.delete(slotIndex);
                    slot.classList.remove('selected');
                }} else {{
                    selectedItems.add(slotIndex);
                    slot.classList.add('selected');
                }}
                updateButtons();
            }}
        }}
        
        function updateButtons() {{
            const hasSelection = selectedItems.size > 0;
            const hasMember = document.getElementById('memberSelect').value !== '';
            const hasDeleteConfirm = document.getElementById('confirmDelete').checked;
            
            document.querySelector('button[onclick="awardItems()"]').disabled = !hasSelection || !hasMember;
            document.querySelector('button[onclick="deleteItems()"]').disabled = !hasSelection || !hasDeleteConfirm;
        }}
        
        document.getElementById('memberSelect').addEventListener('change', updateButtons);
        document.getElementById('confirmDelete').addEventListener('change', updateButtons);
        
        function awardItems() {{
            if (selectedItems.size > 0) {{
                const member = document.getElementById('memberSelect').value;
                alert(`Awarding ${{selectedItems.size}} item(s) to member ${{member}}`);
                // Implement actual award logic here
            }}
        }}
        
        function deleteItems() {{
            if (selectedItems.size > 0) {{
                alert(`Deleting ${{selectedItems.size}} item(s) from vault`);
                // Implement actual delete logic here
            }}
        }}
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

def build_vault_grid(vault_items):
    """Build the 10x10+4 vault grid"""
    # Create 104 slots (10x10 + 4 additional)
    total_slots = 104
    filled_slots = len(vault_items)
    
    grid_html = ""
    for i in range(total_slots):
        if i < filled_slots:
            # Filled slot with trophy icon (as per documentation)
            grid_html += f'''
            <div class="vault-slot filled" data-slot="{i}" onclick="selectItem({i})">
                <div class="vault-icon">🏆</div>
            </div>
            '''
        else:
            # Empty slot
            grid_html += f'''
            <div class="vault-slot" data-slot="{i}">
            </div>
            '''
    
    return grid_html