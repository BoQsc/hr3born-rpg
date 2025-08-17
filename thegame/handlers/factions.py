from aiohttp import web, web_request
from datetime import datetime

from database import get_db
from handlers.auth import require_login
from handlers.character import get_current_character

async def factions_main(request: web_request.Request):
    """Faction system - available at level 91+"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    # Check if character is high enough level for factions
    if character.level < 91:
        return await faction_locked_page(character)
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        # Get all factions
        factions = await database.queries.get_all_factions(conn)
        
        # Get character's current faction info if any
        current_faction = None
        if character.faction_id:
            faction_result = await conn.execute('SELECT * FROM factions WHERE id = :faction_id', 
                                              {'faction_id': character.faction_id})
            current_faction = await faction_result.fetchone()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Faction Wars - Outwar</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: Arial, sans-serif; background: #1a1a1a; color: #ffffff; }}
            
            /* Faction Background */
            .faction-bg {{ 
                background: linear-gradient(135deg, #2d0a0a 0%, #4a0a0a 25%, #0a2d0a 50%, #0a0a2d 75%, #2d0a0a 100%);
                min-height: 100vh;
                background-image: 
                    radial-gradient(circle at 20% 20%, rgba(255, 0, 0, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 80% 20%, rgba(0, 255, 0, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 50% 80%, rgba(0, 0, 255, 0.1) 0%, transparent 50%);
            }}
            
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
            .main-container {{ padding: 20px; max-width: 1400px; margin: 0 auto; }}
            
            /* Faction Header */
            .faction-header {{ background: rgba(45, 45, 45, 0.9); border: 1px solid #ff6600; border-radius: 8px; padding: 20px; margin-bottom: 20px; text-align: center; }}
            .faction-title {{ color: #ff6600; font-size: 36px; font-weight: bold; margin-bottom: 10px; }}
            .faction-subtitle {{ color: #ffd700; font-size: 18px; margin-bottom: 15px; }}
            .faction-warning {{ color: #ff4444; font-size: 14px; background: rgba(255, 68, 68, 0.1); padding: 10px; border-radius: 5px; border: 1px solid #ff4444; }}
            
            /* Current Faction Display */
            .current-faction {{ background: rgba(0, 100, 0, 0.2); border: 2px solid #00ff00; border-radius: 12px; padding: 25px; margin-bottom: 30px; text-align: center; }}
            .current-faction-title {{ color: #00ff00; font-size: 24px; font-weight: bold; margin-bottom: 15px; }}
            .loyalty-display {{ display: flex; justify-content: center; gap: 30px; margin: 20px 0; }}
            .loyalty-stat {{ text-align: center; }}
            .loyalty-value {{ font-size: 32px; font-weight: bold; color: #ffd700; }}
            .loyalty-label {{ color: #ccc; font-size: 12px; }}
            .faction-benefits {{ background: rgba(0,0,0,0.3); border-radius: 8px; padding: 15px; margin-top: 15px; }}
            .benefit {{ margin: 5px 0; color: #90ee90; }}
            
            /* Faction Selection Grid */
            .factions-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 25px; margin-bottom: 30px; }}
            
            /* Faction Cards */
            .faction-card {{ 
                background: rgba(45, 45, 45, 0.9);
                border: 3px solid transparent;
                border-radius: 15px;
                padding: 25px;
                text-align: center;
                transition: all 0.3s;
                position: relative;
                overflow: hidden;
            }}
            .faction-card.alvar {{ border-color: #ff4444; }}
            .faction-card.delruk {{ border-color: #4444ff; }}
            .faction-card.vordyn {{ border-color: #44ff44; }}
            .faction-card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
            
            .faction-backdrop {{ 
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                opacity: 0.1;
                z-index: 0;
            }}
            .alvar .faction-backdrop {{ background: linear-gradient(45deg, #ff4444, #ff6666); }}
            .delruk .faction-backdrop {{ background: linear-gradient(45deg, #4444ff, #6666ff); }}
            .vordyn .faction-backdrop {{ background: linear-gradient(45deg, #44ff44, #66ff66); }}
            
            .faction-content {{ position: relative; z-index: 1; }}
            .faction-icon {{ font-size: 64px; margin-bottom: 15px; }}
            .faction-name {{ font-size: 28px; font-weight: bold; margin-bottom: 10px; }}
            .faction-name.alvar {{ color: #ff4444; }}
            .faction-name.delruk {{ color: #4444ff; }}
            .faction-name.vordyn {{ color: #44ff44; }}
            
            .faction-description {{ color: #ccc; margin-bottom: 20px; line-height: 1.4; }}
            .faction-stats {{ background: rgba(0,0,0,0.5); border-radius: 8px; padding: 15px; margin-bottom: 20px; }}
            .faction-stat {{ display: flex; justify-content: space-between; margin: 8px 0; }}
            .stat-label {{ color: #ccc; }}
            .stat-value {{ font-weight: bold; }}
            .stat-value.alvar {{ color: #ff6666; }}
            .stat-value.delruk {{ color: #6666ff; }}
            .stat-value.vordyn {{ color: #66ff66; }}
            
            .faction-btn {{ 
                width: 100%;
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s;
            }}
            .btn-join-alvar {{ background: linear-gradient(45deg, #ff4444, #ff6666); color: white; }}
            .btn-join-alvar:hover {{ background: linear-gradient(45deg, #ff6666, #ff8888); }}
            .btn-join-delruk {{ background: linear-gradient(45deg, #4444ff, #6666ff); color: white; }}
            .btn-join-delruk:hover {{ background: linear-gradient(45deg, #6666ff, #8888ff); }}
            .btn-join-vordyn {{ background: linear-gradient(45deg, #44ff44, #66ff66); color: white; }}
            .btn-join-vordyn:hover {{ background: linear-gradient(45deg, #66ff66, #88ff88); }}
            .btn-current {{ background: #ffd700; color: #000; }}
            .btn-cooldown {{ background: #666; color: #999; cursor: not-allowed; }}
            
            /* Faction Wars Section */
            .wars-section {{ background: rgba(45, 45, 45, 0.9); border: 1px solid #ff6600; border-radius: 12px; padding: 25px; margin-bottom: 30px; }}
            .wars-title {{ color: #ff6600; font-size: 24px; font-weight: bold; margin-bottom: 20px; text-align: center; }}
            .war-status {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}
            .war-faction {{ text-align: center; padding: 15px; border-radius: 8px; }}
            .war-faction.alvar {{ background: rgba(255, 68, 68, 0.2); border: 1px solid #ff4444; }}
            .war-faction.delruk {{ background: rgba(68, 68, 255, 0.2); border: 1px solid #4444ff; }}
            .war-faction.vordyn {{ background: rgba(68, 255, 68, 0.2); border: 1px solid #44ff44; }}
            .war-score {{ font-size: 32px; font-weight: bold; }}
            .war-members {{ color: #ccc; font-size: 12px; }}
            
            /* Loyalty Mission Panel */
            .missions-panel {{ background: rgba(45, 45, 45, 0.9); border: 1px solid #ffd700; border-radius: 12px; padding: 25px; }}
            .missions-title {{ color: #ffd700; font-size: 20px; font-weight: bold; margin-bottom: 20px; text-align: center; }}
            .mission-card {{ 
                background: #333;
                border-left: 4px solid #ffd700;
                padding: 15px;
                margin: 10px 0;
                border-radius: 0 8px 8px 0;
            }}
            .mission-name {{ font-weight: bold; color: #ffd700; margin-bottom: 5px; }}
            .mission-description {{ color: #ccc; font-size: 13px; margin-bottom: 8px; }}
            .mission-reward {{ color: #90ee90; font-size: 12px; }}
            .mission-btn {{ 
                padding: 8px 15px;
                background: #ffd700;
                color: #000;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
                margin-top: 10px;
            }}
            
            /* Faction Change Cooldown */
            .cooldown-info {{ background: rgba(255, 68, 68, 0.1); border: 1px solid #ff4444; border-radius: 8px; padding: 15px; margin: 15px 0; text-align: center; }}
            .cooldown-text {{ color: #ff4444; }}
            .cooldown-timer {{ font-weight: bold; color: #ffd700; }}
        </style>
    </head>
    <body class="faction-bg">
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
            <!-- Faction Header -->
            <div class="faction-header">
                <div class="faction-title">⚔️ FACTION WARS ⚔️</div>
                <div class="faction-subtitle">Choose your allegiance • Fight for your faction • Earn exclusive rewards</div>
                <div class="faction-warning">
                    ⚠️ WARNING: Faction choice affects PvP, available quests, and endgame content. Choose wisely!
                </div>
            </div>
            
            {generate_current_faction_display(character, current_faction) if current_faction else ''}
            
            <!-- Faction Selection -->
            <div class="factions-grid">
                {generate_faction_cards(factions, character)}
            </div>
            
            <!-- Faction Wars Status -->
            <div class="wars-section">
                <div class="wars-title">🏛️ CURRENT FACTION WAR STATUS</div>
                <div class="war-status">
                    <div class="war-faction alvar">
                        <div class="war-score" style="color: #ff4444;">2,847</div>
                        <div>Alvar Liberation</div>
                        <div class="war-members">234 active members</div>
                    </div>
                    <div class="war-faction delruk">
                        <div class="war-score" style="color: #4444ff;">3,156</div>
                        <div>Delruk Alliance</div>
                        <div class="war-members">312 active members</div>
                    </div>
                    <div class="war-faction vordyn">
                        <div class="war-score" style="color: #44ff44;">2,999</div>
                        <div>Vordyn Rebellion</div>
                        <div class="war-members">287 active members</div>
                    </div>
                </div>
                <div style="text-align: center; margin-top: 15px; color: #ccc; font-size: 12px;">
                    War scores update every hour • Monthly rewards based on faction performance
                </div>
            </div>
            
            <!-- Loyalty Missions -->
            <div class="missions-panel">
                <div class="missions-title">🎯 LOYALTY MISSIONS</div>
                {generate_loyalty_missions(character, current_faction)}
            </div>
        </div>
        
        <script>
        function joinFaction(factionId, factionName) {{
            if (confirm(`Join ${{factionName}}? This choice cannot be changed for 30 days!`)) {{
                fetch(`/factions/join/${{factionId}}`, {{method: 'POST'}})
                .then(response => {{
                    if (response.ok) {{
                        alert(`Welcome to ${{factionName}}!`);
                        location.reload();
                    }} else {{
                        alert('Failed to join faction. You may be on cooldown.');
                    }}
                }});
            }}
        }}
        
        function completeMission(missionId) {{
            fetch(`/factions/mission/${{missionId}}`, {{method: 'POST'}})
            .then(response => {{
                if (response.ok) {{
                    alert('Mission completed! Loyalty points earned.');
                    location.reload();
                }} else {{
                    alert('Failed to complete mission.');
                }}
            }});
        }}
        
        function leaveFaction() {{
            if (confirm('Leave your current faction? You will lose all loyalty points and cannot join another faction for 30 days!')) {{
                fetch('/factions/leave', {{method: 'POST'}})
                .then(response => {{
                    if (response.ok) {{
                        alert('You have left your faction.');
                        location.reload();
                    }} else {{
                        alert('Failed to leave faction.');
                    }}
                }});
            }}
        }}
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def faction_locked_page(character):
    """Show faction locked page for characters under level 91"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Factions - Locked</title>
        <style>
            body {{ font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; text-align: center; padding: 50px; }}
            .locked-container {{ max-width: 600px; margin: 0 auto; background: #333; padding: 40px; border-radius: 10px; }}
            .locked-title {{ color: #ff6600; font-size: 32px; margin-bottom: 20px; }}
            .locked-message {{ margin: 20px 0; line-height: 1.6; }}
            .level-requirement {{ color: #ffd700; font-size: 24px; font-weight: bold; margin: 20px 0; }}
            .progress-bar {{ width: 100%; height: 20px; background: #555; border-radius: 10px; overflow: hidden; margin: 20px 0; }}
            .progress-fill {{ height: 100%; background: linear-gradient(90deg, #ff6600, #ffd700); }}
            .back-link {{ color: #ff6600; text-decoration: none; font-size: 18px; }}
        </style>
    </head>
    <body>
        <div class="locked-container">
            <div class="locked-title">🔒 FACTIONS LOCKED</div>
            <div class="locked-message">
                The faction system is only available to elite warriors who have proven themselves in combat.
                <br><br>
                Reach level 91 to unlock the ability to join one of the three great factions and participate in epic faction wars!
            </div>
            <div class="level-requirement">Level Requirement: 91</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {(character.level / 91) * 100}%;"></div>
            </div>
            <div style="margin: 20px 0;">
                Current Level: {character.level}/91 ({91 - character.level} levels to go)
            </div>
            <a href="/game" class="back-link">← Return to Game</a>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

def generate_current_faction_display(character, current_faction):
    """Generate current faction display"""
    if not current_faction:
        return ""
    
    return f"""
    <div class="current-faction">
        <div class="current-faction-title">🏛️ {current_faction['name']}</div>
        <div style="color: #ccc; margin-bottom: 15px;">{current_faction['description']}</div>
        
        <div class="loyalty-display">
            <div class="loyalty-stat">
                <div class="loyalty-value">{character.alvar_loyalty}</div>
                <div class="loyalty-label">Alvar Loyalty</div>
            </div>
            <div class="loyalty-stat">
                <div class="loyalty-value">{character.delruk_loyalty}</div>
                <div class="loyalty-label">Delruk Loyalty</div>
            </div>
            <div class="loyalty-stat">
                <div class="loyalty-value">{character.vordyn_loyalty}</div>
                <div class="loyalty-label">Vordyn Loyalty</div>
            </div>
        </div>
        
        <div class="faction-benefits">
            <div style="color: #ffd700; font-weight: bold; margin-bottom: 10px;">Current Benefits:</div>
            <div class="benefit">• +{current_faction['bonus_per_loyalty']*100}% {current_faction['damage_type']} damage per loyalty point</div>
            <div class="benefit">• Access to faction-exclusive quests and dungeons</div>
            <div class="benefit">• Faction-only marketplace and items</div>
            <div class="benefit">• Priority in faction war battles</div>
        </div>
        
        <button onclick="leaveFaction()" style="margin-top: 15px; padding: 10px 20px; background: #ff4444; color: white; border: none; border-radius: 5px; cursor: pointer;">
            LEAVE FACTION
        </button>
    </div>
    """

def generate_faction_cards(factions, character):
    """Generate faction selection cards"""
    cards_html = ""
    faction_classes = {1: 'alvar', 2: 'delruk', 3: 'vordyn'}
    faction_icons = {1: '⚔️', 2: '🛡️', 3: '🔥'}
    
    # Check if character can change factions (30 day cooldown)
    can_change = character.faction_changes_this_month < 1
    
    for faction in factions:
        faction_class = faction_classes.get(faction['id'], 'alvar')
        faction_icon = faction_icons.get(faction['id'], '⚔️')
        
        # Determine button state
        if character.faction_id == faction['id']:
            button_class = "btn-current"
            button_text = "CURRENT FACTION"
            button_action = ""
        elif not can_change and character.faction_id:
            button_class = "btn-cooldown"
            button_text = "COOLDOWN ACTIVE"
            button_action = ""
        else:
            button_class = f"btn-join-{faction_class}"
            button_text = f"JOIN {faction['name'].upper()}"
            button_action = f"onclick=\"joinFaction({faction['id']}, '{faction['name']}')\""
        
        cards_html += f"""
        <div class="faction-card {faction_class}">
            <div class="faction-backdrop"></div>
            <div class="faction-content">
                <div class="faction-icon">{faction_icon}</div>
                <div class="faction-name {faction_class}">{faction['name']}</div>
                <div class="faction-description">{faction['description']}</div>
                
                <div class="faction-stats">
                    <div class="faction-stat">
                        <span class="stat-label">Specialization:</span>
                        <span class="stat-value {faction_class}">{faction['damage_type'].title()}</span>
                    </div>
                    <div class="faction-stat">
                        <span class="stat-label">Loyalty Bonus:</span>
                        <span class="stat-value {faction_class}">+{faction['bonus_per_loyalty']*100}% per point</span>
                    </div>
                    <div class="faction-stat">
                        <span class="stat-label">Active Members:</span>
                        <span class="stat-value {faction_class}">{150 + faction['id'] * 50}</span>
                    </div>
                    <div class="faction-stat">
                        <span class="stat-label">War Score:</span>
                        <span class="stat-value {faction_class}">{2800 + faction['id'] * 100}</span>
                    </div>
                </div>
                
                <button class="faction-btn {button_class}" {button_action}>
                    {button_text}
                </button>
            </div>
        </div>
        """
    
    if not can_change and character.faction_id:
        cards_html += """
        <div class="cooldown-info">
            <div class="cooldown-text">Faction Change Cooldown Active</div>
            <div class="cooldown-timer">29 days, 14 hours remaining</div>
            <div style="font-size: 12px; margin-top: 5px;">You can only change factions once per month</div>
        </div>
        """
    
    return cards_html

def generate_loyalty_missions(character, current_faction):
    """Generate loyalty missions"""
    if not current_faction:
        return """
        <div style="text-align: center; color: #ccc; padding: 40px;">
            Join a faction to access loyalty missions and exclusive rewards!
        </div>
        """
    
    missions = [
        {
            'id': 'pvp_wins',
            'name': 'Faction Champion',
            'description': 'Win 5 PvP battles against enemy faction members',
            'reward': '+10 Loyalty Points, 50,000 Gold',
            'progress': '2/5'
        },
        {
            'id': 'dungeon_clear',
            'name': 'Sacred Dungeon',
            'description': 'Complete your faction\'s sacred dungeon',
            'reward': '+25 Loyalty Points, Faction Equipment',
            'progress': 'Available'
        },
        {
            'id': 'resource_gather',
            'name': 'Resource Gathering',
            'description': 'Gather 100 faction-specific resources',
            'reward': '+5 Loyalty Points, 25,000 Gold',
            'progress': '67/100'
        }
    ]
    
    missions_html = ""
    for mission in missions:
        missions_html += f"""
        <div class="mission-card">
            <div class="mission-name">{mission['name']}</div>
            <div class="mission-description">{mission['description']}</div>
            <div class="mission-reward">Rewards: {mission['reward']}</div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                <div style="color: #88ccff; font-size: 12px;">Progress: {mission['progress']}</div>
                <button class="mission-btn" onclick="completeMission('{mission['id']}')">
                    COMPLETE
                </button>
            </div>
        </div>
        """
    
    return missions_html

async def join_faction(request: web_request.Request):
    """Join a faction"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        return web.Response(text="Character not found", status=400)
    
    if character.level < 91:
        return web.Response(text="Level 91 required", status=400)
    
    faction_id = int(request.match_info['faction_id'])
    
    # Check cooldown
    if character.faction_changes_this_month >= 1:
        return web.Response(text="Faction change cooldown active", status=400)
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        # Update character faction
        await conn.execute('''
            UPDATE characters 
            SET faction_id = :faction_id, faction_changes_this_month = faction_changes_this_month + 1
            WHERE id = :character_id
        ''', {'faction_id': faction_id, 'character_id': character.id})
        
        await conn.commit()
    
    return web.Response(text="Faction joined")

async def leave_faction(request: web_request.Request):
    """Leave current faction"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        return web.Response(text="Character not found", status=400)
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        # Clear faction and loyalty points
        await conn.execute('''
            UPDATE characters 
            SET faction_id = NULL, 
                alvar_loyalty = 0, 
                delruk_loyalty = 0, 
                vordyn_loyalty = 0,
                faction_changes_this_month = faction_changes_this_month + 1
            WHERE id = :character_id
        ''', {'character_id': character.id})
        
        await conn.commit()
    
    return web.Response(text="Faction left")