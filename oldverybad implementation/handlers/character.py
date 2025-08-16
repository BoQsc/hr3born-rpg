from aiohttp import web
from services.character_service import CharacterService
from models.character import CharacterCreationRequest

class CharacterHandler:
    def __init__(self, app):
        self.app = app
        self.character_service = CharacterService(app['db'], app['queries'], app['redis'])
    
    async def create_character(self, request):
        """Create a new character"""
        try:
            data = await request.json()
            user_id = request['user_id']
            
            # Create character request
            char_request = CharacterCreationRequest(
                name=data.get('name', ''),
                character_class=data.get('character_class', '')
            )
            
            # Create character
            success, message, character = await self.character_service.create_character(user_id, char_request)
            
            if success:
                return web.json_response({
                    'message': message,
                    'character': character.to_dict() if character else None
                }, status=201)
            else:
                return web.json_response({'error': message}, status=400)
                
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_user_characters(self, request):
        """Get all characters for the current user"""
        try:
            user_id = request['user_id']
            characters = await self.character_service.get_user_characters(user_id)
            
            return web.json_response({'characters': characters})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_character(self, request):
        """Get specific character details"""
        try:
            character_id = request.match_info['character_id']
            character = await self.character_service.get_character(character_id)
            
            if not character:
                return web.json_response({'error': 'Character not found'}, status=404)
            
            return web.json_response({'character': character.to_dict()})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def change_faction(self, request):
        """Change character's faction"""
        try:
            character_id = request.match_info['character_id']
            data = await request.json()
            faction = data.get('faction')
            
            success, message = await self.character_service.change_faction(character_id, faction)
            
            if success:
                return web.json_response({'message': message})
            else:
                return web.json_response({'error': message}, status=400)
                
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def heal_character(self, request):
        """Heal character"""
        try:
            character_id = request.match_info['character_id']
            data = await request.json()
            heal_amount = data.get('heal_amount', 0)
            
            success = await self.character_service.heal_character(character_id, heal_amount)
            
            if success:
                return web.json_response({'message': 'Character healed'})
            else:
                return web.json_response({'error': 'Failed to heal character'}, status=400)
                
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_character_stats(self, request):
        """Get character stats with equipment bonuses"""
        try:
            character_id = request.match_info['character_id']
            
            # Process resource generation first
            resources = await self.character_service.process_resource_generation(character_id)
            
            character = await self.character_service.get_character(character_id)
            
            if not character:
                return web.json_response({'error': 'Character not found'}, status=404)
            
            return web.json_response({
                'character': character.to_dict(),
                'resource_generation': resources
            })
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_top_characters(self, request):
        """Get top characters by level"""
        try:
            limit = int(request.query.get('limit', 50))
            characters = await self.character_service.get_top_characters(limit)
            
            return web.json_response({'characters': characters})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)