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
    """Build HTML for combat results"""
    
    # Build damage breakdown
    damage_details = ""
    for dmg_type, amount in damage_breakdown.items():
        if amount > 0 and dmg_type != 'total':
            damage_details += f"<li>{dmg_type.title()}: {amount}</li>"
    
    counter_details = ""
    if counter_breakdown:
        for dmg_type, amount in counter_breakdown.items():
            if amount > 0 and dmg_type != 'total':
                counter_details += f"<li>{dmg_type.title()}: {amount}</li>"
    
    # Determine result message
    if winner_id == attacker.id:
        result_class = "victory"
        result_message = "VICTORY!"
        reward_message = f"Gained {exp_gained:,} experience and {gold_gained:,} gold!"
    elif winner_id == target.id:
        result_class = "defeat"
        result_message = "DEFEAT!"
        reward_message = "You were defeated and lost experience and gold."
    else:
        result_class = "draw"
        result_message = "BATTLE CONTINUES"
        reward_message = "Both fighters survive to fight another day."
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Combat Result - {attacker.name} vs {target.name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }}
            .combat-result {{ max-width: 800px; margin: 0 auto; }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .result-title {{ font-size: 2.5em; margin-bottom: 10px; }}
            .victory {{ color: #00ff00; }}
            .defeat {{ color: #ff4444; }}
            .draw {{ color: #ffaa00; }}
            .combatants {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin: 30px 0; }}
            .combatant {{ background: #333; padding: 20px; border-radius: 10px; }}
            .combatant h3 {{ color: #ff6600; margin-top: 0; }}
            .damage-breakdown {{ background: #444; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .damage-breakdown h4 {{ margin-top: 0; color: #ff6600; }}
            .damage-breakdown ul {{ margin: 10px 0; padding-left: 20px; }}
            .total-damage {{ font-size: 1.2em; font-weight: bold; color: #ff4444; }}
            .hp-bar {{ margin: 10px 0; }}
            .hp-label {{ display: flex; justify-content: space-between; }}
            .hp-progress {{ width: 100%; height: 20px; background: #555; border-radius: 10px; margin-top: 5px; }}
            .hp-fill {{ height: 100%; border-radius: 10px; background: #ff4444; }}
            .rewards {{ background: #004400; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center; }}
            .penalties {{ background: #440000; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center; }}
            .actions {{ text-align: center; margin: 30px 0; }}
            .btn {{ padding: 15px 30px; background: #ff6600; color: white; text-decoration: none; border-radius: 5px; margin: 0 10px; }}
            .btn:hover {{ background: #ff8833; }}
        </style>
    </head>
    <body>
        <div class="combat-result">
            <div class="header">
                <h1 class="result-title {result_class}">{result_message}</h1>
                <h2>{attacker.name} vs {target.name}</h2>
            </div>
            
            <div class="combatants">
                <div class="combatant">
                    <h3>{attacker.name} (Attacker)</h3>
                    <div class="damage-breakdown">
                        <h4>Damage Dealt: {damage_breakdown['total']}</h4>
                        <ul>
                            {damage_details}
                        </ul>
                        <div class="total-damage">Actual Damage: {actual_damage}</div>
                    </div>
                    <div class="hp-bar">
                        <div class="hp-label">
                            <span>Hit Points</span>
                            <span>{attacker.hit_points_current}/{attacker.hit_points_max}</span>
                        </div>
                        <div class="hp-progress">
                            <div class="hp-fill" style="width: {(attacker.hit_points_current/attacker.hit_points_max)*100:.1f}%;"></div>
                        </div>
                    </div>
                    {f'<div class="rewards"><strong>{reward_message}</strong></div>' if winner_id == attacker.id else ''}
                    {f'<div class="penalties"><strong>{reward_message}</strong></div>' if winner_id == target.id else ''}
                </div>
                
                <div class="combatant">
                    <h3>{target.name} (Defender)</h3>
                    {f'''
                    <div class="damage-breakdown">
                        <h4>Counter Damage: {counter_breakdown.get('total', 0)}</h4>
                        <ul>
                            {counter_details}
                        </ul>
                        <div class="total-damage">Actual Damage: {actual_counter}</div>
                    </div>
                    ''' if counter_breakdown else '<p><em>No counter-attack</em></p>'}
                    <div class="hp-bar">
                        <div class="hp-label">
                            <span>Hit Points</span>
                            <span>{target.hit_points_current}/{target.hit_points_max}</span>
                        </div>
                        <div class="hp-progress">
                            <div class="hp-fill" style="width: {(target.hit_points_current/target.hit_points_max)*100:.1f}%;"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="actions">
                <a href="/game" class="btn">RETURN TO GAME</a>
                <a href="/combat/history" class="btn">COMBAT HISTORY</a>
            </div>
        </div>
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
        combat_logs = await database.queries.get_combat_history(conn, attacker_id=character.id, target_id=character.id)
    
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