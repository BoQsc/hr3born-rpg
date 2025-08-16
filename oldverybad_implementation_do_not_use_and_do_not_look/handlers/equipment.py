from aiohttp import web
from services.equipment_service import EquipmentService

class EquipmentHandler:
    def __init__(self, app):
        self.app = app
        self.equipment_service = EquipmentService(app['db'], app['queries'], app['redis'])
    
    async def get_character_items(self, request):
        """Get all items for a character"""
        try:
            character_id = request.match_info['character_id']
            items = await self.equipment_service.get_character_items(character_id)
            
            return web.json_response({
                'items': [item.to_dict() for item in items]
            })
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_character_equipment(self, request):
        """Get character's equipped items"""
        try:
            character_id = request.match_info['character_id']
            equipment = await self.equipment_service.get_character_equipped_items(character_id)
            
            return web.json_response({
                'equipment': equipment.to_dict()
            })
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def equip_item(self, request):
        """Equip an item to a slot"""
        try:
            character_id = request.match_info['character_id']
            item_id = request.match_info['item_id']
            data = await request.json()
            slot = data.get('slot')
            
            if not slot:
                return web.json_response({'error': 'Slot required'}, status=400)
            
            success, message = await self.equipment_service.equip_item(character_id, item_id, slot)
            
            if success:
                return web.json_response({'message': message})
            else:
                return web.json_response({'error': message}, status=400)
                
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def unequip_item(self, request):
        """Unequip an item"""
        try:
            character_id = request.match_info['character_id']
            item_id = request.match_info['item_id']
            
            success, message = await self.equipment_service.unequip_item(character_id, item_id)
            
            if success:
                return web.json_response({'message': message})
            else:
                return web.json_response({'error': message}, status=400)
                
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def transfer_item(self, request):
        """Transfer item between characters"""
        try:
            item_id = request.match_info['item_id']
            data = await request.json()
            from_character_id = data.get('from_character_id')
            to_character_id = data.get('to_character_id')
            
            if not from_character_id or not to_character_id:
                return web.json_response({
                    'error': 'Both from_character_id and to_character_id required'
                }, status=400)
            
            success, message = await self.equipment_service.transfer_item(
                item_id, from_character_id, to_character_id
            )
            
            if success:
                return web.json_response({'message': message})
            else:
                return web.json_response({'error': message}, status=400)
                
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)