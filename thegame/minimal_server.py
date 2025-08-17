#!/usr/bin/env python3
"""
Minimal server to test basic functionality
"""
from aiohttp import web
import aiohttp_session
from aiohttp_session import SimpleCookieStorage

async def hello(request):
    return web.Response(text="Hello World!")

async def init_app():
    app = web.Application()
    aiohttp_session.setup(app, SimpleCookieStorage())
    
    app.router.add_get('/', hello)
    app.router.add_get('/test', hello)
    
    return app

async def main():
    app = await init_app()
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, 'localhost', 8083)
    await site.start()
    
    print("Server started at http://localhost:8083")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())