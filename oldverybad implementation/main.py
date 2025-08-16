import asyncio
import logging
from aiohttp import web
from config import Config
from database import init_db, close_db
from redis_client import init_redis, close_redis
from routes import setup_routes
from middleware import setup_middleware
from background_tasks import start_background_tasks, stop_background_tasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_app():
    app = web.Application()
    
    # Setup configuration
    app['config'] = Config
    
    # Initialize database
    await init_db(app)
    
    # Initialize Redis
    await init_redis(app)
    
    # Setup middleware
    setup_middleware(app)
    
    # Setup routes
    setup_routes(app)
    
    # Start background tasks
    await start_background_tasks(app)
    
    return app

async def cleanup(app):
    await stop_background_tasks(app)
    await close_redis(app)
    await close_db(app)

def main():
    app_factory = create_app
    
    async def init():
        app = await app_factory()
        app.on_cleanup.append(cleanup)
        return app
    
    app = asyncio.get_event_loop().run_until_complete(init())
    
    web.run_app(
        app,
        host=Config.HOST,
        port=Config.PORT
    )

if __name__ == '__main__':
    main()