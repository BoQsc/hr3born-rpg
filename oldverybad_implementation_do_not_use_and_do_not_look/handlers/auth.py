import json
import bcrypt
import jwt
from datetime import datetime, timedelta
from aiohttp import web
from services.user_service import UserService

class AuthHandler:
    def __init__(self, app):
        self.app = app
        self.user_service = UserService(app['db'], app['queries'], app['redis'])
    
    async def register(self, request):
        """Register a new user"""
        try:
            data = await request.json()
            
            username = data.get('username', '').strip()
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            
            # Validate input
            if not username or len(username) < 3:
                return web.json_response(
                    {'error': 'Username must be at least 3 characters long'},
                    status=400
                )
            
            if not email or '@' not in email or '.' not in email:
                return web.json_response(
                    {'error': 'Valid email address required'},
                    status=400
                )
            
            if not password or len(password) < 6:
                return web.json_response(
                    {'error': 'Password must be at least 6 characters long'},
                    status=400
                )
            
            # Check if user already exists
            existing_user = await self.user_service.get_user_by_username(username)
            if existing_user:
                return web.json_response(
                    {'error': 'Username already exists'},
                    status=400
                )
            
            existing_email = await self.user_service.get_user_by_email(email)
            if existing_email:
                return web.json_response(
                    {'error': 'Email already registered'},
                    status=400
                )
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Create user
            user_id = await self.user_service.create_user(username, email, password_hash)
            
            if user_id:
                return web.json_response({
                    'message': 'User registered successfully',
                    'user_id': user_id
                }, status=201)
            else:
                return web.json_response(
                    {'error': 'Failed to create user'},
                    status=500
                )
                
        except Exception as e:
            return web.json_response(
                {'error': f'Registration failed: {str(e)}'},
                status=500
            )
    
    async def login(self, request):
        """Login user"""
        try:
            data = await request.json()
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            if not username or not password:
                return web.json_response(
                    {'error': 'Username and password required'},
                    status=400
                )
            
            # Get user
            user = await self.user_service.get_user_by_username(username)
            if not user:
                return web.json_response(
                    {'error': 'Invalid username or password'},
                    status=401
                )
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                return web.json_response(
                    {'error': 'Invalid username or password'},
                    status=401
                )
            
            # Update last login
            await self.user_service.update_last_login(user['id'])
            
            # Generate JWT token
            config = self.app['config']
            payload = {
                'user_id': str(user['id']),
                'username': user['username'],
                'exp': datetime.utcnow() + timedelta(days=7)  # 7 day expiry
            }
            
            token = jwt.encode(payload, config.JWT_SECRET, algorithm='HS256')
            
            # Store session in Redis
            await self.user_service.create_session(str(user['id']), token)
            
            return web.json_response({
                'token': token,
                'user': {
                    'id': str(user['id']),
                    'username': user['username'],
                    'email': user['email'],
                    'is_preferred_player': user['is_preferred_player'],
                    'points': user['points'],
                    'character_slots': user['character_slots']
                }
            })
            
        except Exception as e:
            return web.json_response(
                {'error': f'Login failed: {str(e)}'},
                status=500
            )
    
    async def logout(self, request):
        """Logout user"""
        try:
            user_id = request.get('user_id')
            if user_id:
                await self.user_service.delete_session(user_id)
            
            return web.json_response({'message': 'Logged out successfully'})
            
        except Exception as e:
            return web.json_response(
                {'error': f'Logout failed: {str(e)}'},
                status=500
            )
    
    async def get_current_user(self, request):
        """Get current user information"""
        try:
            user_id = request.get('user_id')
            user = await self.user_service.get_user_by_id(user_id)
            
            if not user:
                return web.json_response(
                    {'error': 'User not found'},
                    status=404
                )
            
            # Get user's characters
            characters = await self.user_service.get_user_characters(user_id)
            
            return web.json_response({
                'user': {
                    'id': str(user['id']),
                    'username': user['username'],
                    'email': user['email'],
                    'is_preferred_player': user['is_preferred_player'],
                    'points': user['points'],
                    'character_slots': user['character_slots'],
                    'created_at': user['created_at'].isoformat(),
                    'last_login': user['last_login'].isoformat() if user['last_login'] else None
                },
                'characters': characters
            })
            
        except Exception as e:
            return web.json_response(
                {'error': f'Failed to get user info: {str(e)}'},
                status=500
            )