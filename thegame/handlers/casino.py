from aiohttp import web, web_request
import random
import json
from datetime import datetime

from database import get_db
from handlers.auth import require_login
from handlers.character import get_current_character

async def casino_main(request: web_request.Request):
    """Main casino interface - Outwar style"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Underground Casino - Outwar</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: Arial, sans-serif; background: #0a0a0a; color: #ffffff; }}
            
            /* Casino Background */
            .casino-bg {{ 
                background: linear-gradient(135deg, #1a0033 0%, #330066 50%, #1a0033 100%);
                min-height: 100vh;
                background-image: 
                    radial-gradient(circle at 20% 50%, rgba(255, 215, 0, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 80% 30%, rgba(255, 0, 128, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 40% 80%, rgba(0, 255, 255, 0.1) 0%, transparent 50%);
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
            
            /* Casino Header */
            .casino-header {{ text-align: center; padding: 40px 20px; }}
            .casino-title {{ font-size: 48px; font-weight: bold; background: linear-gradient(45deg, #ffd700, #ff8c00, #ff0080); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 2px 2px 4px rgba(0,0,0,0.8); margin-bottom: 10px; }}
            .casino-subtitle {{ color: #ffd700; font-size: 18px; text-shadow: 1px 1px 2px rgba(0,0,0,0.8); }}
            .player-balance {{ margin-top: 20px; font-size: 24px; }}
            .balance-amount {{ color: #00ff00; font-weight: bold; }}
            
            /* Games Grid */
            .games-container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            .games-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; }}
            
            /* Game Cards */
            .game-card {{ 
                background: linear-gradient(145deg, #2d2d2d, #1a1a1a);
                border: 2px solid #444;
                border-radius: 15px;
                padding: 25px;
                text-align: center;
                transition: all 0.3s ease;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            }}
            .game-card:hover {{ 
                border-color: #ffd700;
                transform: translateY(-5px);
                box-shadow: 0 12px 48px rgba(255, 215, 0, 0.2);
            }}
            
            .game-icon {{ font-size: 64px; margin-bottom: 15px; }}
            .game-title {{ font-size: 24px; font-weight: bold; color: #ffd700; margin-bottom: 10px; }}
            .game-description {{ color: #ccc; margin-bottom: 20px; line-height: 1.4; }}
            .game-stats {{ background: #333; border-radius: 8px; padding: 15px; margin-bottom: 20px; }}
            .stat-row {{ display: flex; justify-content: space-between; margin: 5px 0; }}
            .stat-label {{ color: #ccc; }}
            .stat-value {{ color: #ffd700; font-weight: bold; }}
            
            .play-btn {{ 
                width: 100%;
                padding: 15px;
                font-size: 18px;
                font-weight: bold;
                background: linear-gradient(45deg, #ff6600, #ff8800);
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s ease;
            }}
            .play-btn:hover {{ 
                background: linear-gradient(45deg, #ff8800, #ffaa00);
                transform: scale(1.05);
            }}
            
            /* Slot Machine Specific */
            .slot-machine {{ background: linear-gradient(145deg, #4a4a4a, #2a2a2a); }}
            .slot-reels {{ display: flex; justify-content: center; gap: 10px; margin: 20px 0; }}
            .slot-reel {{ 
                width: 60px;
                height: 60px;
                background: #000;
                border: 3px solid #ffd700;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
            }}
            .slot-controls {{ margin: 20px 0; }}
            .bet-input {{ 
                width: 100px;
                padding: 8px;
                background: #333;
                border: 1px solid #666;
                border-radius: 5px;
                color: white;
                text-align: center;
                margin: 0 10px;
            }}
            
            /* Dice Game */
            .dice-game {{ background: linear-gradient(145deg, #0066cc, #004499); }}
            .dice-container {{ display: flex; justify-content: center; gap: 20px; margin: 20px 0; }}
            .dice {{ 
                width: 50px;
                height: 50px;
                background: white;
                color: black;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                font-weight: bold;
            }}
            
            /* Roulette */
            .roulette-game {{ background: linear-gradient(145deg, #cc0000, #990000); }}
            .roulette-wheel {{ 
                width: 120px;
                height: 120px;
                border: 5px solid #ffd700;
                border-radius: 50%;
                background: conic-gradient(#ff0000 0deg, #000000 18deg, #ff0000 36deg, #000000 54deg, #ff0000 72deg, #000000 90deg, #ff0000 108deg, #000000 126deg, #ff0000 144deg, #000000 162deg, #ff0000 180deg, #000000 198deg, #ff0000 216deg, #000000 234deg, #ff0000 252deg, #000000 270deg, #ff0000 288deg, #000000 306deg, #ff0000 324deg, #000000 342deg);
                margin: 20px auto;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 18px;
            }}
            
            /* Poker */
            .poker-game {{ background: linear-gradient(145deg, #006600, #004400); }}
            .poker-hand {{ display: flex; justify-content: center; gap: 5px; margin: 20px 0; }}
            .playing-card {{ 
                width: 40px;
                height: 56px;
                background: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 12px;
                color: black;
            }}
            
            /* Lottery */
            .lottery-game {{ background: linear-gradient(145deg, #8800cc, #660099); }}
            .lottery-numbers {{ display: flex; justify-content: center; gap: 10px; margin: 20px 0; }}
            .lottery-ball {{ 
                width: 40px;
                height: 40px;
                background: #ffd700;
                color: #000;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
            }}
            
            /* Results Modal */
            .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; }}
            .modal-content {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); background: #2d2d2d; border: 2px solid #ffd700; border-radius: 15px; padding: 30px; text-align: center; min-width: 400px; }}
            .modal-title {{ font-size: 24px; font-weight: bold; margin-bottom: 20px; }}
            .win {{ color: #00ff00; }}
            .lose {{ color: #ff4444; }}
            .modal-result {{ font-size: 20px; margin: 20px 0; }}
            .modal-close {{ padding: 10px 20px; background: #ff6600; color: white; border: none; border-radius: 5px; cursor: pointer; margin-top: 20px; }}
            
            /* Animations */
            @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
            .spinning {{ animation: spin 2s linear infinite; }}
            
            @keyframes glow {{ 0%, 100% {{ box-shadow: 0 0 20px rgba(255, 215, 0, 0.5); }} 50% {{ box-shadow: 0 0 40px rgba(255, 215, 0, 0.8); }} }}
            .glowing {{ animation: glow 2s ease-in-out infinite; }}
        </style>
    </head>
    <body class="casino-bg">
        <!-- Top Navigation -->
        <div class="top-nav">
            <div class="nav-tab" onclick="window.location.href='/game'">Explore World</div>
            <div class="nav-tab" onclick="window.location.href='/challenges'">Challenges</div>
            <div class="nav-tab" onclick="window.location.href='/marketplace'">Marketplace</div>
            <div class="nav-tab" onclick="window.location.href='/rankings'">Rankings</div>
            <div class="nav-tab active">Casino</div>
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
        
        <!-- Casino Header -->
        <div class="casino-header">
            <div class="casino-title">🎰 UNDERGROUND CASINO 🎰</div>
            <div class="casino-subtitle">Try Your Luck • Win Big • Lose Everything</div>
            <div class="player-balance">
                Current Balance: <span class="balance-amount" id="playerGold">{character.gold:,}g</span>
            </div>
        </div>
        
        <!-- Games Container -->
        <div class="games-container">
            <div class="games-grid">
                <!-- Slot Machine -->
                <div class="game-card slot-machine">
                    <div class="game-icon">🎰</div>
                    <div class="game-title">SLOT MACHINE</div>
                    <div class="game-description">Classic 3-reel slots with massive jackpots!</div>
                    
                    <div class="slot-reels">
                        <div class="slot-reel" id="reel1">🍒</div>
                        <div class="slot-reel" id="reel2">🍒</div>
                        <div class="slot-reel" id="reel3">🍒</div>
                    </div>
                    
                    <div class="game-stats">
                        <div class="stat-row"><span class="stat-label">Min Bet:</span><span class="stat-value">100g</span></div>
                        <div class="stat-row"><span class="stat-label">Max Bet:</span><span class="stat-value">10,000g</span></div>
                        <div class="stat-row"><span class="stat-label">Jackpot:</span><span class="stat-value">1,000,000g</span></div>
                    </div>
                    
                    <div class="slot-controls">
                        Bet: <input type="number" class="bet-input" id="slotBet" value="1000" min="100" max="10000">g
                    </div>
                    
                    <button class="play-btn" onclick="playSlots()">SPIN REELS</button>
                </div>
                
                <!-- Dice Rolling -->
                <div class="game-card dice-game">
                    <div class="game-icon">🎲</div>
                    <div class="game-title">DICE ROLLING</div>
                    <div class="game-description">Roll two dice and bet on the outcome!</div>
                    
                    <div class="dice-container">
                        <div class="dice" id="dice1">⚀</div>
                        <div class="dice" id="dice2">⚀</div>
                    </div>
                    
                    <div class="game-stats">
                        <div class="stat-row"><span class="stat-label">Double Pays:</span><span class="stat-value">6x</span></div>
                        <div class="stat-row"><span class="stat-label">High (8-12):</span><span class="stat-value">2x</span></div>
                        <div class="stat-row"><span class="stat-label">Low (2-6):</span><span class="stat-value">2x</span></div>
                    </div>
                    
                    <div class="slot-controls">
                        Bet: <input type="number" class="bet-input" id="diceBet" value="500" min="50" max="5000">g
                        <select id="diceType" style="margin-left: 10px; padding: 5px; background: #333; color: white; border: 1px solid #666;">
                            <option value="high">High (8-12)</option>
                            <option value="low">Low (2-6)</option>
                            <option value="double">Any Double</option>
                        </select>
                    </div>
                    
                    <button class="play-btn" onclick="playDice()">ROLL DICE</button>
                </div>
                
                <!-- Roulette -->
                <div class="game-card roulette-game">
                    <div class="game-icon">🎡</div>
                    <div class="game-title">ROULETTE</div>
                    <div class="game-description">Spin the wheel and bet on your lucky number!</div>
                    
                    <div class="roulette-wheel" id="rouletteWheel">00</div>
                    
                    <div class="game-stats">
                        <div class="stat-row"><span class="stat-label">Single Number:</span><span class="stat-value">35x</span></div>
                        <div class="stat-row"><span class="stat-label">Red/Black:</span><span class="stat-value">2x</span></div>
                        <div class="stat-row"><span class="stat-label">Odd/Even:</span><span class="stat-value">2x</span></div>
                    </div>
                    
                    <div class="slot-controls">
                        Bet: <input type="number" class="bet-input" id="rouletteBet" value="1000" min="100" max="10000">g
                        <select id="rouletteType" style="margin-left: 10px; padding: 5px; background: #333; color: white; border: 1px solid #666;">
                            <option value="red">Red</option>
                            <option value="black">Black</option>
                            <option value="odd">Odd</option>
                            <option value="even">Even</option>
                        </select>
                    </div>
                    
                    <button class="play-btn" onclick="playRoulette()">SPIN WHEEL</button>
                </div>
                
                <!-- Poker -->
                <div class="game-card poker-game">
                    <div class="game-icon">🃏</div>
                    <div class="game-title">POKER HAND</div>
                    <div class="game-description">Draw 5 cards and try to get the best hand!</div>
                    
                    <div class="poker-hand">
                        <div class="playing-card" id="card1">?</div>
                        <div class="playing-card" id="card2">?</div>
                        <div class="playing-card" id="card3">?</div>
                        <div class="playing-card" id="card4">?</div>
                        <div class="playing-card" id="card5">?</div>
                    </div>
                    
                    <div class="game-stats">
                        <div class="stat-row"><span class="stat-label">Royal Flush:</span><span class="stat-value">1000x</span></div>
                        <div class="stat-row"><span class="stat-label">Straight Flush:</span><span class="stat-value">50x</span></div>
                        <div class="stat-row"><span class="stat-label">Four of a Kind:</span><span class="stat-value">25x</span></div>
                    </div>
                    
                    <div class="slot-controls">
                        Bet: <input type="number" class="bet-input" id="pokerBet" value="2000" min="200" max="20000">g
                    </div>
                    
                    <button class="play-btn" onclick="playPoker()">DRAW HAND</button>
                </div>
                
                <!-- Lottery -->
                <div class="game-card lottery-game">
                    <div class="game-icon">🎟️</div>
                    <div class="game-title">DAILY LOTTERY</div>
                    <div class="game-description">Pick your lucky numbers for the daily draw!</div>
                    
                    <div class="lottery-numbers">
                        <div class="lottery-ball" id="lotto1">?</div>
                        <div class="lottery-ball" id="lotto2">?</div>
                        <div class="lottery-ball" id="lotto3">?</div>
                        <div class="lottery-ball" id="lotto4">?</div>
                        <div class="lottery-ball" id="lotto5">?</div>
                    </div>
                    
                    <div class="game-stats">
                        <div class="stat-row"><span class="stat-label">Ticket Price:</span><span class="stat-value">5,000g</span></div>
                        <div class="stat-row"><span class="stat-label">Current Jackpot:</span><span class="stat-value">10,000,000g</span></div>
                        <div class="stat-row"><span class="stat-label">Next Draw:</span><span class="stat-value">23:59</span></div>
                    </div>
                    
                    <button class="play-btn" onclick="playLottery()">BUY TICKET</button>
                </div>
                
                <!-- High-Low Card Game -->
                <div class="game-card" style="background: linear-gradient(145deg, #ff6600, #cc5500);">
                    <div class="game-icon">🎴</div>
                    <div class="game-title">HIGH-LOW</div>
                    <div class="game-description">Guess if the next card will be higher or lower!</div>
                    
                    <div style="margin: 20px 0;">
                        <div class="playing-card" id="currentCard" style="width: 80px; height: 112px; font-size: 24px;">A♠</div>
                    </div>
                    
                    <div class="game-stats">
                        <div class="stat-row"><span class="stat-label">Correct Guess:</span><span class="stat-value">2x</span></div>
                        <div class="stat-row"><span class="stat-label">Win Streak x5:</span><span class="stat-value">50x</span></div>
                        <div class="stat-row"><span class="stat-label">Current Streak:</span><span class="stat-value" id="streak">0</span></div>
                    </div>
                    
                    <div class="slot-controls">
                        Bet: <input type="number" class="bet-input" id="highLowBet" value="750" min="100" max="7500">g
                    </div>
                    
                    <div style="display: flex; gap: 10px; margin: 20px 0;">
                        <button class="play-btn" style="flex: 1;" onclick="playHighLow('higher')">HIGHER</button>
                        <button class="play-btn" style="flex: 1;" onclick="playHighLow('lower')">LOWER</button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Results Modal -->
        <div class="modal" id="resultModal">
            <div class="modal-content">
                <div class="modal-title" id="modalTitle">Game Result</div>
                <div class="modal-result" id="modalResult"></div>
                <div id="modalDetails"></div>
                <button class="modal-close" onclick="closeModal()">CLOSE</button>
            </div>
        </div>
        
        <script>
        let playerGold = {character.gold};
        let winStreak = 0;
        
        async function updateGold(amount) {{
            playerGold += amount;
            document.getElementById('playerGold').textContent = playerGold.toLocaleString() + 'g';
            
            // Update server-side gold
            try {{
                await fetch('/casino/update-gold', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{gold: playerGold}})
                }});
            }} catch (e) {{
                console.error('Failed to update gold on server');
            }}
        }}
        
        function showResult(title, result, details, isWin, amount) {{
            document.getElementById('modalTitle').textContent = title;
            document.getElementById('modalTitle').className = isWin ? 'modal-title win' : 'modal-title lose';
            document.getElementById('modalResult').textContent = result;
            document.getElementById('modalDetails').innerHTML = details;
            document.getElementById('resultModal').style.display = 'block';
            
            if (amount !== 0) {{
                updateGold(amount);
            }}
        }}
        
        function closeModal() {{
            document.getElementById('resultModal').style.display = 'none';
        }}
        
        // Slot Machine
        function playSlots() {{
            const bet = parseInt(document.getElementById('slotBet').value);
            if (bet > playerGold) {{
                alert('Not enough gold!');
                return;
            }}
            
            const symbols = ['🍒', '🍋', '🍊', '🍇', '⭐', '💎', '7️⃣'];
            const reels = [
                symbols[Math.floor(Math.random() * symbols.length)],
                symbols[Math.floor(Math.random() * symbols.length)],
                symbols[Math.floor(Math.random() * symbols.length)]
            ];
            
            // Animate reels
            const reelElements = ['reel1', 'reel2', 'reel3'];
            reelElements.forEach((reel, index) => {{
                const element = document.getElementById(reel);
                element.classList.add('spinning');
                setTimeout(() => {{
                    element.textContent = reels[index];
                    element.classList.remove('spinning');
                }}, 1000 + (index * 500));
            }});
            
            setTimeout(() => {{
                let winAmount = 0;
                let message = '';
                
                if (reels[0] === reels[1] && reels[1] === reels[2]) {{
                    // Three of a kind
                    if (reels[0] === '💎') winAmount = bet * 100;
                    else if (reels[0] === '7️⃣') winAmount = bet * 50;
                    else if (reels[0] === '⭐') winAmount = bet * 25;
                    else winAmount = bet * 10;
                    message = 'Three ' + reels[0] + '! You win ' + winAmount.toLocaleString() + 'g!';
                }} else if (reels[0] === reels[1] || reels[1] === reels[2] || reels[0] === reels[2]) {{
                    // Two of a kind
                    winAmount = bet * 2;
                    message = 'Two of a kind! You win ' + winAmount.toLocaleString() + 'g!';
                }} else {{
                    winAmount = -bet;
                    message = 'No match. You lose ' + bet.toLocaleString() + 'g.';
                }}
                
                showResult('Slot Machine', message, 'Reels: ' + reels.join(' ') + '<br>Bet: ' + bet.toLocaleString() + 'g', winAmount > 0, winAmount);
            }}, 2500);
        }}
        
        // Dice Game
        function playDice() {{
            const bet = parseInt(document.getElementById('diceBet').value);
            const betType = document.getElementById('diceType').value;
            
            if (bet > playerGold) {{
                alert('Not enough gold!');
                return;
            }}
            
            const dice1 = Math.floor(Math.random() * 6) + 1;
            const dice2 = Math.floor(Math.random() * 6) + 1;
            const total = dice1 + dice2;
            
            const diceSymbols = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅'];
            document.getElementById('dice1').textContent = diceSymbols[dice1 - 1];
            document.getElementById('dice2').textContent = diceSymbols[dice2 - 1];
            
            let winAmount = 0;
            let message = '';
            
            if (betType === 'high' && total >= 8) {{
                winAmount = bet * 2;
                message = 'High wins! Total: ' + total;
            }} else if (betType === 'low' && total <= 6) {{
                winAmount = bet * 2;
                message = 'Low wins! Total: ' + total;
            }} else if (betType === 'double' && dice1 === dice2) {{
                winAmount = bet * 6;
                message = 'Double ' + dice1 + 's! You win big!';
            }} else {{
                winAmount = -bet;
                message = 'You lose. Total: ' + total;
            }}
            
            showResult('Dice Roll', message, 'Dice: ' + dice1 + ' + ' + dice2 + ' = ' + total + '<br>Bet: ' + betType + ' for ' + bet.toLocaleString() + 'g', winAmount > 0, winAmount);
        }}
        
        // Roulette
        function playRoulette() {{
            const bet = parseInt(document.getElementById('rouletteBet').value);
            const betType = document.getElementById('rouletteType').value;
            
            if (bet > playerGold) {{
                alert('Not enough gold!');
                return;
            }}
            
            const number = Math.floor(Math.random() * 37); // 0-36
            const isRed = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36].includes(number);
            const isBlack = number > 0 && !isRed;
            const isOdd = number % 2 === 1;
            const isEven = number > 0 && number % 2 === 0;
            
            document.getElementById('rouletteWheel').textContent = number;
            document.getElementById('rouletteWheel').classList.add('spinning');
            
            setTimeout(() => {{
                document.getElementById('rouletteWheel').classList.remove('spinning');
                
                let winAmount = 0;
                let message = '';
                
                if ((betType === 'red' && isRed) || 
                    (betType === 'black' && isBlack) ||
                    (betType === 'odd' && isOdd) ||
                    (betType === 'even' && isEven)) {{
                    winAmount = bet * 2;
                    message = betType.toUpperCase() + ' wins!';
                }} else {{
                    winAmount = -bet;
                    message = betType.toUpperCase() + ' loses.';
                }}
                
                const color = isRed ? 'Red' : isBlack ? 'Black' : 'Green';
                showResult('Roulette', message, 'Number: ' + number + ' (' + color + ')<br>Bet: ' + betType + ' for ' + bet.toLocaleString() + 'g', winAmount > 0, winAmount);
            }}, 2000);
        }}
        
        // Poker
        function playPoker() {{
            const bet = parseInt(document.getElementById('pokerBet').value);
            
            if (bet > playerGold) {{
                alert('Not enough gold!');
                return;
            }}
            
            const suits = ['♠', '♥', '♦', '♣'];
            const ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'];
            
            const hand = [];
            for (let i = 0; i < 5; i++) {{
                const suit = suits[Math.floor(Math.random() * suits.length)];
                const rank = ranks[Math.floor(Math.random() * ranks.length)];
                hand.push({{rank, suit}});
                document.getElementById('card' + (i + 1)).textContent = rank + suit;
                document.getElementById('card' + (i + 1)).style.color = (suit === '♥' || suit === '♦') ? 'red' : 'black';
            }}
            
            // Simple hand evaluation (just checking for pairs)
            const rankCounts = {{}};
            hand.forEach(card => {{
                rankCounts[card.rank] = (rankCounts[card.rank] || 0) + 1;
            }});
            
            const counts = Object.values(rankCounts).sort((a, b) => b - a);
            let winAmount = 0;
            let handType = '';
            
            if (counts[0] === 4) {{
                winAmount = bet * 25;
                handType = 'Four of a Kind';
            }} else if (counts[0] === 3 && counts[1] === 2) {{
                winAmount = bet * 9;
                handType = 'Full House';
            }} else if (counts[0] === 3) {{
                winAmount = bet * 3;
                handType = 'Three of a Kind';
            }} else if (counts[0] === 2 && counts[1] === 2) {{
                winAmount = bet * 2;
                handType = 'Two Pair';
            }} else if (counts[0] === 2) {{
                winAmount = bet;
                handType = 'Pair';
            }} else {{
                winAmount = -bet;
                handType = 'High Card (No Win)';
            }}
            
            showResult('Poker Hand', handType, 'Hand: ' + hand.map(c => c.rank + c.suit).join(' ') + '<br>Bet: ' + bet.toLocaleString() + 'g', winAmount > 0, winAmount);
        }}
        
        // Lottery
        function playLottery() {{
            const ticketCost = 5000;
            
            if (ticketCost > playerGold) {{
                alert('Not enough gold for a lottery ticket!');
                return;
            }}
            
            const numbers = [];
            for (let i = 0; i < 5; i++) {{
                numbers.push(Math.floor(Math.random() * 50) + 1);
                document.getElementById('lotto' + (i + 1)).textContent = numbers[i];
            }}
            
            // Simple lottery win check
            const matches = numbers.filter(n => n <= 10).length; // Numbers 1-10 are "winning"
            let winAmount = -ticketCost;
            let message = 'No winning numbers.';
            
            if (matches >= 3) {{
                winAmount = ticketCost * Math.pow(10, matches - 2);
                message = matches + ' matching numbers!';
            }}
            
            showResult('Lottery Ticket', message, 'Numbers: ' + numbers.join(' ') + '<br>Ticket Cost: ' + ticketCost.toLocaleString() + 'g', winAmount > 0, winAmount);
        }}
        
        // High-Low
        function playHighLow(guess) {{
            const bet = parseInt(document.getElementById('highLowBet').value);
            
            if (bet > playerGold) {{
                alert('Not enough gold!');
                return;
            }}
            
            const suits = ['♠', '♥', '♦', '♣'];
            const ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'];
            const currentCard = document.getElementById('currentCard').textContent;
            const currentRank = currentCard.slice(0, -1);
            const currentValue = ranks.indexOf(currentRank);
            
            const newSuit = suits[Math.floor(Math.random() * suits.length)];
            const newRank = ranks[Math.floor(Math.random() * ranks.length)];
            const newValue = ranks.indexOf(newRank);
            const newCard = newRank + newSuit;
            
            document.getElementById('currentCard').textContent = newCard;
            document.getElementById('currentCard').style.color = (newSuit === '♥' || newSuit === '♦') ? 'red' : 'black';
            
            let winAmount = 0;
            let message = '';
            let correct = false;
            
            if ((guess === 'higher' && newValue > currentValue) || 
                (guess === 'lower' && newValue < currentValue)) {{
                correct = true;
                winStreak++;
                winAmount = bet * (1 + winStreak * 0.5);
                message = 'Correct! Win streak: ' + winStreak;
            }} else {{
                winStreak = 0;
                winAmount = -bet;
                message = 'Wrong! Streak reset.';
            }}
            
            document.getElementById('streak').textContent = winStreak;
            showResult('High-Low', message, 'Previous: ' + currentCard + '<br>New: ' + newCard + '<br>Guess: ' + guess, correct, winAmount);
        }}
        
        // Close modal when clicking outside
        window.onclick = function(event) {{
            const modal = document.getElementById('resultModal');
            if (event.target === modal) {{
                closeModal();
            }}
        }}
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def update_gold(request: web_request.Request):
    """Update player gold from casino games"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        return web.Response(text="Character not found", status=400)
    
    try:
        data = await request.json()
        new_gold = data.get('gold', 0)
        
        # Basic validation
        if new_gold < 0:
            new_gold = 0
        elif new_gold > 999999999:  # Max gold cap
            new_gold = 999999999
        
        database = await get_db()
        async with database.get_connection_context() as conn:
            await conn.execute('UPDATE characters SET gold = ? WHERE id = ?', (new_gold, character.id))
            await conn.commit()
        
        return web.Response(text="Gold updated")
    except Exception as e:
        return web.Response(text=f"Error: {e}", status=400)