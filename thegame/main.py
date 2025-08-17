from aiohttp import web, web_request
import aiohttp_session
from aiohttp_session import SimpleCookieStorage
import asyncio
import secrets
from pathlib import Path

from database import init_database, get_db
from handlers import auth, character, world, crew, combat, marketplace, rankings, casino, challenges, wilderness, factions, supplies, treasury, quests

@web.middleware
async def error_middleware(request, handler):
    """Global error handling middleware"""
    try:
        return await handler(request)
    except web.HTTPException:
        # Re-raise HTTP exceptions (redirects, etc.)
        raise
    except Exception as e:
        print(f"Unhandled error in {request.path}: {e}")
        # Return a generic error page
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error - Outwar</title>
            <style>
                body {{ font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; text-align: center; padding: 50px; }}
                .error-container {{ max-width: 600px; margin: 0 auto; background: #333; padding: 40px; border-radius: 10px; }}
                .error-title {{ color: #ff4444; font-size: 24px; margin-bottom: 20px; }}
                .error-message {{ margin: 20px 0; }}
                .back-link {{ color: #ff6600; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1 class="error-title">Oops! Something went wrong</h1>
                <div class="error-message">
                    An unexpected error occurred while processing your request.
                    Please try again later.
                </div>
                <a href="/game" class="back-link">← Return to Game</a>
            </div>
        </body>
        </html>
        """
        return web.Response(text=error_html, content_type='text/html', status=500)

async def init_app():
    app = web.Application(middlewares=[error_middleware])
    
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
        
        # Marketplace system
        web.get('/marketplace', marketplace.marketplace_main),
        web.post('/marketplace/buy/{listing_id}', marketplace.buy_item),
        web.post('/marketplace/sell', marketplace.sell_item),
        
        # Rankings system
        web.get('/rankings', rankings.rankings_main),
        
        # Casino system
        web.get('/casino', casino.casino_main),
        web.post('/casino/update-gold', casino.update_gold),
        
        # Challenges and dungeons
        web.get('/challenges', challenges.challenges_main),
        web.post('/challenges/start/{challenge_id}', challenges.start_challenge),
        web.post('/challenges/claim/{challenge_id}', challenges.claim_reward),
        
        # Wilderness exploration
        web.get('/wilderness', wilderness.wilderness_main),
        web.post('/wilderness/explore', wilderness.explore_wilderness),
        web.post('/wilderness/combat', wilderness.wilderness_combat),
        
        # Faction system
        web.get('/factions', factions.factions_main),
        web.post('/factions/join/{faction_id}', factions.join_faction),
        web.post('/factions/leave', factions.leave_faction),
        
        # Supplies shop
        web.get('/supplies', supplies.supplies_main),
        web.post('/supplies/buy', supplies.buy_supplies),
        
        # Treasury system
        web.get('/treasury', treasury.treasury_main),
        web.post('/treasury/banking', treasury.handle_banking),
        web.post('/treasury/invest', treasury.handle_investment),
        web.post('/treasury/insurance', treasury.handle_insurance),
        web.post('/treasury/claim', treasury.handle_claim),
        
        # Quest system
        web.get('/quests', quests.quest_helper),
        web.post('/quests/accept/{quest_id}', quests.accept_quest),
        web.post('/quests/track/{quest_id}', quests.track_quest),
        
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
            database = await get_db()
            async with database.get_connection_context() as conn:
                # Heal all characters by 10 HP every 5 minutes
                await conn.execute("""
                    UPDATE characters 
                    SET hit_points_current = MIN(hit_points_current + 10, hit_points_max)
                    WHERE hit_points_current < hit_points_max
                """)
                await conn.commit()
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
    site = web.TCPSite(runner, 'localhost', 8083)
    print("Starting server at http://localhost:8083")
    await site.start()
    
    # Keep running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    asyncio.run(main())