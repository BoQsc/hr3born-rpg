from aiohttp import web

class WorldHandler:
    def __init__(self, app):
        self.app = app
        # World service will be implemented later
    
    async def get_zones(self, request):
        """Get all game zones"""
        try:
            async with self.app['db'].acquire() as conn:
                results = await conn.fetch("SELECT * FROM zones ORDER BY name")
                zones = [dict(row) for row in results]
            
            return web.json_response({'zones': zones})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_zone_rooms(self, request):
        """Get all rooms in a zone"""
        try:
            zone_id = request.match_info['zone_id']
            
            async with self.app['db'].acquire() as conn:
                results = await conn.fetch(
                    "SELECT * FROM rooms WHERE zone_id = $1 ORDER BY room_number",
                    zone_id
                )
                rooms = [dict(row) for row in results]
            
            return web.json_response({'rooms': rooms})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_room(self, request):
        """Get room details"""
        try:
            room_id = request.match_info['room_id']
            
            async with self.app['db'].acquire() as conn:
                room_result = await conn.fetchrow(
                    "SELECT * FROM rooms WHERE id = $1",
                    room_id
                )
                
                if not room_result:
                    return web.json_response({'error': 'Room not found'}, status=404)
                
                room = dict(room_result)
            
            return web.json_response({'room': room})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_room_npcs(self, request):
        """Get NPCs in a room"""
        try:
            room_id = request.match_info['room_id']
            
            async with self.app['db'].acquire() as conn:
                results = await conn.fetch(
                    """SELECT * FROM npcs 
                       WHERE room_id = $1 
                       AND (last_killed IS NULL OR last_killed + INTERVAL '1 second' * respawn_time <= NOW())""",
                    room_id
                )
                npcs = [dict(row) for row in results]
            
            return web.json_response({'npcs': npcs})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_room_players(self, request):
        """Get players in a room"""
        try:
            room_id = request.match_info['room_id']
            
            async with self.app['db'].acquire() as conn:
                results = await conn.fetch(
                    """SELECT id, name, character_class, level, faction 
                       FROM characters 
                       WHERE current_room_id = $1 AND current_hp > 0""",
                    room_id
                )
                players = [dict(row) for row in results]
            
            return web.json_response({'players': players})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def move_character(self, request):
        """Move character to a different room"""
        try:
            character_id = request.match_info['character_id']
            data = await request.json()
            room_id = data.get('room_id')
            
            if not room_id:
                return web.json_response({'error': 'room_id required'}, status=400)
            
            # Verify room exists
            async with self.app['db'].acquire() as conn:
                room = await conn.fetchrow("SELECT * FROM rooms WHERE id = $1", room_id)
                if not room:
                    return web.json_response({'error': 'Room not found'}, status=404)
                
                # Update character location
                await conn.execute(
                    "UPDATE characters SET current_room_id = $1, last_active = NOW() WHERE id = $2",
                    room_id, character_id
                )
            
            return web.json_response({'message': 'Character moved successfully'})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)