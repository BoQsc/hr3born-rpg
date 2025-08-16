from aiohttp import web

class CrewHandler:
    def __init__(self, app):
        self.app = app
        # Crew service will be implemented later
    
    async def create_crew(self, request):
        """Create a new crew"""
        try:
            data = await request.json()
            user_id = request['user_id']
            
            name = data.get('name', '').strip()
            description = data.get('description', '').strip()
            
            if not name or len(name) < 3:
                return web.json_response({
                    'error': 'Crew name must be at least 3 characters long'
                }, status=400)
            
            async with self.app['db'].acquire() as conn:
                # Check if crew name exists
                existing = await conn.fetchrow("SELECT id FROM crews WHERE name = $1", name)
                if existing:
                    return web.json_response({
                        'error': 'Crew name already exists'
                    }, status=400)
                
                # Create crew
                result = await conn.fetchrow(
                    """INSERT INTO crews (name, description, leader_id) 
                       VALUES ($1, $2, $3) RETURNING id""",
                    name, description, user_id
                )
                
                crew_id = str(result['id'])
            
            return web.json_response({
                'message': 'Crew created successfully',
                'crew_id': crew_id
            }, status=201)
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_crew(self, request):
        """Get crew details"""
        try:
            crew_id = request.match_info['crew_id']
            
            async with self.app['db'].acquire() as conn:
                crew = await conn.fetchrow(
                    """SELECT c.*, u.username as leader_name
                       FROM crews c
                       LEFT JOIN users u ON c.leader_id = u.id
                       WHERE c.id = $1""",
                    crew_id
                )
                
                if not crew:
                    return web.json_response({'error': 'Crew not found'}, status=404)
            
            return web.json_response({'crew': dict(crew)})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_crew_members(self, request):
        """Get crew members"""
        try:
            crew_id = request.match_info['crew_id']
            
            async with self.app['db'].acquire() as conn:
                members = await conn.fetch(
                    """SELECT id, name, character_class, level, crew_rank, last_active
                       FROM characters 
                       WHERE crew_id = $1 
                       ORDER BY crew_rank DESC, level DESC""",
                    crew_id
                )
            
            return web.json_response({'members': [dict(row) for row in members]})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_crew_vault(self, request):
        """Get crew vault items"""
        try:
            crew_id = request.match_info['crew_id']
            
            async with self.app['db'].acquire() as conn:
                vault_items = await conn.fetch(
                    """SELECT cvi.*, it.name, it.rarity, it.description,
                              c.name as deposited_by_name
                       FROM crew_vault_items cvi
                       JOIN item_templates it ON cvi.item_template_id = it.id
                       LEFT JOIN characters c ON cvi.deposited_by = c.id
                       WHERE cvi.crew_id = $1
                       ORDER BY cvi.vault_position""",
                    crew_id
                )
            
            return web.json_response({'vault_items': [dict(row) for row in vault_items]})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def deposit_item(self, request):
        """Deposit item to crew vault"""
        try:
            crew_id = request.match_info['crew_id']
            data = await request.json()
            character_id = data.get('character_id')
            item_id = data.get('item_id')
            
            # This would use equipment service
            return web.json_response({'message': 'Item deposited to vault'})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def award_item(self, request):
        """Award vault item to character"""
        try:
            crew_id = request.match_info['crew_id']
            data = await request.json()
            vault_item_id = data.get('vault_item_id')
            character_id = data.get('character_id')
            
            # This would use equipment service
            return web.json_response({'message': 'Item awarded to character'})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def delete_vault_item(self, request):
        """Delete item from vault"""
        try:
            crew_id = request.match_info['crew_id']
            item_id = request.match_info['item_id']
            
            async with self.app['db'].acquire() as conn:
                await conn.execute(
                    "DELETE FROM crew_vault_items WHERE id = $1 AND crew_id = $2",
                    item_id, crew_id
                )
            
            return web.json_response({'message': 'Item deleted from vault'})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def join_crew(self, request):
        """Join a crew"""
        try:
            crew_id = request.match_info['crew_id']
            data = await request.json()
            character_id = data.get('character_id')
            
            async with self.app['db'].acquire() as conn:
                await conn.execute(
                    "UPDATE characters SET crew_id = $1, crew_rank = 'member' WHERE id = $2",
                    crew_id, character_id
                )
            
            return web.json_response({'message': 'Joined crew successfully'})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def leave_crew(self, request):
        """Leave a crew"""
        try:
            crew_id = request.match_info['crew_id']
            data = await request.json()
            character_id = data.get('character_id')
            
            async with self.app['db'].acquire() as conn:
                await conn.execute(
                    "UPDATE characters SET crew_id = NULL, crew_rank = 'member' WHERE id = $1",
                    character_id
                )
            
            return web.json_response({'message': 'Left crew successfully'})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
    
    async def get_top_crews(self, request):
        """Get top crews by member count and level"""
        try:
            limit = int(request.query.get('limit', 20))
            
            async with self.app['db'].acquire() as conn:
                crews = await conn.fetch(
                    """SELECT c.*, COUNT(ch.id) as member_count,
                              AVG(ch.level) as avg_level,
                              u.username as leader_name
                       FROM crews c
                       LEFT JOIN characters ch ON c.id = ch.crew_id
                       LEFT JOIN users u ON c.leader_id = u.id
                       GROUP BY c.id, u.username
                       ORDER BY member_count DESC, avg_level DESC
                       LIMIT $1""",
                    limit
                )
            
            return web.json_response({'crews': [dict(row) for row in crews]})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)