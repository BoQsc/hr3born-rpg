from aiohttp import web
import datetime
from handlers.auth import AuthHandler
from handlers.character import CharacterHandler
from handlers.equipment import EquipmentHandler
from handlers.combat import CombatHandler
from handlers.world import WorldHandler
from handlers.crew import CrewHandler

def setup_routes(app):
    """Setup all application routes"""
    
    # Create handlers
    auth_handler = AuthHandler(app)
    character_handler = CharacterHandler(app)
    equipment_handler = EquipmentHandler(app)
    combat_handler = CombatHandler(app)
    world_handler = WorldHandler(app)
    crew_handler = CrewHandler(app)
    
    # Health check
    app.router.add_get('/api/health', health_check)
    
    # Authentication routes
    app.router.add_post('/api/auth/register', auth_handler.register)
    app.router.add_post('/api/auth/login', auth_handler.login)
    app.router.add_post('/api/auth/logout', auth_handler.logout)
    app.router.add_get('/api/auth/me', auth_handler.get_current_user)
    
    # Character routes
    app.router.add_post('/api/characters', character_handler.create_character)
    app.router.add_get('/api/characters', character_handler.get_user_characters)
    app.router.add_get('/api/characters/{character_id}', character_handler.get_character)
    app.router.add_put('/api/characters/{character_id}/faction', character_handler.change_faction)
    app.router.add_post('/api/characters/{character_id}/heal', character_handler.heal_character)
    app.router.add_get('/api/characters/{character_id}/stats', character_handler.get_character_stats)
    
    # Equipment routes
    app.router.add_get('/api/characters/{character_id}/items', equipment_handler.get_character_items)
    app.router.add_get('/api/characters/{character_id}/equipment', equipment_handler.get_character_equipment)
    app.router.add_post('/api/characters/{character_id}/items/{item_id}/equip', equipment_handler.equip_item)
    app.router.add_post('/api/characters/{character_id}/items/{item_id}/unequip', equipment_handler.unequip_item)
    app.router.add_post('/api/items/{item_id}/transfer', equipment_handler.transfer_item)
    
    # Combat routes
    app.router.add_post('/api/combat/pvp', combat_handler.initiate_pvp_combat)
    app.router.add_post('/api/combat/pve', combat_handler.initiate_pve_combat)
    app.router.add_get('/api/combat/history/{character_id}', combat_handler.get_combat_history)
    app.router.add_get('/api/combat/recent-pvp', combat_handler.get_recent_pvp_battles)
    
    # World routes
    app.router.add_get('/api/world/zones', world_handler.get_zones)
    app.router.add_get('/api/world/zones/{zone_id}/rooms', world_handler.get_zone_rooms)
    app.router.add_get('/api/world/rooms/{room_id}', world_handler.get_room)
    app.router.add_get('/api/world/rooms/{room_id}/npcs', world_handler.get_room_npcs)
    app.router.add_get('/api/world/rooms/{room_id}/players', world_handler.get_room_players)
    app.router.add_post('/api/characters/{character_id}/move', world_handler.move_character)
    
    # Crew routes
    app.router.add_post('/api/crews', crew_handler.create_crew)
    app.router.add_get('/api/crews/{crew_id}', crew_handler.get_crew)
    app.router.add_get('/api/crews/{crew_id}/members', crew_handler.get_crew_members)
    app.router.add_get('/api/crews/{crew_id}/vault', crew_handler.get_crew_vault)
    app.router.add_post('/api/crews/{crew_id}/vault/deposit', crew_handler.deposit_item)
    app.router.add_post('/api/crews/{crew_id}/vault/award', crew_handler.award_item)
    app.router.add_delete('/api/crews/{crew_id}/vault/{item_id}', crew_handler.delete_vault_item)
    app.router.add_post('/api/crews/{crew_id}/join', crew_handler.join_crew)
    app.router.add_post('/api/crews/{crew_id}/leave', crew_handler.leave_crew)
    
    # Rankings routes
    app.router.add_get('/api/rankings/characters', character_handler.get_top_characters)
    app.router.add_get('/api/rankings/crews', crew_handler.get_top_crews)
    
    # Static files and main page
    app.router.add_static('/static/', path='static/', name='static')
    app.router.add_get('/', serve_index)

async def health_check(request):
    """Health check endpoint"""
    return web.json_response({'status': 'healthy', 'timestamp': datetime.datetime.now().isoformat()})

async def serve_index(request):
    """Serve the main game page"""
    return web.FileResponse('static/index.html')