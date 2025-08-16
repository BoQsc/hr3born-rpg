from aiohttp import web
from services.combat_service import CombatService

class CombatHandler:
    def __init__(self, app):
        self.app = app
        self.combat_service = CombatService(app['db'], app['queries'], app['redis'])
    
    async def initiate_pvp_combat(self, request):
        """Start PvP combat between two characters"""
        try:
            data = await request.json()
            attacker_id = data.get('attacker_id')
            defender_id = data.get('defender_id')
            
            if not attacker_id or not defender_id:
                return web.json_response({
                    'error': 'Both attacker_id and defender_id required'
                }, status=400)
            
            success, message, result = await self.combat_service.initiate_pvp_combat(
                attacker_id, defender_id
            )
            
            if success:
                return web.json_response({
                    'message': message,
                    'combat_result': result.to_dict() if result else None
                })
            else:
                return web.json_response({'error': message}, status=400)
                
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def initiate_pve_combat(self, request):
        """Start PvE combat between character and NPC"""
        try:
            data = await request.json()
            character_id = data.get('character_id')
            npc_id = data.get('npc_id')
            
            if not character_id or not npc_id:
                return web.json_response({
                    'error': 'Both character_id and npc_id required'
                }, status=400)
            
            success, message, result = await self.combat_service.initiate_pve_combat(
                character_id, npc_id
            )
            
            if success:
                return web.json_response({
                    'message': message,
                    'combat_result': result.to_dict() if result else None
                })
            else:
                return web.json_response({'error': message}, status=400)
                
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_combat_history(self, request):
        """Get combat history for a character"""
        try:
            character_id = request.match_info['character_id']
            limit = int(request.query.get('limit', 20))
            
            history = await self.combat_service.get_combat_history(character_id, limit)
            
            return web.json_response({'combat_history': history})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_recent_pvp_battles(self, request):
        """Get recent PvP battles"""
        try:
            limit = int(request.query.get('limit', 50))
            battles = await self.combat_service.get_recent_pvp_battles(limit)
            
            return web.json_response({'recent_battles': battles})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)