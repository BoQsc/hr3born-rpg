from database import get_db
import random

async def give_starter_equipment(character_id: int):
    """Give new characters basic starter equipment"""
    database = await get_db()
    conn = await database.get_connection()
    try:
        # Give basic equipment based on character level/class
        starter_items = [
            1,  # Rusty Sword (weapon)
            6,  # Cloth Shirt (chest)
            11, # Cloth Cap (head)
            16, # Simple Amulet (accessory)
        ]
        
        for item_id in starter_items:
            await database.queries.add_to_inventory(conn, character_id=character_id, item_id=item_id, quantity=1, transfers_remaining=10)
        
        await conn.commit()
    finally:
        await conn.close()

async def calculate_character_power(character_id: int) -> int:
    """Calculate and update character's total power"""
    database = await get_db()
    conn = await database.get_connection()
    try:
        # Get power calculation from database
        result = await database.queries.calculate_character_total_power(conn, character_id=character_id)
        total_power = result['total_power'] if result else 0
        
        # Update character's total power
        await database.queries.update_character_total_power(conn, total_power=total_power, character_id=character_id)
        await conn.commit()
        
        return total_power
    finally:
        await conn.close()

async def auto_heal_characters():
    """Heal all characters over time (background task)"""
    database = await get_db()
    conn = await database.get_connection()
    try:
        # Heal 1 HP every 5 minutes, full rage every hour
        await conn.execute("""
            UPDATE characters 
            SET hit_points_current = MIN(hit_points_current + 1, hit_points_max),
                rage_current = MIN(rage_current + 5, rage_max)
            WHERE hit_points_current < hit_points_max OR rage_current < rage_max
        """)
        await conn.commit()
    finally:
        await conn.close()