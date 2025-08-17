from aiohttp import web, web_request
import random

from database import get_db
from handlers.auth import require_login
from handlers.character import get_current_character

async def quest_helper(request: web_request.Request):
    """Quest helper interface"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    # Get quest search parameter
    search_term = request.query.get('search', '').lower()
    
    # Generate available quests based on character level
    available_quests = generate_quests_for_level(character.level, search_term)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Quest Helper - Outwar</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: Arial, sans-serif; color: #ffffff; }}
            
            /* Quest Background */
            body.quest-bg {{ 
                background-color: #2d2d0a !important;
                background: linear-gradient(135deg, #2d2d0a 0%, #4a4a1a 50%, #2d2d0a 100%);
                min-height: 100vh;
                background-image: 
                    radial-gradient(circle at 20% 50%, rgba(255, 255, 0, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 80% 30%, rgba(255, 215, 0, 0.1) 0%, transparent 50%);
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
            .main-container {{ padding: 20px; max-width: 1200px; margin: 0 auto; }}
            
            /* Quest Header */
            .quest-header {{ background: rgba(45, 45, 45, 0.9); border: 1px solid #ffd700; border-radius: 8px; padding: 20px; margin-bottom: 20px; text-align: center; }}
            .quest-title {{ color: #ffd700; font-size: 32px; font-weight: bold; margin-bottom: 10px; }}
            .quest-subtitle {{ color: #ffeb3b; font-size: 16px; margin-bottom: 15px; }}
            
            /* Search Section */
            .search-section {{ background: rgba(45, 45, 45, 0.9); border: 1px solid #ffd700; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
            .search-title {{ color: #ffd700; font-size: 18px; font-weight: bold; margin-bottom: 15px; }}
            .search-controls {{ display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }}
            .search-input {{ 
                flex: 1;
                min-width: 200px;
                padding: 10px;
                background: #333;
                border: 1px solid #666;
                border-radius: 5px;
                color: white;
                font-size: 14px;
            }}
            .search-btn {{ 
                padding: 10px 20px;
                background: linear-gradient(45deg, #ffd700, #ffeb3b);
                color: #000;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
            }}
            .filter-select {{ 
                padding: 8px;
                background: #333;
                border: 1px solid #666;
                border-radius: 5px;
                color: white;
            }}
            
            /* Quest Grid */
            .quests-container {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            
            /* Quest Cards */
            .quest-card {{ 
                background: rgba(45, 45, 45, 0.9);
                border: 2px solid #555;
                border-radius: 12px;
                padding: 20px;
                transition: all 0.3s;
                position: relative;
            }}
            .quest-card:hover {{ border-color: #ffd700; transform: translateY(-3px); }}
            .quest-card.daily {{ border-color: #32cd32; }}
            .quest-card.weekly {{ border-color: #ff6600; }}
            .quest-card.main {{ border-color: #ffd700; }}
            .quest-card.side {{ border-color: #87ceeb; }}
            
            .quest-type {{ 
                position: absolute;
                top: 10px;
                right: 10px;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
                text-transform: uppercase;
            }}
            .type-daily {{ background: #32cd32; color: white; }}
            .type-weekly {{ background: #ff6600; color: white; }}
            .type-main {{ background: #ffd700; color: #000; }}
            .type-side {{ background: #87ceeb; color: #000; }}
            
            .quest-icon {{ font-size: 32px; margin-bottom: 10px; }}
            .quest-name {{ font-size: 18px; font-weight: bold; color: #ffd700; margin-bottom: 8px; }}
            .quest-giver {{ color: #87ceeb; font-size: 12px; margin-bottom: 10px; }}
            .quest-description {{ color: #ccc; margin-bottom: 15px; line-height: 1.4; font-size: 13px; }}
            
            .quest-objectives {{ margin-bottom: 15px; }}
            .objective-title {{ color: #ffd700; font-size: 12px; font-weight: bold; margin-bottom: 5px; }}
            .objective-item {{ 
                background: #333;
                padding: 6px 10px;
                border-radius: 4px;
                margin: 3px 0;
                font-size: 11px;
                border-left: 3px solid #ffd700;
            }}
            
            .quest-rewards {{ margin-bottom: 15px; }}
            .rewards-title {{ color: #32cd32; font-size: 12px; font-weight: bold; margin-bottom: 5px; }}
            .reward-item {{ 
                display: inline-block;
                background: #444;
                padding: 3px 6px;
                border-radius: 3px;
                margin: 2px;
                font-size: 10px;
            }}
            .reward-exp {{ color: #87ceeb; }}
            .reward-gold {{ color: #ffd700; }}
            .reward-item-drop {{ color: #ff8c00; }}
            
            .quest-location {{ color: #90ee90; font-size: 11px; margin-bottom: 15px; }}
            .quest-level {{ color: #ccc; font-size: 11px; margin-bottom: 15px; }}
            
            .quest-actions {{ display: flex; gap: 10px; }}
            .quest-btn {{ 
                flex: 1;
                padding: 8px;
                font-size: 12px;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                transition: all 0.3s;
            }}
            .btn-accept {{ background: linear-gradient(45deg, #32cd32, #90ee90); color: white; }}
            .btn-accept:hover {{ background: linear-gradient(45deg, #90ee90, #98fb98); }}
            .btn-track {{ background: linear-gradient(45deg, #ffd700, #ffeb3b); color: #000; }}
            .btn-track:hover {{ background: linear-gradient(45deg, #ffeb3b, #ffff00); }}
            .btn-navigate {{ background: linear-gradient(45deg, #87ceeb, #add8e6); color: #000; }}
            .btn-navigate:hover {{ background: linear-gradient(45deg, #add8e6, #b0e0e6); }}
            .btn-unavailable {{ background: #666; color: #999; cursor: not-allowed; }}
            
            /* Active Quest Tracker */
            .active-tracker {{ 
                position: fixed;
                top: 100px;
                right: 20px;
                width: 300px;
                background: rgba(45, 45, 45, 0.95);
                border: 2px solid #ffd700;
                border-radius: 10px;
                padding: 15px;
                z-index: 1000;
            }}
            .tracker-title {{ color: #ffd700; font-size: 14px; font-weight: bold; margin-bottom: 10px; text-align: center; }}
            .tracked-quest {{ margin-bottom: 10px; }}
            .tracked-name {{ color: #87ceeb; font-size: 12px; font-weight: bold; }}
            .tracked-progress {{ color: #ccc; font-size: 11px; }}
            .progress-bar {{ 
                width: 100%;
                height: 6px;
                background: #333;
                border-radius: 3px;
                overflow: hidden;
                margin: 3px 0;
            }}
            .progress-fill {{ 
                height: 100%;
                background: linear-gradient(90deg, #32cd32, #90ee90);
                transition: width 0.3s;
            }}
            
            /* Quest Log */
            .quest-log {{ background: rgba(45, 45, 45, 0.9); border: 1px solid #ffd700; border-radius: 8px; padding: 20px; margin-top: 20px; }}
            .log-title {{ color: #ffd700; font-size: 18px; font-weight: bold; margin-bottom: 15px; text-align: center; }}
            .log-tabs {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 15px; }}
            .log-tab {{ padding: 8px 16px; background: #444; color: white; border: none; border-radius: 5px; cursor: pointer; }}
            .log-tab.active {{ background: #ffd700; color: #000; }}
        </style>
    </head>
    <body class="quest-bg">
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
            <!-- Quest Header -->
            <div class="quest-header">
                <div class="quest-title">📜 QUEST HELPER</div>
                <div class="quest-subtitle">Find and track your adventures • Discover new challenges • Earn great rewards</div>
            </div>
            
            <!-- Search Section -->
            <div class="search-section">
                <div class="search-title">🔍 QUEST SEARCH</div>
                <div class="search-controls">
                    <input type="text" class="search-input" id="questSearch" placeholder="Search for quests, NPCs, or locations..." value="{search_term}">
                    <select class="filter-select" id="questFilter">
                        <option value="all">All Quests</option>
                        <option value="daily">Daily Quests</option>
                        <option value="weekly">Weekly Quests</option>
                        <option value="main">Main Story</option>
                        <option value="side">Side Quests</option>
                    </select>
                    <select class="filter-select" id="levelFilter">
                        <option value="all">All Levels</option>
                        <option value="mylevel">My Level ({character.level})</option>
                        <option value="lower">Below My Level</option>
                        <option value="higher">Above My Level</option>
                    </select>
                    <button class="search-btn" onclick="searchQuests()">SEARCH</button>
                </div>
            </div>
            
            <!-- Available Quests -->
            <div class="quests-container">
                {generate_quest_cards(available_quests, character)}
            </div>
            
            <!-- Quest Log -->
            <div class="quest-log">
                <div class="log-title">📋 QUEST LOG</div>
                <div class="log-tabs">
                    <button class="log-tab active" onclick="switchLogTab('active')">Active Quests</button>
                    <button class="log-tab" onclick="switchLogTab('completed')">Completed</button>
                    <button class="log-tab" onclick="switchLogTab('failed')">Failed</button>
                </div>
                <div id="activeQuests">
                    {generate_active_quests(character)}
                </div>
                <div id="completedQuests" style="display: none;">
                    {generate_completed_quests(character)}
                </div>
                <div id="failedQuests" style="display: none;">
                    {generate_failed_quests(character)}
                </div>
            </div>
        </div>
        
        <!-- Active Quest Tracker -->
        <div class="active-tracker">
            <div class="tracker-title">🎯 ACTIVE QUESTS</div>
            {generate_quest_tracker(character)}
        </div>
        
        <script>
        function searchQuests() {{
            const searchTerm = document.getElementById('questSearch').value;
            const filter = document.getElementById('questFilter').value;
            const levelFilter = document.getElementById('levelFilter').value;
            
            const params = new URLSearchParams();
            if (searchTerm) params.append('search', searchTerm);
            if (filter !== 'all') params.append('filter', filter);
            if (levelFilter !== 'all') params.append('level', levelFilter);
            
            window.location.href = '/quests?' + params.toString();
        }}
        
        function acceptQuest(questId, questName) {{
            if (confirm(`Accept quest: ${{questName}}?`)) {{
                fetch(`/quests/accept/${{questId}}`, {{method: 'POST'}})
                .then(response => {{
                    if (response.ok) {{
                        alert('Quest accepted! Check your quest log for objectives.');
                        location.reload();
                    }} else {{
                        alert('Failed to accept quest.');
                    }}
                }});
            }}
        }}
        
        function trackQuest(questId) {{
            fetch(`/quests/track/${{questId}}`, {{method: 'POST'}})
            .then(response => {{
                if (response.ok) {{
                    alert('Quest is now being tracked!');
                    location.reload();
                }} else {{
                    alert('Failed to track quest.');
                }}
            }});
        }}
        
        function navigateToQuest(location) {{
            alert(`Navigation: Head to ${{location}} to continue this quest. Use the minimap to find your way!`);
        }}
        
        function switchLogTab(tab) {{
            // Hide all tab contents
            document.getElementById('activeQuests').style.display = 'none';
            document.getElementById('completedQuests').style.display = 'none';
            document.getElementById('failedQuests').style.display = 'none';
            
            // Remove active class from all tabs
            document.querySelectorAll('.log-tab').forEach(t => t.classList.remove('active'));
            
            // Show selected tab content
            document.getElementById(tab + 'Quests').style.display = 'block';
            
            // Add active class to clicked tab
            event.target.classList.add('active');
        }}
        
        // Auto-search when typing
        document.getElementById('questSearch').addEventListener('input', function() {{
            if (this.value.length >= 3 || this.value.length === 0) {{
                setTimeout(searchQuests, 500);
            }}
        }});
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

def generate_quests_for_level(level, search_term=""):
    """Generate quests appropriate for character level"""
    all_quests = [
        {
            'id': 'daily_combat_training',
            'name': 'Combat Training',
            'type': 'daily',
            'icon': '⚔️',
            'giver': 'Combat Instructor Marcus',
            'location': 'Training Grounds',
            'level_req': 1,
            'description': 'Practice your combat skills by defeating training dummies and sparring with other warriors.',
            'objectives': ['Defeat 5 training dummies', 'Win 2 sparring matches'],
            'rewards': ['1,500 EXP', '2,000 Gold', 'Combat Manual'],
            'status': 'available'
        },
        {
            'id': 'weekly_exploration',
            'name': 'Explore the Unknown',
            'type': 'weekly',
            'icon': '🗺️',
            'giver': 'Explorer Captain Sarah',
            'location': 'Adventure Guild',
            'level_req': 5,
            'description': 'Venture into uncharted territories and document your discoveries for the Explorer\'s Guild.',
            'objectives': ['Visit 3 new locations', 'Collect 10 rare specimens', 'Map unknown areas'],
            'rewards': ['5,000 EXP', '10,000 Gold', 'Explorer\'s Badge'],
            'status': 'available'
        },
        {
            'id': 'main_dragon_threat',
            'name': 'The Dragon Threat',
            'type': 'main',
            'icon': '🐲',
            'giver': 'King Aldric',
            'location': 'Royal Throne Room',
            'level_req': 30,
            'description': 'Ancient dragons have awakened and threaten the kingdom. Investigate their return and find a way to stop them.',
            'objectives': ['Investigate dragon sightings', 'Gather ancient dragon lore', 'Prepare for final battle'],
            'rewards': ['25,000 EXP', '50,000 Gold', 'Royal Commendation', 'Dragon Slayer Title'],
            'status': 'locked' if level < 30 else 'available'
        },
        {
            'id': 'side_merchant_troubles',
            'name': 'Merchant\'s Troubles',
            'type': 'side',
            'icon': '💰',
            'giver': 'Merchant Bob',
            'location': 'Marketplace',
            'level_req': 10,
            'description': 'Local merchant is having trouble with bandits stealing his goods. Help him secure his trade routes.',
            'objectives': ['Eliminate bandit camp', 'Recover stolen goods', 'Escort merchant convoy'],
            'rewards': ['3,000 EXP', '5,000 Gold', 'Merchant Discount'],
            'status': 'available' if level >= 10 else 'locked'
        },
        {
            'id': 'daily_herb_gathering',
            'name': 'Herb Gathering',
            'type': 'daily',
            'icon': '🌿',
            'giver': 'Herbalist Elena',
            'location': 'Alchemist Shop',
            'level_req': 1,
            'description': 'Collect medicinal herbs from the wilderness for the local herbalist.',
            'objectives': ['Collect 20 healing herbs', 'Find 5 rare mushrooms'],
            'rewards': ['800 EXP', '1,200 Gold', 'Health Potion x3'],
            'status': 'available'
        }
    ]
    
    # Filter quests based on search term
    if search_term:
        all_quests = [q for q in all_quests if 
                     search_term in q['name'].lower() or 
                     search_term in q['description'].lower() or
                     search_term in q['giver'].lower() or
                     search_term in q['location'].lower()]
    
    return all_quests

def generate_quest_cards(quests, character):
    """Generate HTML for quest cards"""
    if not quests:
        return '<div style="grid-column: 1/-1; text-align: center; color: #ccc; padding: 40px;">No quests found matching your criteria.</div>'
    
    cards_html = ""
    for quest in quests:
        # Build objectives HTML
        objectives_html = ""
        for obj in quest['objectives']:
            objectives_html += f'<div class="objective-item">{obj}</div>'
        
        # Build rewards HTML
        rewards_html = ""
        for reward in quest['rewards']:
            reward_class = ""
            if 'EXP' in reward:
                reward_class = "reward-exp"
            elif 'Gold' in reward:
                reward_class = "reward-gold"
            else:
                reward_class = "reward-item-drop"
            
            rewards_html += f'<span class="reward-item {reward_class}">{reward}</span>'
        
        # Determine availability
        is_available = quest['status'] == 'available' and character.level >= quest['level_req']
        button_html = ""
        
        if quest['status'] == 'locked' or character.level < quest['level_req']:
            button_html = '<button class="quest-btn btn-unavailable">LEVEL LOCKED</button>'
        elif is_available:
            button_html = f'''
            <button class="quest-btn btn-accept" onclick="acceptQuest('{quest['id']}', '{quest['name']}')">ACCEPT</button>
            <button class="quest-btn btn-track" onclick="trackQuest('{quest['id']}')">TRACK</button>
            <button class="quest-btn btn-navigate" onclick="navigateToQuest('{quest['location']}')">NAVIGATE</button>
            '''
        
        cards_html += f'''
        <div class="quest-card {quest['type']}">
            <div class="quest-type type-{quest['type']}">{quest['type']}</div>
            <div class="quest-icon">{quest['icon']}</div>
            <div class="quest-name">{quest['name']}</div>
            <div class="quest-giver">Quest Giver: {quest['giver']}</div>
            <div class="quest-description">{quest['description']}</div>
            
            <div class="quest-objectives">
                <div class="objective-title">Objectives:</div>
                {objectives_html}
            </div>
            
            <div class="quest-rewards">
                <div class="rewards-title">Rewards:</div>
                {rewards_html}
            </div>
            
            <div class="quest-location">📍 Location: {quest['location']}</div>
            <div class="quest-level">⭐ Required Level: {quest['level_req']}</div>
            
            <div class="quest-actions">
                {button_html}
            </div>
        </div>
        '''
    
    return cards_html

def generate_active_quests(character):
    """Generate active quests display"""
    return '''
    <div style="text-align: center; color: #ccc; padding: 20px;">
        <div style="font-size: 18px; margin-bottom: 10px;">📜 No Active Quests</div>
        <div>Accept quests from NPCs to start your adventures!</div>
    </div>
    '''

def generate_completed_quests(character):
    """Generate completed quests display"""
    return '''
    <div style="text-align: center; color: #ccc; padding: 20px;">
        <div style="font-size: 18px; margin-bottom: 10px;">✅ No Completed Quests</div>
        <div>Complete quests to see your achievements here!</div>
    </div>
    '''

def generate_failed_quests(character):
    """Generate failed quests display"""
    return '''
    <div style="text-align: center; color: #ccc; padding: 20px;">
        <div style="font-size: 18px; margin-bottom: 10px;">❌ No Failed Quests</div>
        <div>Failed quests will appear here. Don't give up!</div>
    </div>
    '''

def generate_quest_tracker(character):
    """Generate quest tracker display"""
    return '''
    <div style="text-align: center; color: #ccc; padding: 10px;">
        <div style="font-size: 14px; margin-bottom: 5px;">No tracked quests</div>
        <div style="font-size: 11px;">Accept and track quests to see progress here</div>
    </div>
    '''

async def accept_quest(request: web_request.Request):
    """Accept a quest"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        return web.Response(text="Character not found", status=400)
    
    quest_id = request.match_info['quest_id']
    
    # Here you would implement quest acceptance logic
    # For now, just return success
    return web.Response(text="Quest accepted")

async def track_quest(request: web_request.Request):
    """Track a quest"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        return web.Response(text="Character not found", status=400)
    
    quest_id = request.match_info['quest_id']
    
    # Here you would implement quest tracking logic
    # For now, just return success
    return web.Response(text="Quest tracked")