from aiohttp import web, web_request
from typing import Dict, List, Optional

from database import get_db
from handlers.auth import require_login
from handlers.character import get_current_character

async def rankings_main(request: web_request.Request):
    """Main rankings interface - Outwar style"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    # Get ranking type from query params
    ranking_type = request.query.get('type', 'power')
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        # Get rankings based on type
        limit = 50  # Show top 50 players
        if ranking_type == 'power':
            rankings = await database.queries.get_power_rankings(conn, limit=limit)
        elif ranking_type == 'level':
            rankings = await database.queries.get_level_rankings(conn, limit=limit)
        elif ranking_type == 'gold':
            rankings = await database.queries.get_gold_rankings(conn, limit=limit)
        elif ranking_type == 'experience':
            rankings = await database.queries.get_experience_rankings(conn, limit=limit)
        elif ranking_type == 'wilderness':
            rankings = await database.queries.get_wilderness_rankings(conn, limit=limit)
        else:
            rankings = await database.queries.get_power_rankings(conn, limit=limit)
    
    # Find character's position
    char_position = None
    for i, rank in enumerate(rankings):
        if rank['id'] == character.id:
            char_position = i + 1
            break
    
    # Build rankings HTML
    rankings_html = build_rankings_html(rankings, character.id)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rankings - Outwar</title>
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
            .main-container {{ padding: 20px; max-width: 1200px; margin: 0 auto; }}
            
            /* Rankings Header */
            .rankings-header {{ background: #2d2d2d; border: 1px solid #555; border-radius: 8px; padding: 20px; margin-bottom: 20px; text-align: center; }}
            .rankings-title {{ color: #ffd700; font-size: 28px; font-weight: bold; margin-bottom: 15px; }}
            .rankings-subtitle {{ color: #ccc; margin-bottom: 20px; }}
            
            /* Ranking Tabs */
            .ranking-tabs {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }}
            .ranking-tab {{ padding: 10px 20px; background: #444; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 12px; }}
            .ranking-tab.active {{ background: #ffd700; color: #000; font-weight: bold; }}
            .ranking-tab:hover {{ background: #555; }}
            .ranking-tab.active:hover {{ background: #ffdd33; }}
            
            /* Player Position Banner */
            .player-position {{ background: linear-gradient(90deg, #4169e1, #1e3a8a); border: 1px solid #5578ff; border-radius: 8px; padding: 15px; margin-bottom: 20px; text-align: center; }}
            .position-text {{ font-size: 16px; font-weight: bold; }}
            .position-rank {{ color: #ffd700; font-size: 20px; }}
            
            /* Rankings Table */
            .rankings-container {{ background: #2d2d2d; border: 1px solid #555; border-radius: 8px; overflow: hidden; }}
            .rankings-table {{ width: 100%; border-collapse: collapse; }}
            .rankings-table th {{ background: #444; color: #ffd700; padding: 15px; text-align: left; font-weight: bold; border-bottom: 2px solid #666; }}
            .rankings-table td {{ padding: 12px 15px; border-bottom: 1px solid #444; }}
            .rankings-table tr:hover {{ background: #333; }}
            .rankings-table tr.own-character {{ background: #1a3d5c; }}
            .rankings-table tr.own-character:hover {{ background: #2a4d6c; }}
            
            /* Rank Styling */
            .rank-number {{ font-weight: bold; font-size: 16px; width: 60px; text-align: center; }}
            .rank-1 {{ color: #ffd700; }}
            .rank-2 {{ color: #c0c0c0; }}
            .rank-3 {{ color: #cd7f32; }}
            .rank-top10 {{ color: #ff6600; }}
            .rank-top100 {{ color: #00aa00; }}
            
            /* Character Info */
            .character-info {{ display: flex; align-items: center; gap: 10px; }}
            .character-avatar {{ width: 32px; height: 32px; background: linear-gradient(45deg, #666, #999); border-radius: 50%; display: flex; align-items: center; justify-content: center; }}
            .character-name {{ font-weight: bold; color: #88ccff; }}
            .character-class {{ color: #ccc; font-size: 11px; }}
            .character-faction {{ color: #ff8c00; font-size: 10px; }}
            
            /* Stats */
            .stat-value {{ font-weight: bold; }}
            .stat-large {{ font-size: 16px; }}
            .stat-power {{ color: #ff6600; }}
            .stat-level {{ color: #00aa00; }}
            .stat-gold {{ color: #ffd700; }}
            .stat-exp {{ color: #88ccff; }}
            
            /* Last Active */
            .last-active {{ color: #ccc; font-size: 11px; }}
            .active-recent {{ color: #00ff00; }}
            .active-offline {{ color: #ff4444; }}
            
            /* Footer */
            .rankings-footer {{ background: #333; padding: 15px; text-align: center; color: #ccc; font-size: 12px; }}
            
            /* Responsive */
            @media (max-width: 768px) {{
                .rankings-table {{ font-size: 12px; }}
                .rankings-table th, .rankings-table td {{ padding: 8px; }}
                .ranking-tabs {{ gap: 5px; }}
                .ranking-tab {{ padding: 8px 12px; font-size: 11px; }}
            }}
        </style>
    </head>
    <body>
        <!-- Top Navigation -->
        <div class="top-nav">
            <div class="nav-tab" onclick="window.location.href='/game'">Explore World</div>
            <div class="nav-tab" onclick="window.location.href='/challenges'">Challenges</div>
            <div class="nav-tab" onclick="window.location.href='/marketplace'">Marketplace</div>
            <div class="nav-tab active">Rankings</div>
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
            <!-- Rankings Header -->
            <div class="rankings-header">
                <div class="rankings-title">🏆 LEADERBOARDS</div>
                <div class="rankings-subtitle">See how you stack up against other players</div>
            </div>
            
            <!-- Ranking Tabs -->
            <div class="ranking-tabs">
                <button class="ranking-tab {'active' if ranking_type == 'power' else ''}" onclick="switchRanking('power')">💪 Total Power</button>
                <button class="ranking-tab {'active' if ranking_type == 'level' else ''}" onclick="switchRanking('level')">⭐ Level</button>
                <button class="ranking-tab {'active' if ranking_type == 'experience' else ''}" onclick="switchRanking('experience')">📈 Experience</button>
                <button class="ranking-tab {'active' if ranking_type == 'gold' else ''}" onclick="switchRanking('gold')">💰 Gold</button>
                <button class="ranking-tab {'active' if ranking_type == 'wilderness' else ''}" onclick="switchRanking('wilderness')">🌲 Wilderness</button>
                <button class="ranking-tab {'active' if ranking_type == 'pvp' else ''}" onclick="switchRanking('pvp')">⚔️ PvP Wins</button>
            </div>
            
            <!-- Player Position -->
            {f'<div class="player-position"><div class="position-text">Your Current Rank: <span class="position-rank">#{char_position}</span> of {len(rankings)}</div></div>' if char_position else ''}
            
            <!-- Rankings Table -->
            <div class="rankings-container">
                <table class="rankings-table">
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Character</th>
                            <th>Class</th>
                            <th>{get_ranking_column_header(ranking_type)}</th>
                            <th>Level</th>
                            <th>Last Active</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rankings_html}
                    </tbody>
                </table>
            </div>
            
            <!-- Footer -->
            <div class="rankings-footer">
                Rankings updated every 5 minutes • Only active players shown • Last updated: Now
            </div>
        </div>
        
        <script>
        function switchRanking(type) {{
            window.location.href = '/rankings?type=' + type;
        }}
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

def build_rankings_html(rankings, current_char_id):
    """Build HTML for rankings list"""
    if not rankings:
        return '<div class="no-data">No rankings data available</div>'
    
    html = ""
    for i, rank in enumerate(rankings):
        rank_num = i + 1
        is_current = rank['id'] == current_char_id
        row_class = 'current-player' if is_current else ''
        
        # Handle sqlite3.Row objects properly
        total_power = rank['total_power'] if 'total_power' in rank.keys() else 0
        
        html += f"""
        <tr class="{row_class}">
            <td class="rank">#{rank_num}</td>
            <td class="name">
                <a href="/character/{rank['id']}">{rank['name']}</a>
            </td>
            <td class="class">{rank['class_name']}</td>
            <td class="power">{total_power:,}</td>
            <td class="level">{rank['level']}</td>
            <td class="last-active">Online</td>
        </tr>
        """
    
    return html

def get_ranking_column_header(ranking_type):
    """Get the appropriate column header for ranking type"""
    headers = {
        'power': 'Total Power',
        'level': 'Level', 
        'experience': 'Experience',
        'gold': 'Gold',
        'wilderness': 'Wilderness Level'
    }
    return headers.get(ranking_type, 'Power')
