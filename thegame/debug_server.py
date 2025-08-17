#!/usr/bin/env python3
"""
Debug version of main.py to find the issue
"""
from aiohttp import web, web_request
import aiohttp_session
from aiohttp_session import SimpleCookieStorage
import asyncio
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
        import traceback
        traceback.print_exc()
        # Return a generic error page
        error_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error - Outwar</title>
            <style>
                body { font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; text-align: center; padding: 50px; }
                .error-container { max-width: 600px; margin: 0 auto; background: #333; padding: 40px; border-radius: 10px; }
                .error-title { color: #ff4444; font-size: 24px; margin-bottom: 20px; }
                .error-message { margin: 20px 0; }
                .back-link { color: #ff6600; text-decoration: none; }
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
    print("Initializing app...")
    app = web.Application(middlewares=[error_middleware])
    
    print("Setting up session...")
    aiohttp_session.setup(app, SimpleCookieStorage())
    
    print("Initializing database...")
    await init_database()
    
    print("Setting up routes...")
    
    # Add routes gradually to find the problematic one
    app.router.add_routes([
        # Authentication
        web.get('/', auth.index),
        web.get('/login', auth.login_page),
        web.post('/login', auth.login),
        web.get('/register', auth.register_page),
        web.post('/register', auth.register),
        web.post('/logout', auth.logout),
    ])
    
    print("Auth routes added...")
    
    # Character management
    app.router.add_routes([
        web.get('/characters', character.character_list),
        web.get('/character/create', character.create_character_page),
        web.post('/character/create', character.create_character),
        web.post('/character/{character_id}/select', character.select_character),
        web.get('/character/{character_id}', character.character_detail),
        web.get('/inventory', character.inventory),
        web.post('/equip/{slot_id}/{item_id}', character.equip_item),
    ])
    
    print("Character routes added...")
    
    # Game world
    app.router.add_routes([
        web.get('/game', world.game_main),
        web.get('/room/{room_id}', world.room_detail),
        web.post('/move/{direction}', world.move_character),
    ])
    
    print("World routes added...")
    
    # Combat
    app.router.add_routes([
        web.post('/attack/{target_id}', combat.attack_player),
        web.get('/combat/history', combat.combat_history),
    ])
    
    print("Combat routes added...")
    
    # Other systems
    app.router.add_routes([
        web.get('/marketplace', marketplace.marketplace_main),
        web.get('/crew', crew.crew_main),
        web.get('/challenges', challenges.challenges_main),
        web.get('/wilderness', wilderness.wilderness_main),
    ])
    
    print("Basic routes added...")
    
    # Test the problematic routes one by one
    try:
        app.router.add_get('/rankings', rankings.rankings_main)
        print("Rankings route added successfully!")
    except Exception as e:
        print(f"Rankings route failed: {e}")
        
    try:
        app.router.add_get('/casino', casino.casino_main)
        print("Casino route added successfully!")
    except Exception as e:
        print(f"Casino route failed: {e}")
    
    return app

async def main():
    try:
        app = await init_app()
        
        print("Starting server...")
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, 'localhost', 8082)
        await site.start()
        
        print("Server started successfully at http://localhost:8082")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("Server stopped")
    except Exception as e:
        print(f"Server error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())