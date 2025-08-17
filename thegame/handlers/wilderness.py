from aiohttp import web, web_request
import random
import json
from datetime import datetime

from database import get_db
from handlers.auth import require_login
from handlers.character import get_current_character

async def wilderness_main(request: web_request.Request):
    """Main wilderness exploration interface"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    # Check if character has enough energy for wilderness
    wilderness_energy = character.rage_current
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Wilderness - Outwar</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: Arial, sans-serif; background: #1a1a1a; color: #ffffff; }}
            
            /* Wilderness Background */
            .wilderness-bg {{ 
                background: linear-gradient(135deg, #0a2a0a 0%, #1a4a1a 50%, #0a2a0a 100%);
                min-height: 100vh;
                background-image: 
                    radial-gradient(circle at 20% 50%, rgba(34, 139, 34, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 80% 30%, rgba(0, 100, 0, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 40% 80%, rgba(124, 252, 0, 0.05) 0%, transparent 50%);
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
            
            /* Wilderness Header */
            .wilderness-header {{ background: rgba(45, 45, 45, 0.9); border: 1px solid #228b22; border-radius: 8px; padding: 20px; margin-bottom: 20px; text-align: center; }}
            .wilderness-title {{ color: #32cd32; font-size: 32px; font-weight: bold; margin-bottom: 10px; }}
            .wilderness-subtitle {{ color: #90ee90; font-size: 16px; margin-bottom: 15px; }}
            .energy-bar {{ background: #333; border-radius: 10px; padding: 5px; margin: 15px 0; }}
            .energy-fill {{ height: 20px; background: linear-gradient(90deg, #ff4444, #ffff00, #00ff00); border-radius: 5px; transition: width 0.3s; }}
            .energy-text {{ text-align: center; margin-top: 5px; color: #90ee90; }}
            
            /* Exploration Grid */
            .exploration-container {{ display: grid; grid-template-columns: 2fr 1fr; gap: 30px; }}
            
            /* Main Exploration Area */
            .exploration-area {{ background: rgba(45, 45, 45, 0.9); border: 1px solid #228b22; border-radius: 12px; padding: 25px; }}
            .area-title {{ color: #32cd32; font-size: 20px; font-weight: bold; margin-bottom: 20px; text-align: center; }}
            
            /* Wilderness Map */
            .wilderness-map {{ 
                background: #1a1a1a;
                border: 2px solid #228b22;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                min-height: 300px;
                position: relative;
            }}
            .map-grid {{ 
                display: grid;
                grid-template-columns: repeat(5, 1fr);
                gap: 5px;
                height: 300px;
            }}
            .map-tile {{ 
                background: #2d2d2d;
                border: 1px solid #444;
                border-radius: 3px;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s;
                font-size: 24px;
            }}
            .map-tile:hover {{ background: #3d3d3d; }}
            .map-tile.current {{ background: #32cd32; color: #000; }}
            .map-tile.explored {{ background: #228b22; }}
            .map-tile.monster {{ background: #ff4444; }}
            .map-tile.treasure {{ background: #ffd700; }}
            .map-tile.boss {{ background: #8b0000; border: 2px solid #ff0000; }}
            
            /* Action Buttons */
            .action-buttons {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }}
            .action-btn {{ 
                padding: 15px;
                font-size: 16px;
                font-weight: bold;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s;
            }}
            .btn-explore {{ background: linear-gradient(45deg, #228b22, #32cd32); color: white; }}
            .btn-explore:hover {{ background: linear-gradient(45deg, #32cd32, #7fff00); }}
            .btn-explore:disabled {{ background: #666; cursor: not-allowed; }}
            .btn-rest {{ background: linear-gradient(45deg, #4169e1, #87ceeb); color: white; }}
            .btn-rest:hover {{ background: linear-gradient(45deg, #87ceeb, #add8e6); }}
            .btn-hunt {{ background: linear-gradient(45deg, #ff6600, #ff8800); color: white; }}
            .btn-hunt:hover {{ background: linear-gradient(45deg, #ff8800, #ffaa00); }}
            .btn-return {{ background: linear-gradient(45deg, #666, #888); color: white; }}
            .btn-return:hover {{ background: linear-gradient(45deg, #888, #aaa); }}
            
            /* Side Panel */
            .side-panel {{ background: rgba(45, 45, 45, 0.9); border: 1px solid #228b22; border-radius: 12px; padding: 20px; }}
            
            /* Statistics Panel */
            .stats-panel {{ margin-bottom: 25px; }}
            .panel-title {{ color: #32cd32; font-size: 16px; font-weight: bold; margin-bottom: 15px; border-bottom: 1px solid #228b22; padding-bottom: 5px; }}
            .stat-row {{ display: flex; justify-content: space-between; margin: 8px 0; font-size: 13px; }}
            .stat-label {{ color: #90ee90; }}
            .stat-value {{ color: #fff; font-weight: bold; }}
            
            /* Recent Discoveries */
            .discoveries-panel {{ margin-bottom: 25px; }}
            .discovery-item {{ 
                background: #333;
                border-left: 3px solid #32cd32;
                padding: 10px;
                margin: 8px 0;
                border-radius: 0 5px 5px 0;
                font-size: 12px;
            }}
            .discovery-time {{ color: #90ee90; font-size: 10px; }}
            .discovery-reward {{ color: #ffd700; }}
            
            /* Inventory Preview */
            .inventory-preview {{ }}
            .inventory-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 5px; }}
            .inventory-slot {{ 
                width: 40px;
                height: 40px;
                background: #333;
                border: 1px solid #555;
                border-radius: 3px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 20px;
            }}
            .inventory-slot.filled {{ border-color: #32cd32; }}
            
            /* Combat Modal */
            .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; }}
            .modal-content {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: #2d2d2d; border: 2px solid #32cd32; border-radius: 15px; padding: 30px; min-width: 500px; text-align: center; }}
            .modal-title {{ font-size: 24px; font-weight: bold; margin-bottom: 20px; color: #32cd32; }}
            .enemy-portrait {{ width: 100px; height: 100px; background: #ff4444; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 48px; margin: 20px auto; }}
            .combat-actions {{ display: flex; gap: 15px; margin-top: 20px; }}
            .combat-btn {{ flex: 1; padding: 12px; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; }}
            .btn-attack {{ background: #ff4444; color: white; }}
            .btn-flee {{ background: #666; color: white; }}
            
            /* Loot Modal */
            .loot-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin: 20px 0; }}
            .loot-item {{ 
                background: #333;
                border: 2px solid #ffd700;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
            }}
            .loot-icon {{ font-size: 32px; margin-bottom: 10px; }}
            .loot-name {{ color: #ffd700; font-weight: bold; }}
            .loot-description {{ color: #ccc; font-size: 12px; }}
            
            /* Animations */
            @keyframes explore {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.1); }} 100% {{ transform: scale(1); }} }}
            .exploring {{ animation: explore 2s ease-in-out infinite; }}
            
            @keyframes glow {{ 0%, 100% {{ box-shadow: 0 0 20px rgba(50, 205, 50, 0.5); }} 50% {{ box-shadow: 0 0 40px rgba(50, 205, 50, 0.8); }} }}
            .glowing {{ animation: glow 2s ease-in-out infinite; }}
        </style>
    </head>
    <body class="wilderness-bg">
        <!-- Top Navigation -->
        <div class="top-nav">
            <div class="nav-tab" onclick="window.location.href='/game'">Explore World</div>
            <div class="nav-tab" onclick="window.location.href='/challenges'">Dungeons</div>
            <div class="nav-tab" onclick="window.location.href='/challenges'">Challenges</div>
            <div class="nav-tab active">Wilderness</div>
            <div class="nav-tab" onclick="window.location.href='/marketplace'">Marketplace</div>
            <div class="nav-tab" onclick="window.location.href='/rankings'">Rankings</div>
            <div class="nav-tab" onclick="window.location.href='/casino'">Casino</div>
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
            <!-- Wilderness Header -->
            <div class="wilderness-header">
                <div class="wilderness-title">🌲 THE WILDERNESS 🌲</div>
                <div class="wilderness-subtitle">Explore uncharted territories • Hunt monsters • Discover treasures</div>
                <div class="energy-bar">
                    <div class="energy-fill" style="width: {(wilderness_energy / 100) * 100}%;"></div>
                </div>
                <div class="energy-text">Wilderness Energy: {wilderness_energy}/100</div>
            </div>
            
            <!-- Exploration Container -->
            <div class="exploration-container">
                <!-- Main Exploration Area -->
                <div class="exploration-area">
                    <div class="area-title">Wilderness Map - Level {character.wilderness_level} Zone</div>
                    
                    <!-- Wilderness Map -->
                    <div class="wilderness-map">
                        <div class="map-grid" id="wildernessMap">
                            {generate_wilderness_map(character)}
                        </div>
                    </div>
                    
                    <!-- Action Buttons -->
                    <div class="action-buttons">
                        <button class="action-btn btn-explore" onclick="exploreWilderness()" 
                                {"disabled" if wilderness_energy < 10 else ""}>
                            🔍 EXPLORE (10 Energy)
                        </button>
                        <button class="action-btn btn-hunt" onclick="huntMonsters()"
                                {"disabled" if wilderness_energy < 20 else ""}>
                            ⚔️ HUNT MONSTERS (20 Energy)
                        </button>
                        <button class="action-btn btn-rest" onclick="restInWilderness()">
                            😴 REST (+20 Energy)
                        </button>
                        <button class="action-btn btn-return" onclick="returnToTown()">
                            🏠 RETURN TO TOWN
                        </button>
                    </div>
                    
                    <div style="text-align: center; color: #90ee90; font-size: 12px; margin-top: 15px;">
                        Current Zone: Wilderness Level {character.wilderness_level}<br>
                        Monsters: Level {character.wilderness_level}-{character.wilderness_level + 5}<br>
                        Difficulty: {"Beginner" if character.wilderness_level < 10 else "Intermediate" if character.wilderness_level < 25 else "Advanced"}
                    </div>
                </div>
                
                <!-- Side Panel -->
                <div class="side-panel">
                    <!-- Statistics -->
                    <div class="stats-panel">
                        <div class="panel-title">Wilderness Statistics</div>
                        <div class="stat-row">
                            <span class="stat-label">Wilderness Level:</span>
                            <span class="stat-value">{character.wilderness_level}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Monsters Defeated:</span>
                            <span class="stat-value">{character.wilderness_level * 25}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Areas Explored:</span>
                            <span class="stat-value">{character.wilderness_level * 10}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Treasures Found:</span>
                            <span class="stat-value">{character.wilderness_level * 5}</span>
                        </div>
                        <div class="stat-row">
                            <span class="stat-label">Current Energy:</span>
                            <span class="stat-value">{wilderness_energy}/100</span>
                        </div>
                    </div>
                    
                    <!-- Recent Discoveries -->
                    <div class="discoveries-panel">
                        <div class="panel-title">Recent Discoveries</div>
                        {generate_recent_discoveries(character)}
                    </div>
                    
                    <!-- Wilderness Inventory -->
                    <div class="inventory-preview">
                        <div class="panel-title">Wilderness Inventory</div>
                        <div class="inventory-grid">
                            <div class="inventory-slot filled">🏹</div>
                            <div class="inventory-slot filled">🛡️</div>
                            <div class="inventory-slot filled">💎</div>
                            <div class="inventory-slot filled">🧪</div>
                            <div class="inventory-slot"></div>
                            <div class="inventory-slot"></div>
                            <div class="inventory-slot"></div>
                            <div class="inventory-slot"></div>
                        </div>
                        <div style="text-align: center; font-size: 11px; color: #90ee90; margin-top: 10px;">
                            8/20 Slots Used
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Combat Modal -->
        <div class="modal" id="combatModal">
            <div class="modal-content">
                <div class="modal-title">Wild Encounter!</div>
                <div class="enemy-portrait" id="enemyPortrait">🐺</div>
                <div id="enemyName">Dire Wolf</div>
                <div id="enemyLevel">Level 15</div>
                <div style="margin: 20px 0; color: #ccc;">
                    A fierce predator blocks your path!
                </div>
                <div class="combat-actions">
                    <button class="combat-btn btn-attack" onclick="attackMonster()">⚔️ ATTACK</button>
                    <button class="combat-btn btn-flee" onclick="fleeFromMonster()">🏃 FLEE</button>
                </div>
            </div>
        </div>
        
        <!-- Loot Modal -->
        <div class="modal" id="lootModal">
            <div class="modal-content">
                <div class="modal-title">Treasure Found!</div>
                <div class="loot-grid">
                    <div class="loot-item">
                        <div class="loot-icon">💰</div>
                        <div class="loot-name">2,500 Gold</div>
                        <div class="loot-description">Shiny coins</div>
                    </div>
                    <div class="loot-item">
                        <div class="loot-icon">🏹</div>
                        <div class="loot-name">Forest Bow</div>
                        <div class="loot-description">+45 Attack</div>
                    </div>
                    <div class="loot-item">
                        <div class="loot-icon">💎</div>
                        <div class="loot-name">Nature Gem</div>
                        <div class="loot-description">Rare material</div>
                    </div>
                </div>
                <button class="combat-btn btn-attack" style="width: 100%; margin-top: 20px;" onclick="collectLoot()">
                    COLLECT ALL
                </button>
            </div>
        </div>
        
        <script>
        let wildernessEnergy = {wilderness_energy};
        let currentPosition = {{x: 2, y: 2}};
        
        function exploreWilderness() {{
            if (wildernessEnergy < 10) {{
                alert('Not enough energy to explore!');
                return;
            }}
            
            wildernessEnergy -= 10;
            updateEnergyBar();
            
            // Random exploration outcome
            const outcomes = ['monster', 'treasure', 'empty', 'secret'];
            const outcome = outcomes[Math.floor(Math.random() * outcomes.length)];
            
            setTimeout(() => {{
                if (outcome === 'monster') {{
                    showCombatModal();
                }} else if (outcome === 'treasure') {{
                    showLootModal();
                }} else if (outcome === 'secret') {{
                    alert('You discovered a secret area! +500 EXP');
                    updateCharacterExp(500);
                }} else {{
                    alert('You explore the area but find nothing of interest.');
                }}
            }}, 2000);
            
            // Animate exploration
            document.querySelector('.btn-explore').classList.add('exploring');
            setTimeout(() => {{
                document.querySelector('.btn-explore').classList.remove('exploring');
            }}, 2000);
        }}
        
        function huntMonsters() {{
            if (wildernessEnergy < 20) {{
                alert('Not enough energy to hunt!');
                return;
            }}
            
            wildernessEnergy -= 20;
            updateEnergyBar();
            showCombatModal();
        }}
        
        function restInWilderness() {{
            wildernessEnergy = Math.min(100, wildernessEnergy + 20);
            updateEnergyBar();
            alert('You rest and recover 20 energy.');
        }}
        
        function returnToTown() {{
            if (confirm('Return to town? You will lose any temporary wilderness bonuses.')) {{
                window.location.href = '/game';
            }}
        }}
        
        function updateEnergyBar() {{
            const percentage = (wildernessEnergy / 100) * 100;
            document.querySelector('.energy-fill').style.width = percentage + '%';
            document.querySelector('.energy-text').textContent = `Wilderness Energy: ${{wildernessEnergy}}/100`;
            
            // Update button states
            document.querySelector('.btn-explore').disabled = wildernessEnergy < 10;
            document.querySelector('.btn-hunt').disabled = wildernessEnergy < 20;
        }}
        
        function showCombatModal() {{
            const monsters = [
                {{name: 'Dire Wolf', emoji: '🐺', level: 15}},
                {{name: 'Forest Bear', emoji: '🐻', level: 18}},
                {{name: 'Wild Boar', emoji: '🐗', level: 12}},
                {{name: 'Mountain Cat', emoji: '🐱', level: 14}},
                {{name: 'Forest Troll', emoji: '👹', level: 20}}
            ];
            
            const monster = monsters[Math.floor(Math.random() * monsters.length)];
            
            document.getElementById('enemyPortrait').textContent = monster.emoji;
            document.getElementById('enemyName').textContent = monster.name;
            document.getElementById('enemyLevel').textContent = `Level ${{monster.level}}`;
            document.getElementById('combatModal').style.display = 'block';
        }}
        
        function showLootModal() {{
            document.getElementById('lootModal').style.display = 'block';
        }}
        
        function attackMonster() {{
            // Simulate combat
            const playerWins = Math.random() > 0.3; // 70% chance to win
            
            if (playerWins) {{
                alert('Victory! You defeated the monster and gained experience!');
                updateCharacterExp(1000);
                // 50% chance for loot
                if (Math.random() > 0.5) {{
                    document.getElementById('combatModal').style.display = 'none';
                    showLootModal();
                }} else {{
                    document.getElementById('combatModal').style.display = 'none';
                }}
            }} else {{
                alert('Defeat! The monster was too strong. You lose some energy.');
                wildernessEnergy = Math.max(0, wildernessEnergy - 10);
                updateEnergyBar();
                document.getElementById('combatModal').style.display = 'none';
            }}
        }}
        
        function fleeFromMonster() {{
            alert('You successfully flee from the monster!');
            wildernessEnergy = Math.max(0, wildernessEnergy - 5);
            updateEnergyBar();
            document.getElementById('combatModal').style.display = 'none';
        }}
        
        function collectLoot() {{
            alert('Loot collected! Check your inventory for new items.');
            document.getElementById('lootModal').style.display = 'none';
        }}
        
        function updateCharacterExp(exp) {{
            // This would normally update via server
            // For demo purposes, just show the gain
            console.log(`Gained ${{exp}} experience!`);
        }}
        
        // Close modals when clicking outside
        window.onclick = function(event) {{
            const combatModal = document.getElementById('combatModal');
            const lootModal = document.getElementById('lootModal');
            if (event.target === combatModal) {{
                combatModal.style.display = 'none';
            }}
            if (event.target === lootModal) {{
                lootModal.style.display = 'none';
            }}
        }}
        
        // Generate random map tiles
        function generateRandomMap() {{
            const tiles = document.querySelectorAll('.map-tile');
            tiles.forEach((tile, index) => {{
                if (index === 12) {{ // Center tile (current position)
                    tile.classList.add('current');
                    tile.textContent = '👤';
                }} else {{
                    const rand = Math.random();
                    if (rand < 0.1) {{
                        tile.classList.add('monster');
                        tile.textContent = '👹';
                    }} else if (rand < 0.15) {{
                        tile.classList.add('treasure');
                        tile.textContent = '💎';
                    }} else if (rand < 0.18) {{
                        tile.classList.add('boss');
                        tile.textContent = '🐲';
                    }} else if (rand < 0.4) {{
                        tile.classList.add('explored');
                        tile.textContent = '🌲';
                    }} else {{
                        tile.textContent = '🌲';
                    }}
                }}
            }});
        }}
        
        // Initialize map on load
        setTimeout(generateRandomMap, 100);
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

def generate_wilderness_map(character):
    """Generate wilderness map grid"""
    map_html = ""
    for i in range(25):  # 5x5 grid
        if i == 12:  # Center position
            map_html += '<div class="map-tile current" onclick="exploreTile(12)">👤</div>'
        else:
            # Random terrain generation
            rand = random.random()
            if rand < 0.1:
                map_html += '<div class="map-tile monster" onclick="exploreTile({})">👹</div>'.format(i)
            elif rand < 0.15:
                map_html += '<div class="map-tile treasure" onclick="exploreTile({})">💎</div>'.format(i)
            elif rand < 0.18:
                map_html += '<div class="map-tile boss" onclick="exploreTile({})">🐲</div>'.format(i)
            elif rand < 0.4:
                map_html += '<div class="map-tile explored" onclick="exploreTile({})">🌲</div>'.format(i)
            else:
                map_html += '<div class="map-tile" onclick="exploreTile({})">🌲</div>'.format(i)
    
    return map_html

def generate_recent_discoveries(character):
    """Generate recent discoveries list"""
    discoveries = [
        {"time": "5 min ago", "text": "Found rare herbs", "reward": "+250 Gold"},
        {"time": "12 min ago", "text": "Defeated Forest Wolf", "reward": "+800 EXP"},
        {"time": "18 min ago", "text": "Discovered hidden cave", "reward": "+1 Wilderness Level"},
        {"time": "25 min ago", "text": "Found mysterious crystal", "reward": "Magic Gem"},
    ]
    
    discoveries_html = ""
    for discovery in discoveries:
        discoveries_html += f'''
        <div class="discovery-item">
            <div>{discovery['text']}</div>
            <div class="discovery-reward">{discovery['reward']}</div>
            <div class="discovery-time">{discovery['time']}</div>
        </div>
        '''
    
    return discoveries_html

async def explore_wilderness(request: web_request.Request):
    """Handle wilderness exploration"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        return web.Response(text="Character not found", status=400)
    
    # Implement wilderness exploration logic here
    return web.Response(text="Exploration complete")

async def wilderness_combat(request: web_request.Request):
    """Handle wilderness combat"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        return web.Response(text="Character not found", status=400)
    
    # Implement wilderness combat logic here
    return web.Response(text="Combat complete")