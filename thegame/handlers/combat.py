from aiohttp import web, web_request
import random
from datetime import datetime

from database import get_db
from handlers.auth import require_login
from handlers.character import get_current_character
from models.character import Character

async def attack_player(request: web_request.Request):
    """Attack another player"""
    await require_login(request)
    attacker = await get_current_character(request)
    
    if not attacker:
        raise web.HTTPFound('/characters')
    
    target_id = int(request.match_info['target_id'])
    
    if target_id == attacker.id:
        raise web.HTTPBadRequest(text="Cannot attack yourself")
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        # Get target character
        target_data = await database.queries.get_character_by_id(conn, character_id=target_id)
        if not target_data:
            raise web.HTTPNotFound(text="Target character not found")
        
        target = Character.from_db_row(target_data)
        
        # Check if target is alive
        if not target.is_alive():
            raise web.HTTPBadRequest(text="Target is already defeated")
        
        # Check if both characters are in the same room
        if attacker.current_room_id != target.current_room_id:
            raise web.HTTPBadRequest(text="Target is not in the same location")
        
        # Check if attacker has enough rage (minimum 10 for attack)
        if attacker.rage_current < 10:
            raise web.HTTPBadRequest(text="Not enough rage to attack")
        
        # Calculate damage
        damage_breakdown = attacker.calculate_damage_to(target)
        total_damage = damage_breakdown['total']
        
        # Apply damage
        actual_damage = target.take_damage(total_damage)
        
        # Consume rage
        attacker.rage_current = max(0, attacker.rage_current - 10)
        
        # Calculate counter-attack if target survives
        counter_damage = 0
        counter_breakdown = {}
        if target.is_alive() and target.rage_current >= 5:
            counter_breakdown = target.calculate_damage_to(attacker)
            counter_damage = counter_breakdown['total']
            actual_counter = attacker.take_damage(counter_damage)
            target.rage_current = max(0, target.rage_current - 5)
        else:
            actual_counter = 0
        
        # Determine winner
        winner_id = None
        experience_gained = 0
        gold_gained = 0
        
        if not target.is_alive():
            # Attacker wins
            winner_id = attacker.id
            level_diff = max(1, target.level - attacker.level + 1)
            experience_gained = random.randint(50, 150) * level_diff
            gold_gained = random.randint(10, 50) * level_diff
            
            # Apply rewards
            level_gains = attacker.gain_experience(experience_gained)
            attacker.gold += gold_gained
            
            # Penalty for target (lose some experience and gold)
            exp_loss = min(target.experience, experience_gained // 2)
            gold_loss = min(target.gold, gold_gained // 2)
            target.experience = max(0, target.experience - exp_loss)
            target.gold = max(0, target.gold - gold_loss)
            
        elif not attacker.is_alive():
            # Target wins (counter-attack killed attacker)
            winner_id = target.id
            level_diff = max(1, attacker.level - target.level + 1)
            target_exp_gain = random.randint(50, 150) * level_diff
            target_gold_gain = random.randint(10, 50) * level_diff
            
            target.gain_experience(target_exp_gain)
            target.gold += target_gold_gain
            
            # Penalty for attacker
            exp_loss = min(attacker.experience, target_exp_gain // 2)
            gold_loss = min(attacker.gold, target_gold_gain // 2)
            attacker.experience = max(0, attacker.experience - exp_loss)
            attacker.gold = max(0, attacker.gold - gold_loss)
        
        # Update both characters in database
        await database.queries.update_character_stats(
            conn, level=attacker.level, experience=attacker.experience, gold=attacker.gold,
            rage_current=attacker.rage_current, rage_max=attacker.rage_max, hit_points_current=attacker.hit_points_current,
            hit_points_max=attacker.hit_points_max, attack=attacker.attack, total_power=attacker.total_power, character_id=attacker.id
        )
        
        await database.queries.update_character_stats(
            conn, level=target.level, experience=target.experience, gold=target.gold,
            rage_current=target.rage_current, rage_max=target.rage_max, hit_points_current=target.hit_points_current,
            hit_points_max=target.hit_points_max, attack=target.attack, total_power=target.total_power, character_id=target.id
        )
        
        # Log combat
        await database.queries.log_combat(
            conn, attacker_id=attacker.id, defender_id=target.id, attacker_damage=total_damage, defender_damage=counter_damage,
            attacker_hp_before=attacker.hit_points_current + actual_counter, attacker_hp_after=attacker.hit_points_current,
            defender_hp_before=target.hit_points_current + actual_damage, defender_hp_after=target.hit_points_current,
            winner_id=winner_id, experience_gained=experience_gained, gold_gained=gold_gained, combat_type='pvp'
        )
        
        await conn.commit()
    
    # Build combat result page
    result_html = build_combat_result_html(
        attacker, target, damage_breakdown, counter_breakdown,
        actual_damage, actual_counter, winner_id, experience_gained, gold_gained
    )
    
    return web.Response(text=result_html, content_type='text/html')

def build_combat_result_html(attacker, target, damage_breakdown, counter_breakdown, 
                           actual_damage, actual_counter, winner_id, exp_gained, gold_gained):
    """Build Outwar-style combat result HTML"""
    
    # Build combat log entries
    combat_log_entries = []
    
    # Add attacker's actions
    if damage_breakdown.get('total', 0) > 0:
        for dmg_type, amount in damage_breakdown.items():
            if amount > 0 and dmg_type != 'total':
                combat_log_entries.append(f"{attacker.name} hit {target.name} for {amount} {dmg_type} damage!")
    
    # Add defender's counter-attack
    if counter_breakdown and counter_breakdown.get('total', 0) > 0:
        for dmg_type, amount in counter_breakdown.items():
            if amount > 0 and dmg_type != 'total':
                combat_log_entries.append(f"{target.name} hit {attacker.name} for {amount} {dmg_type} damage!")
    
    # Final result
    if winner_id == attacker.id:
        combat_log_entries.append(f"{attacker.name} has defeated {target.name}!")
        result_message = "You have won the battle!"
        reward_text = f"{attacker.name} gained {exp_gained} strength" if exp_gained > 0 else f"{attacker.name} gained 0 strength"
        gold_text = f"🟡 {attacker.name} gained {gold_gained} gold!" if gold_gained > 0 else ""
    elif winner_id == target.id:
        combat_log_entries.append(f"{target.name} has defeated {attacker.name}!")
        result_message = "You have been defeated!"
        reward_text = f"{attacker.name} lost experience and gold"
        gold_text = ""
    else:
        result_message = "Battle continues..."
        reward_text = "No one was defeated"
        gold_text = ""
    
    # Build combat log HTML
    combat_log_html = ""
    for entry in combat_log_entries:
        combat_log_html += f"<div class='log-entry'>{entry}</div>"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Combat Result - {attacker.name} vs {target.name}</title>
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
            
            /* Combat Screen Layout */
            .combat-container {{ padding: 20px; max-width: 800px; margin: 0 auto; text-align: center; }}
            .battle-header {{ margin-bottom: 30px; }}
            .battle-title {{ font-size: 24px; color: #ffd700; margin-bottom: 10px; }}
            .vs-text {{ font-size: 18px; color: #ccc; }}
            
            /* Character Portraits */
            .combatants {{ display: flex; justify-content: space-around; margin: 30px 0; }}
            .combatant {{ width: 200px; }}
            .portrait {{ width: 200px; height: 300px; background: linear-gradient(45deg, #8b0000, #000); border: 2px solid #888; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px; }}
            .portrait.left {{ background: linear-gradient(45deg, #8b0000, #000); }}
            .portrait.right {{ background: linear-gradient(45deg, #4a4a4a, #000); }}
            .health-bar {{ width: 100%; height: 20px; background: #333; border-radius: 10px; overflow: hidden; margin-top: 5px; }}
            .health-fill {{ height: 100%; background: linear-gradient(90deg, #ff4444 0%, #cc3333 100%); transition: width 0.3s; }}
            
            /* Battle Result */
            .battle-result {{ background: #2d2d2d; border: 1px solid #555; border-radius: 8px; padding: 20px; margin: 20px 0; }}
            .result-message {{ font-size: 18px; color: #00ff00; font-weight: bold; margin-bottom: 10px; }}
            .result-message.defeat {{ color: #ff4444; }}
            .reward-line {{ margin: 5px 0; }}
            .gold-reward {{ color: #ffd700; }}
            .combat-log-toggle {{ color: #88ccff; cursor: pointer; text-decoration: underline; margin-top: 10px; }}
            
            /* Combat Log */
            .combat-log {{ background: #1a1a1a; border: 1px solid #555; border-radius: 5px; padding: 15px; margin-top: 10px; text-align: left; display: none; }}
            .combat-log.show {{ display: block; }}
            .log-entry {{ margin: 3px 0; font-family: 'Courier New', monospace; font-size: 11px; color: #fff; }}
            
            /* Return Button */
            .return-button {{ margin-top: 30px; }}
            .btn-return {{ padding: 15px 30px; background: linear-gradient(180deg, #ff6600 0%, #cc5500 100%); color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; text-decoration: none; display: inline-block; }}
            .btn-return:hover {{ background: linear-gradient(180deg, #ff8800 0%, #dd6600 100%); }}
        </style>
    </head>
    <body>
        <!-- Top Navigation -->
        <div class="top-nav">
            <div class="nav-tab">Explore World</div>
            <div class="nav-tab active">Combat</div>
            <div class="nav-tab">Dungeons</div>
            <div class="nav-tab">Challenges</div>
            <div class="nav-tab">All docs</div>
            <div class="nav-tab">News</div>
            <div class="nav-tab">Discord</div>
        </div>
        
        <!-- Header Status Bar -->
        <div class="status-bar">
            <div class="status-left">
                <span>{attacker.name}</span>
                <span>🔴</span>
                <span>🕐 {attacker.id % 12 + 1}:{(attacker.id * 7) % 60:02d}am</span>
                <span>Level: {attacker.level}</span>
                <span>EXP: {attacker.experience:,}</span>
                <span>RAGE: {attacker.rage_current}</span>
            </div>
            <div class="status-right">
                <div class="status-icon"></div>
                <div class="status-icon"></div>
                <div class="status-icon"></div>
                <div class="status-icon"></div>
            </div>
        </div>
        
        <!-- Combat Container -->
        <div class="combat-container">
            <div class="battle-header">
                <div class="battle-title">{attacker.name}</div>
                <div class="vs-text">VS</div>
                <div class="battle-title">{target.name}</div>
            </div>
            
            <!-- Character Portraits -->
            <div class="combatants">
                <div class="combatant">
                    <div class="portrait left">
                        <div style="text-align: center; color: #ccc;">
                            {attacker.name}<br>
                            <small>Level {attacker.level}</small>
                        </div>
                    </div>
                    <div class="health-bar">
                        <div class="health-fill" style="width: {(attacker.hit_points_current/attacker.hit_points_max)*100:.1f}%;"></div>
                    </div>
                    <div style="margin-top: 5px; font-size: 11px;">Health: {attacker.hit_points_current}/{attacker.hit_points_max}</div>
                </div>
                
                <div class="combatant">
                    <div class="portrait right">
                        <div style="text-align: center; color: #ccc;">
                            {target.name}<br>
                            <small>Level {target.level}</small>
                        </div>
                    </div>
                    <div class="health-bar">
                        <div class="health-fill" style="width: {(target.hit_points_current/target.hit_points_max)*100:.1f}%;"></div>
                    </div>
                    <div style="margin-top: 5px; font-size: 11px;">Health: {target.hit_points_current}/{target.hit_points_max}</div>
                </div>
            </div>
            
            <!-- Battle Result -->
            <div class="battle-result">
                <div class="result-message {'defeat' if winner_id == target.id else ''}">{result_message}</div>
                <div class="reward-line">{reward_text}</div>
                {f'<div class="reward-line gold-reward">{gold_text}</div>' if gold_text else ''}
                <div class="combat-log-toggle" onclick="toggleCombatLog()">Show Combat Log</div>
                
                <div class="combat-log" id="combatLog">
                    <div style="margin-bottom: 10px; cursor: pointer;" onclick="toggleCombatLog()">Hide Combat Log</div>
                    {combat_log_html}
                </div>
            </div>
            
            <!-- Return Button -->
            <div class="return-button">
                <a href="/game" class="btn-return">RETURN TO WORLD</a>
            </div>
        </div>
        
        <script>
        function toggleCombatLog() {{
            var log = document.getElementById('combatLog');
            log.classList.toggle('show');
        }}
        </script>
    </body>
    </html>
    """
    return html

async def combat_history(request: web_request.Request):
    """View combat history"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        combat_logs = await database.queries.get_combat_history(conn, character_id=character.id)
    
    # Build combat log HTML
    combat_html = ""
    for log in combat_logs:
        timestamp = datetime.fromisoformat(log['created_at']).strftime('%Y-%m-%d %H:%M')
        
        if log['attacker_id'] == character.id:
            # Character was attacker
            opponent = log['defender_name'] or "Unknown"
            action = "attacked"
            damage_dealt = log['attacker_damage']
            damage_received = log['defender_damage']
        else:
            # Character was defender
            opponent = log['attacker_name'] or "Unknown"
            action = "was attacked by"
            damage_dealt = log['defender_damage']
            damage_received = log['attacker_damage']
        
        result = ""
        if log['winner_id'] == character.id:
            result = '<span style="color: #00ff00;">VICTORY</span>'
        elif log['winner_id'] and log['winner_id'] != character.id:
            result = '<span style="color: #ff4444;">DEFEAT</span>'
        else:
            result = '<span style="color: #ffaa00;">ONGOING</span>'
        
        combat_html += f"""
        <div class="combat-log">
            <div class="log-header">
                <span class="timestamp">{timestamp}</span>
                <span class="result">{result}</span>
            </div>
            <div class="log-details">
                <strong>{character.name}</strong> {action} <strong>{opponent}</strong>
            </div>
            <div class="damage-info">
                Damage dealt: {damage_dealt} | Damage received: {damage_received}
                {f' | Gained: {log["experience_gained"]} XP, {log["gold_gained"]} gold' if log['experience_gained'] > 0 else ''}
            </div>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Combat History - {character.name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }}
            .title {{ color: #ff6600; }}
            .nav a {{ color: #ff6600; text-decoration: none; padding: 10px 15px; background: #333; border-radius: 5px; margin-left: 10px; }}
            .combat-log {{ background: #333; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #ff6600; }}
            .log-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
            .timestamp {{ color: #ccc; font-size: 0.9em; }}
            .log-details {{ margin: 8px 0; }}
            .damage-info {{ font-size: 0.9em; color: #ccc; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1 class="title">COMBAT HISTORY - {character.name}</h1>
            <div class="nav">
                <a href="/game">BACK TO GAME</a>
            </div>
        </div>
        
        <div class="combat-logs">
            {combat_html if combat_html else '<p>No combat history available.</p>'}
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')