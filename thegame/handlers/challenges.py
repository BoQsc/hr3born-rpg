from aiohttp import web, web_request
import random
from datetime import datetime, timedelta

from database import get_db
from handlers.auth import require_login
from handlers.character import get_current_character

async def challenges_main(request: web_request.Request):
    """Main challenges interface - Outwar style"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    # Generate daily challenges
    daily_challenges = generate_daily_challenges(character)
    weekly_challenges = generate_weekly_challenges(character)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Challenges & Dungeons - Outwar</title>
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
            .main-container {{ padding: 20px; max-width: 1400px; margin: 0 auto; }}
            
            /* Header */
            .challenges-header {{ background: #2d2d2d; border: 1px solid #555; border-radius: 8px; padding: 20px; margin-bottom: 20px; text-align: center; }}
            .challenges-title {{ color: #4169e1; font-size: 32px; font-weight: bold; margin-bottom: 10px; }}
            .challenges-subtitle {{ color: #ccc; font-size: 16px; }}
            
            /* Tab Navigation */
            .tab-nav {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 30px; }}
            .tab-btn {{ padding: 12px 24px; background: #444; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; transition: all 0.3s; }}
            .tab-btn.active {{ background: #4169e1; color: white; }}
            .tab-btn:hover {{ background: #555; }}
            .tab-btn.active:hover {{ background: #5578ff; }}
            
            /* Content Sections */
            .content-section {{ display: none; }}
            .content-section.active {{ display: block; }}
            
            /* Challenge Cards Grid */
            .challenges-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 20px; margin-bottom: 30px; }}
            .challenge-card {{ background: #2d2d2d; border: 2px solid #444; border-radius: 12px; padding: 20px; transition: all 0.3s; }}
            .challenge-card:hover {{ border-color: #666; }}
            .challenge-card.completed {{ border-color: #00aa00; }}
            .challenge-card.available {{ border-color: #ffd700; }}
            
            .challenge-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; }}
            .challenge-icon {{ font-size: 32px; }}
            .challenge-difficulty {{ 
                padding: 4px 8px; 
                border-radius: 4px; 
                font-size: 10px; 
                font-weight: bold;
                text-transform: uppercase;
            }}
            .difficulty-easy {{ background: #00aa00; color: white; }}
            .difficulty-medium {{ background: #ff8800; color: white; }}
            .difficulty-hard {{ background: #ff4444; color: white; }}
            .difficulty-elite {{ background: #8800cc; color: white; }}
            
            .challenge-title {{ font-size: 18px; font-weight: bold; color: #ffd700; margin-bottom: 8px; }}
            .challenge-description {{ color: #ccc; margin-bottom: 15px; line-height: 1.4; }}
            
            .challenge-objectives {{ margin-bottom: 15px; }}
            .objective {{ 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
                padding: 8px 12px; 
                background: #333; 
                border-radius: 6px; 
                margin-bottom: 5px; 
                font-size: 12px;
            }}
            .objective.completed {{ background: #004400; color: #00ff00; }}
            .objective-progress {{ color: #88ccff; }}
            
            .challenge-rewards {{ margin-bottom: 15px; }}
            .rewards-title {{ font-size: 12px; color: #ffd700; margin-bottom: 5px; }}
            .reward-item {{ 
                display: inline-block; 
                background: #444; 
                padding: 4px 8px; 
                border-radius: 4px; 
                margin: 2px; 
                font-size: 11px;
            }}
            .reward-exp {{ color: #88ccff; }}
            .reward-gold {{ color: #ffd700; }}
            .reward-item-drop {{ color: #ff8800; }}
            
            .challenge-timer {{ color: #ff4444; font-size: 12px; margin-bottom: 15px; }}
            
            .challenge-actions {{ display: flex; gap: 10px; }}
            .challenge-btn {{ 
                flex: 1;
                padding: 10px; 
                border: none; 
                border-radius: 6px; 
                cursor: pointer; 
                font-weight: bold;
                transition: all 0.3s;
            }}
            .btn-start {{ background: #00aa00; color: white; }}
            .btn-start:hover {{ background: #00cc00; }}
            .btn-claim {{ background: #4169e1; color: white; }}
            .btn-claim:hover {{ background: #5578ff; }}
            .btn-disabled {{ background: #666; color: #999; cursor: not-allowed; }}
            
            /* Dungeon Cards */
            .dungeon-card {{ 
                background: linear-gradient(145deg, #2d2d2d, #1a1a1a);
                border: 2px solid #555;
                border-radius: 15px;
                padding: 25px;
                text-align: center;
                transition: all 0.3s;
                position: relative;
                overflow: hidden;
            }}
            .dungeon-card:hover {{ border-color: #ffd700; transform: translateY(-5px); }}
            .dungeon-card.locked {{ opacity: 0.6; }}
            
            .dungeon-backdrop {{ 
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-size: cover;
                background-position: center;
                opacity: 0.1;
                z-index: 0;
            }}
            
            .dungeon-content {{ position: relative; z-index: 1; }}
            .dungeon-icon {{ font-size: 48px; margin-bottom: 15px; }}
            .dungeon-name {{ font-size: 20px; font-weight: bold; color: #ffd700; margin-bottom: 10px; }}
            .dungeon-description {{ color: #ccc; margin-bottom: 15px; }}
            
            .dungeon-stats {{ background: rgba(0,0,0,0.5); border-radius: 8px; padding: 15px; margin-bottom: 15px; }}
            .stat-row {{ display: flex; justify-content: space-between; margin: 5px 0; font-size: 12px; }}
            .stat-label {{ color: #ccc; }}
            .stat-value {{ color: #ffd700; font-weight: bold; }}
            
            .dungeon-btn {{ 
                width: 100%;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s;
            }}
            .btn-enter {{ background: linear-gradient(45deg, #ff6600, #ff8800); color: white; }}
            .btn-enter:hover {{ background: linear-gradient(45deg, #ff8800, #ffaa00); }}
            .btn-locked {{ background: #666; color: #999; cursor: not-allowed; }}
            
            /* Progress Bars */
            .progress-bar {{ 
                width: 100%;
                height: 8px;
                background: #444;
                border-radius: 4px;
                overflow: hidden;
                margin: 5px 0;
            }}
            .progress-fill {{ 
                height: 100%;
                background: linear-gradient(90deg, #00aa00, #00ff00);
                transition: width 0.3s;
            }}
            
            /* Weekly Boss Section */
            .boss-section {{ 
                background: linear-gradient(145deg, #4a0000, #2d0000);
                border: 2px solid #ff4444;
                border-radius: 15px;
                padding: 30px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .boss-title {{ font-size: 28px; color: #ff4444; font-weight: bold; margin-bottom: 15px; }}
            .boss-timer {{ color: #ffd700; font-size: 16px; margin-bottom: 20px; }}
            .boss-rewards {{ display: flex; justify-content: center; gap: 15px; margin-bottom: 20px; }}
            .boss-reward {{ 
                background: rgba(0,0,0,0.5);
                padding: 10px 15px;
                border-radius: 8px;
                border: 1px solid #ff4444;
            }}
        </style>
    </head>
    <body>
        <!-- Top Navigation -->
        <div class="top-nav">
            <div class="nav-tab" onclick="window.location.href='/game'">Explore World</div>
            <div class="nav-tab active">Challenges</div>
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
            <!-- Header -->
            <div class="challenges-header">
                <div class="challenges-title">🏆 CHALLENGES & DUNGEONS</div>
                <div class="challenges-subtitle">Complete challenges for rewards • Explore dangerous dungeons • Face weekly bosses</div>
            </div>
            
            <!-- Tab Navigation -->
            <div class="tab-nav">
                <button class="tab-btn active" onclick="switchTab('daily')">📅 Daily Challenges</button>
                <button class="tab-btn" onclick="switchTab('weekly')">🗓️ Weekly Challenges</button>
                <button class="tab-btn" onclick="switchTab('dungeons')">🏰 Dungeons</button>
                <button class="tab-btn" onclick="switchTab('bosses')">👹 Weekly Bosses</button>
                <button class="tab-btn" onclick="switchTab('raids')">⚔️ Raids</button>
            </div>
            
            <!-- Daily Challenges -->
            <div id="daily" class="content-section active">
                <h3 style="color: #ffd700; margin-bottom: 20px;">Daily Challenges (Resets in 23:45)</h3>
                <div class="challenges-grid">
                    {generate_challenge_cards(daily_challenges)}
                </div>
            </div>
            
            <!-- Weekly Challenges -->
            <div id="weekly" class="content-section">
                <h3 style="color: #ffd700; margin-bottom: 20px;">Weekly Challenges (Resets in 4 days)</h3>
                <div class="challenges-grid">
                    {generate_challenge_cards(weekly_challenges)}
                </div>
            </div>
            
            <!-- Dungeons -->
            <div id="dungeons" class="content-section">
                <h3 style="color: #ffd700; margin-bottom: 20px;">Available Dungeons</h3>
                <div class="challenges-grid">
                    {generate_dungeon_cards(character)}
                </div>
            </div>
            
            <!-- Weekly Bosses -->
            <div id="bosses" class="content-section">
                <div class="boss-section">
                    <div class="boss-title">🐉 WEEKLY WORLD BOSS: Ancient Dragon</div>
                    <div class="boss-timer">⏰ Respawns in: 2 days, 14 hours, 32 minutes</div>
                    <div class="boss-rewards">
                        <div class="boss-reward">
                            <div style="color: #ffd700;">💰 1,000,000 Gold</div>
                        </div>
                        <div class="boss-reward">
                            <div style="color: #88ccff;">📈 500,000 Experience</div>
                        </div>
                        <div class="boss-reward">
                            <div style="color: #ff8800;">🏆 Legendary Items</div>
                        </div>
                    </div>
                    <button class="dungeon-btn btn-locked">BOSS NOT AVAILABLE</button>
                </div>
                
                <h3 style="color: #ffd700; margin-bottom: 20px;">Previous Boss Fights</h3>
                <div class="challenges-grid">
                    {generate_boss_history()}
                </div>
            </div>
            
            <!-- Raids -->
            <div id="raids" class="content-section">
                <h3 style="color: #ffd700; margin-bottom: 20px;">Crew Raids (Requires Crew)</h3>
                <div class="challenges-grid">
                    {generate_raid_cards(character)}
                </div>
            </div>
        </div>
        
        <script>
        function switchTab(tabName) {{
            // Hide all content sections
            document.querySelectorAll('.content-section').forEach(section => {{
                section.classList.remove('active');
            }});
            
            // Remove active class from all tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            
            // Show selected content section
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked tab button
            event.target.classList.add('active');
        }}
        
        function startChallenge(challengeId) {{
            fetch(`/challenges/start/${{challengeId}}`, {{method: 'POST'}})
            .then(response => {{
                if (response.ok) {{
                    alert('Challenge started!');
                    location.reload();
                }} else {{
                    alert('Failed to start challenge.');
                }}
            }});
        }}
        
        function claimReward(challengeId) {{
            fetch(`/challenges/claim/${{challengeId}}`, {{method: 'POST'}})
            .then(response => {{
                if (response.ok) {{
                    alert('Reward claimed!');
                    location.reload();
                }} else {{
                    alert('Failed to claim reward.');
                }}
            }});
        }}
        
        function enterDungeon(dungeonId) {{
            if (confirm('Enter this dungeon? You may face dangerous enemies!')) {{
                window.location.href = `/dungeons/${{dungeonId}}`;
            }}
        }}
        
        function joinRaid(raidId) {{
            if (confirm('Join this raid? You need to be in a crew to participate.')) {{
                fetch(`/raids/join/${{raidId}}`, {{method: 'POST'}})
                .then(response => {{
                    if (response.ok) {{
                        alert('Joined raid!');
                        window.location.href = `/raids/${{raidId}}`;
                    }} else {{
                        alert('Failed to join raid. Make sure you are in a crew.');
                    }}
                }});
            }}
        }}
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

def generate_daily_challenges(character):
    """Generate daily challenges based on character level"""
    challenges = [
        {
            'id': 'daily_combat',
            'icon': '⚔️',
            'title': 'Combat Training',
            'description': 'Engage in player vs player combat to improve your skills.',
            'difficulty': 'easy',
            'objectives': [
                {'text': 'Win 3 PvP battles', 'progress': 1, 'target': 3, 'completed': False},
                {'text': 'Deal 5000 total damage', 'progress': 2840, 'target': 5000, 'completed': False}
            ],
            'rewards': ['2000 EXP', '5000 Gold', 'Combat Potion'],
            'timer': '23:45:12',
            'status': 'available'
        },
        {
            'id': 'daily_explore',
            'icon': '🗺️',
            'title': 'World Explorer',
            'description': 'Explore different areas of the game world.',
            'difficulty': 'easy',
            'objectives': [
                {'text': 'Visit 5 different rooms', 'progress': 3, 'target': 5, 'completed': False},
                {'text': 'Travel 50 total steps', 'progress': 32, 'target': 50, 'completed': False}
            ],
            'rewards': ['1500 EXP', '3000 Gold'],
            'timer': '23:45:12',
            'status': 'available'
        },
        {
            'id': 'daily_equipment',
            'icon': '🛡️',
            'title': 'Equipment Master',
            'description': 'Upgrade and manage your equipment.',
            'difficulty': 'medium',
            'objectives': [
                {'text': 'Equip 3 new items', 'progress': 1, 'target': 3, 'completed': False},
                {'text': 'Trade with marketplace', 'progress': 0, 'target': 1, 'completed': False}
            ],
            'rewards': ['3000 EXP', '8000 Gold', 'Equipment Box'],
            'timer': '23:45:12',
            'status': 'available'
        }
    ]
    return challenges

def generate_weekly_challenges(character):
    """Generate weekly challenges"""
    challenges = [
        {
            'id': 'weekly_power',
            'icon': '💪',
            'title': 'Power Surge',
            'description': 'Increase your total power significantly this week.',
            'difficulty': 'hard',
            'objectives': [
                {'text': 'Gain 1000 total power', 'progress': 450, 'target': 1000, 'completed': False},
                {'text': 'Reach level 30', 'progress': character.level, 'target': 30, 'completed': character.level >= 30}
            ],
            'rewards': ['15000 EXP', '50000 Gold', 'Legendary Item Box'],
            'timer': '4 days, 12:34:56',
            'status': 'available'
        },
        {
            'id': 'weekly_social',
            'icon': '👥',
            'title': 'Social Butterfly',
            'description': 'Interact with other players and build relationships.',
            'difficulty': 'medium',
            'objectives': [
                {'text': 'Join or create a crew', 'progress': 1, 'target': 1, 'completed': True},
                {'text': 'Help 5 crew members', 'progress': 2, 'target': 5, 'completed': False},
                {'text': 'Trade with 3 players', 'progress': 0, 'target': 3, 'completed': False}
            ],
            'rewards': ['10000 EXP', '25000 Gold', 'Social Boost Potion'],
            'timer': '4 days, 12:34:56',
            'status': 'available'
        }
    ]
    return challenges

def generate_challenge_cards(challenges):
    """Generate HTML for challenge cards"""
    cards_html = ""
    for challenge in challenges:
        # Build objectives HTML
        objectives_html = ""
        for obj in challenge['objectives']:
            completed_class = "completed" if obj['completed'] else ""
            progress_text = f"{obj['progress']}/{obj['target']}"
            if obj['completed']:
                progress_text = "✓ Complete"
            
            objectives_html += f'''
            <div class="objective {completed_class}">
                <span>{obj['text']}</span>
                <span class="objective-progress">{progress_text}</span>
            </div>
            '''
        
        # Build rewards HTML
        rewards_html = ""
        for reward in challenge['rewards']:
            reward_class = ""
            if 'EXP' in reward:
                reward_class = "reward-exp"
            elif 'Gold' in reward:
                reward_class = "reward-gold"
            else:
                reward_class = "reward-item-drop"
            
            rewards_html += f'<span class="reward-item {reward_class}">{reward}</span>'
        
        # Determine card status
        card_class = ""
        button_html = ""
        all_completed = all(obj['completed'] for obj in challenge['objectives'])
        
        if all_completed:
            card_class = "completed"
            button_html = '<button class="challenge-btn btn-claim" onclick="claimReward(\'{}\')">CLAIM REWARD</button>'.format(challenge['id'])
        elif challenge['status'] == 'available':
            card_class = "available"
            button_html = '<button class="challenge-btn btn-start" onclick="startChallenge(\'{}\')">START CHALLENGE</button>'.format(challenge['id'])
        else:
            button_html = '<button class="challenge-btn btn-disabled">NOT AVAILABLE</button>'
        
        cards_html += f'''
        <div class="challenge-card {card_class}">
            <div class="challenge-header">
                <div class="challenge-icon">{challenge['icon']}</div>
                <div class="challenge-difficulty difficulty-{challenge['difficulty']}">{challenge['difficulty']}</div>
            </div>
            <div class="challenge-title">{challenge['title']}</div>
            <div class="challenge-description">{challenge['description']}</div>
            
            <div class="challenge-objectives">
                {objectives_html}
            </div>
            
            <div class="challenge-rewards">
                <div class="rewards-title">Rewards:</div>
                {rewards_html}
            </div>
            
            <div class="challenge-timer">⏰ Resets: {challenge['timer']}</div>
            
            <div class="challenge-actions">
                {button_html}
            </div>
        </div>
        '''
    
    return cards_html

def generate_dungeon_cards(character):
    """Generate dungeon cards"""
    dungeons = [
        {
            'id': 'abandoned_mines',
            'icon': '⛏️',
            'name': 'Abandoned Mines',
            'description': 'Dark tunnels filled with dangerous creatures and valuable ore.',
            'min_level': 5,
            'max_level': 20,
            'difficulty': 'Easy',
            'estimated_time': '15-30 minutes',
            'party_size': '1-3 players',
            'rewards': 'Gold, Equipment, Gems',
            'locked': character.level < 5
        },
        {
            'id': 'crystal_caves',
            'icon': '💎',
            'name': 'Crystal Caves',
            'description': 'Mystical caves where powerful crystals grow, guarded by elemental beings.',
            'min_level': 15,
            'max_level': 40,
            'difficulty': 'Medium',
            'estimated_time': '30-60 minutes',
            'party_size': '2-5 players',
            'rewards': 'Rare Equipment, Magical Items',
            'locked': character.level < 15
        },
        {
            'id': 'shadow_fortress',
            'icon': '🏰',
            'name': 'Shadow Fortress',
            'description': 'An ancient fortress corrupted by dark magic, home to powerful undead.',
            'min_level': 30,
            'max_level': 60,
            'difficulty': 'Hard',
            'estimated_time': '1-2 hours',
            'party_size': '3-5 players',
            'rewards': 'Epic Equipment, Rare Materials',
            'locked': character.level < 30
        },
        {
            'id': 'void_temple',
            'icon': '🌌',
            'name': 'Void Temple',
            'description': 'A temple that exists between dimensions, filled with cosmic horrors.',
            'min_level': 50,
            'max_level': 80,
            'difficulty': 'Elite',
            'estimated_time': '2-3 hours',
            'party_size': '5 players',
            'rewards': 'Legendary Equipment, Cosmic Artifacts',
            'locked': character.level < 50
        },
        {
            'id': 'dragon_lair',
            'icon': '🐲',
            'name': 'Ancient Dragon Lair',
            'description': 'The lair of an ancient dragon, the ultimate challenge for heroes.',
            'min_level': 70,
            'max_level': 95,
            'difficulty': 'Mythic',
            'estimated_time': '3-4 hours',
            'party_size': '5+ players',
            'rewards': 'Mythic Equipment, Dragon Scales',
            'locked': character.level < 70
        }
    ]
    
    cards_html = ""
    for dungeon in dungeons:
        locked_class = "locked" if dungeon['locked'] else ""
        button_class = "btn-locked" if dungeon['locked'] else "btn-enter"
        button_text = f"REQUIRES LEVEL {dungeon['min_level']}" if dungeon['locked'] else "ENTER DUNGEON"
        button_action = "" if dungeon['locked'] else f"onclick=\"enterDungeon('{dungeon['id']}')\"" 
        
        cards_html += f'''
        <div class="dungeon-card {locked_class}">
            <div class="dungeon-content">
                <div class="dungeon-icon">{dungeon['icon']}</div>
                <div class="dungeon-name">{dungeon['name']}</div>
                <div class="dungeon-description">{dungeon['description']}</div>
                
                <div class="dungeon-stats">
                    <div class="stat-row">
                        <span class="stat-label">Level Range:</span>
                        <span class="stat-value">{dungeon['min_level']}-{dungeon['max_level']}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Difficulty:</span>
                        <span class="stat-value">{dungeon['difficulty']}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Est. Time:</span>
                        <span class="stat-value">{dungeon['estimated_time']}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Party Size:</span>
                        <span class="stat-value">{dungeon['party_size']}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Rewards:</span>
                        <span class="stat-value">{dungeon['rewards']}</span>
                    </div>
                </div>
                
                <button class="dungeon-btn {button_class}" {button_action}>{button_text}</button>
            </div>
        </div>
        '''
    
    return cards_html

def generate_boss_history():
    """Generate boss fight history"""
    return '''
    <div class="dungeon-card">
        <div class="dungeon-content">
            <div class="dungeon-icon">👑</div>
            <div class="dungeon-name">Shadow King</div>
            <div class="dungeon-description">Defeated last week by alliance of 50+ players.</div>
            <div class="dungeon-stats">
                <div class="stat-row">
                    <span class="stat-label">Participants:</span>
                    <span class="stat-value">67 players</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Duration:</span>
                    <span class="stat-value">4 hours 23 minutes</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Status:</span>
                    <span class="stat-value">DEFEATED</span>
                </div>
            </div>
            <button class="dungeon-btn btn-locked">COMPLETED</button>
        </div>
    </div>
    '''

def generate_raid_cards(character):
    """Generate raid cards"""
    return '''
    <div class="dungeon-card">
        <div class="dungeon-content">
            <div class="dungeon-icon">⚔️</div>
            <div class="dungeon-name">Crew vs Crew Battle</div>
            <div class="dungeon-description">Epic battles between crews for territory and rewards.</div>
            <div class="dungeon-stats">
                <div class="stat-row">
                    <span class="stat-label">Crew Size:</span>
                    <span class="stat-value">5-20 members</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Duration:</span>
                    <span class="stat-value">1-2 hours</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Rewards:</span>
                    <span class="stat-value">Crew Vault Items</span>
                </div>
            </div>
            <button class="dungeon-btn btn-enter" onclick="joinRaid('crew_battle')">JOIN RAID</button>
        </div>
    </div>
    '''

async def start_challenge(request: web_request.Request):
    """Start a challenge"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        return web.Response(text="Character not found", status=400)
    
    challenge_id = request.match_info['challenge_id']
    
    # Here you would implement challenge start logic
    # For now, just return success
    return web.Response(text="Challenge started")

async def claim_reward(request: web_request.Request):
    """Claim challenge reward"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        return web.Response(text="Character not found", status=400)
    
    challenge_id = request.match_info['challenge_id']
    
    # Here you would implement reward claiming logic
    # For now, just return success
    return web.Response(text="Reward claimed")