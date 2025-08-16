from aiohttp import web, web_request
import aiohttp_session
from aiohttp_session import SimpleCookieStorage
import asyncio
import secrets
from pathlib import Path

from database import init_database, get_db
from handlers import auth, character, world, crew, combat

async def init_app():
    app = web.Application()
    
    # Setup session storage (using SimpleCookieStorage for now)
    # Note: In production, use EncryptedCookieStorage with proper key management
    aiohttp_session.setup(app, SimpleCookieStorage())
    
    # Initialize database
    await init_database()
    
    # Setup routes
    app.router.add_routes([
        # Authentication
        web.get('/', auth.index),
        web.get('/login', auth.login_page),
        web.post('/login', auth.login),
        web.get('/register', auth.register_page),
        web.post('/register', auth.register),
        web.post('/logout', auth.logout),
        
        # Character management
        web.get('/characters', character.character_list),
        web.get('/character/create', character.create_character_page),
        web.post('/character/create', character.create_character),
        web.get('/character/{character_id}', character.character_detail),
        web.post('/character/{character_id}/select', character.select_character),
        
        # Game world
        web.get('/game', world.game_main),
        web.get('/room/{room_id}', world.room_detail),
        web.post('/move/{direction}', world.move_character),
        
        # Equipment and inventory
        web.get('/inventory', character.inventory),
        web.post('/equip/{item_id}', character.equip_item),
        web.post('/unequip/{slot_id}', character.unequip_item),
        
        # Combat
        web.post('/attack/{target_id}', combat.attack_player),
        web.get('/combat/history', combat.combat_history),
        
        # Crew system
        web.get('/crew', crew.crew_main),
        web.get('/crew/create', crew.create_crew_page),
        web.post('/crew/create', crew.create_crew),
        web.post('/crew/{crew_id}/join', crew.join_crew),
        web.get('/crew/vault', crew.crew_vault),
        
        # Static files
        web.static('/static', Path(__file__).parent / 'static'),
    ])
    
    return app

async def cleanup_sessions():
    """Clean up expired sessions periodically"""
    while True:
        try:
            database = await get_db()
            conn = await database.get_connection()
            try:
                await database.queries.cleanup_expired_sessions(conn)
                await conn.commit()
            finally:
                await conn.close()
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")
        
        # Clean up every hour
        await asyncio.sleep(3600)

async def heal_characters():
    """Heal characters periodically"""
    while True:
        try:
            from services.character_service import auto_heal_characters
            await auto_heal_characters()
        except Exception as e:
            print(f"Error healing characters: {e}")
        
        # Heal every 5 minutes
        await asyncio.sleep(300)

async def main():
    app = await init_app()
    
    # Start background tasks
    asyncio.create_task(cleanup_sessions())
    asyncio.create_task(heal_characters())
    
    # Run the web application
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8082)
    print("Starting server at http://localhost:8082")
    await site.start()
    
    # Keep running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    asyncio.run(main())