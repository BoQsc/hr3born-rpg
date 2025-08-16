import json
import jwt
from aiohttp import web
from aiohttp.web_middlewares import middleware
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@middleware
async def auth_middleware(request, handler):
    """Authentication middleware"""
    # Skip auth for certain paths
    skip_auth_paths = ['/api/auth/login', '/api/auth/register', '/api/health', '/']
    
    if request.path in skip_auth_paths or request.path.startswith('/static/'):
        return await handler(request)
    
    # Get token from Authorization header
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        raise web.HTTPUnauthorized(text=json.dumps({'error': 'Missing or invalid authorization header'}))
    
    token = auth_header[7:]  # Remove 'Bearer ' prefix
    
    try:
        # Decode JWT token
        config = request.app['config']
        payload = jwt.decode(token, config.JWT_SECRET, algorithms=['HS256'])
        
        # Add user info to request
        request['user_id'] = payload['user_id']
        request['username'] = payload['username']
        
        # Update last activity
        redis_manager = request.app.get('redis_manager')
        if redis_manager:
            await redis_manager.set_session(payload['user_id'], {
                'user_id': payload['user_id'],
                'username': payload['username'],
                'last_activity': datetime.now().isoformat()
            })
        
    except jwt.ExpiredSignatureError:
        raise web.HTTPUnauthorized(text=json.dumps({'error': 'Token has expired'}))
    except jwt.InvalidTokenError:
        raise web.HTTPUnauthorized(text=json.dumps({'error': 'Invalid token'}))
    
    return await handler(request)

@middleware
async def cors_middleware(request, handler):
    """CORS middleware"""
    response = await handler(request)
    
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    return response

@middleware
async def error_middleware(request, handler):
    """Error handling middleware"""
    try:
        return await handler(request)
    except web.HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unhandled error in {request.path}: {e}")
        
        if request.app['config'].DEBUG:
            error_detail = str(e)
        else:
            error_detail = "Internal server error"
        
        return web.json_response(
            {'error': error_detail},
            status=500
        )

@middleware
async def json_error_middleware(request, handler):
    """Convert HTTP errors to JSON responses"""
    try:
        return await handler(request)
    except web.HTTPException as e:
        if e.status == 404:
            return web.json_response(
                {'error': 'Not found'},
                status=404
            )
        elif e.status == 405:
            return web.json_response(
                {'error': 'Method not allowed'},
                status=405
            )
        else:
            return web.json_response(
                {'error': e.reason},
                status=e.status
            )

def setup_middleware(app):
    """Setup all middleware"""
    app.middlewares.append(cors_middleware)
    app.middlewares.append(error_middleware)
    app.middlewares.append(json_error_middleware)
    app.middlewares.append(auth_middleware)