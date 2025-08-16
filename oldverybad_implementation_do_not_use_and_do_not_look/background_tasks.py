import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    def __init__(self, app):
        self.app = app
        self.tasks = []
        self.running = False
    
    async def start(self):
        """Start all background tasks"""
        self.running = True
        
        # Resource generation task (every hour)
        self.tasks.append(asyncio.create_task(self._resource_generation_task()))
        
        # NPC respawn task (every 5 minutes)
        self.tasks.append(asyncio.create_task(self._npc_respawn_task()))
        
        # Session cleanup task (every 30 minutes)
        self.tasks.append(asyncio.create_task(self._session_cleanup_task()))
        
        # Daily reset task (every 24 hours)
        self.tasks.append(asyncio.create_task(self._daily_reset_task()))
        
        logger.info("Background tasks started")
    
    async def stop(self):
        """Stop all background tasks"""
        self.running = False
        
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        logger.info("Background tasks stopped")
    
    async def _resource_generation_task(self):
        """Process hourly resource generation for all active characters"""
        while self.running:
            try:
                logger.info("Processing resource generation...")
                
                # Get all characters that need resource generation
                async with self.app['db'].acquire() as conn:
                    # Characters active in last 7 days
                    cutoff_time = datetime.now() - timedelta(days=7)
                    
                    results = await conn.fetch("""
                        SELECT id FROM characters 
                        WHERE last_active >= $1 
                        AND last_resource_update <= NOW() - INTERVAL '1 hour'
                    """, cutoff_time)
                    
                    # Process each character
                    for row in results:
                        character_id = str(row['id'])
                        try:
                            # This would use character service to process resources
                            # For now, just update the timestamp
                            await conn.execute("""
                                UPDATE characters 
                                SET last_resource_update = NOW()
                                WHERE id = $1
                            """, character_id)
                            
                        except Exception as e:
                            logger.error(f"Error processing resources for character {character_id}: {e}")
                
                logger.info("Resource generation completed")
                
            except Exception as e:
                logger.error(f"Error in resource generation task: {e}")
            
            # Wait 1 hour
            await asyncio.sleep(3600)
    
    async def _npc_respawn_task(self):
        """Check and respawn NPCs that should be available"""
        while self.running:
            try:
                logger.debug("Checking NPC respawns...")
                
                async with self.app['db'].acquire() as conn:
                    # Reset NPCs that should have respawned
                    await conn.execute("""
                        UPDATE npcs 
                        SET last_killed = NULL 
                        WHERE last_killed IS NOT NULL 
                        AND last_killed + INTERVAL '1 second' * respawn_time <= NOW()
                    """)
                
            except Exception as e:
                logger.error(f"Error in NPC respawn task: {e}")
            
            # Wait 5 minutes
            await asyncio.sleep(300)
    
    async def _session_cleanup_task(self):
        """Clean up expired sessions and inactive users"""
        while self.running:
            try:
                logger.debug("Cleaning up expired sessions...")
                
                async with self.app['db'].acquire() as conn:
                    # Remove expired sessions
                    await conn.execute("""
                        DELETE FROM user_sessions 
                        WHERE expires_at <= NOW()
                    """)
                    
                    # Clean up old combat logs (keep 30 days)
                    cutoff_date = datetime.now() - timedelta(days=30)
                    await conn.execute("""
                        DELETE FROM combat_logs 
                        WHERE started_at <= $1
                    """, cutoff_date)
                    
                    # Clean up old game events (keep 7 days)
                    event_cutoff = datetime.now() - timedelta(days=7)
                    await conn.execute("""
                        DELETE FROM game_events 
                        WHERE created_at <= $1
                    """, event_cutoff)
                
                logger.debug("Session cleanup completed")
                
            except Exception as e:
                logger.error(f"Error in session cleanup task: {e}")
            
            # Wait 30 minutes
            await asyncio.sleep(1800)
    
    async def _daily_reset_task(self):
        """Perform daily resets (transfer counts, daily quests, etc.)"""
        while self.running:
            try:
                # Calculate time until next midnight
                now = datetime.now()
                tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                sleep_seconds = (tomorrow - now).total_seconds()
                
                # Wait until midnight
                await asyncio.sleep(sleep_seconds)
                
                if not self.running:
                    break
                
                logger.info("Performing daily reset...")
                
                async with self.app['db'].acquire() as conn:
                    # Reset daily transfer counts
                    await conn.execute("""
                        UPDATE character_items 
                        SET transfers_today = 0, last_transfer_date = CURRENT_DATE
                        WHERE last_transfer_date < CURRENT_DATE
                    """)
                    
                    # Reset daily quest progress
                    await conn.execute("""
                        UPDATE character_quests 
                        SET status = 'active', progress = '{}'
                        WHERE quest_template_id IN (
                            SELECT id FROM quest_templates WHERE is_daily = true
                        ) AND status = 'completed'
                    """)
                    
                    # Update experience yesterday tracking
                    await conn.execute("""
                        UPDATE characters 
                        SET experience_yesterday = experience - 
                            COALESCE((
                                SELECT SUM(exp_gained) 
                                FROM combat_logs 
                                WHERE (attacker_id = characters.id OR defender_id = characters.id)
                                AND DATE(started_at) = CURRENT_DATE - INTERVAL '1 day'
                            ), 0)
                    """)
                
                logger.info("Daily reset completed")
                
            except Exception as e:
                logger.error(f"Error in daily reset task: {e}")
                # If error, wait 1 hour before trying again
                await asyncio.sleep(3600)

async def start_background_tasks(app):
    """Start background task manager"""
    manager = BackgroundTaskManager(app)
    app['task_manager'] = manager
    await manager.start()

async def stop_background_tasks(app):
    """Stop background task manager"""
    if 'task_manager' in app:
        await app['task_manager'].stop()