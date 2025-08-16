from aiohttp import web, web_request
import aiohttp_session
import hashlib
import secrets
from datetime import datetime, timedelta

from database import get_db

async def get_current_user(request: web_request.Request):
    """Get currently logged in user from session"""
    session = await aiohttp_session.get_session(request)
    user_id = session.get('user_id')
    
    if not user_id:
        return None
        
    # Return a simple user object from session data
    return {
        'id': user_id,
        'username': session.get('username')
    }

async def require_login(request: web_request.Request):
    """Middleware to require login"""
    user = await get_current_user(request)
    if not user:
        raise web.HTTPFound('/login')
    return user

def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hash password with salt"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    pwd_hash = hashlib.pbkdf2_hmac('sha256', 
                                  password.encode('utf-8'), 
                                  salt.encode('utf-8'), 
                                  100000)
    return pwd_hash.hex(), salt

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    try:
        if ':' in hashed:
            pwd_hash, salt = hashed.split(':')
            calculated_hash, _ = hash_password(password, salt)
            return calculated_hash == pwd_hash
        return False
    except:
        return False

async def index(request: web_request.Request):
    """Landing page"""
    user = await get_current_user(request)
    
    if user:
        # Redirect to character list if logged in
        raise web.HTTPFound('/characters')
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Outwar Clone - Welcome</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }
            .container { max-width: 800px; margin: 0 auto; text-align: center; }
            .title { font-size: 3em; color: #ff6600; margin-bottom: 20px; }
            .subtitle { font-size: 1.2em; margin-bottom: 40px; color: #ccc; }
            .buttons { margin: 20px 0; }
            .btn { display: inline-block; padding: 15px 30px; margin: 10px; text-decoration: none; 
                   background: #ff6600; color: white; border-radius: 5px; font-size: 1.1em; }
            .btn:hover { background: #ff8833; }
            .features { text-align: left; margin-top: 40px; }
            .feature { margin: 15px 0; padding: 10px; background: #333; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="title">OUTWAR CLONE</h1>
            <p class="subtitle">Enter the sci-fi MMORPG universe. Battle, explore, and dominate!</p>
            
            <div class="buttons">
                <a href="/login" class="btn">LOGIN</a>
                <a href="/register" class="btn">REGISTER</a>
            </div>
            
            <div class="features">
                <div class="feature">
                    <h3>⚔️ Combat System</h3>
                    <p>Engage in PvP and PvE combat with complex damage calculations</p>
                </div>
                <div class="feature">
                    <h3>🏆 Character Classes</h3>
                    <p>Choose from Gangster, Monster, or Pop Star classes, each with unique bonuses</p>
                </div>
                <div class="feature">
                    <h3>🛡️ Equipment System</h3>
                    <p>Collect and equip items across 10 equipment slots with rarity tiers</p>
                </div>
                <div class="feature">
                    <h3>🌍 World Exploration</h3>
                    <p>Navigate through Diamond City and dimensional areas</p>
                </div>
                <div class="feature">
                    <h3>👥 Crew System</h3>
                    <p>Join crews, share resources, and participate in group activities</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def login_page(request: web_request.Request):
    """Login form"""
    error = request.query.get('error', '')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Outwar Clone</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }}
            .container {{ max-width: 400px; margin: 100px auto; padding: 30px; background: #333; border-radius: 10px; }}
            .title {{ text-align: center; color: #ff6600; margin-bottom: 30px; }}
            .form-group {{ margin: 20px 0; }}
            label {{ display: block; margin-bottom: 5px; }}
            input {{ width: 100%; padding: 10px; border: none; border-radius: 5px; background: #555; color: white; }}
            .btn {{ width: 100%; padding: 15px; background: #ff6600; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 1.1em; }}
            .btn:hover {{ background: #ff8833; }}
            .error {{ color: #ff4444; text-align: center; margin: 10px 0; }}
            .links {{ text-align: center; margin-top: 20px; }}
            .links a {{ color: #ff6600; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2 class="title">LOGIN</h2>
            
            {f'<div class="error">{error}</div>' if error else ''}
            
            <form method="post">
                <div class="form-group">
                    <label>Username:</label>
                    <input type="text" name="username" required>
                </div>
                <div class="form-group">
                    <label>Password:</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit" class="btn">LOGIN</button>
            </form>
            
            <div class="links">
                <a href="/register">Don't have an account? Register</a><br>
                <a href="/">Back to Home</a>
            </div>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def login(request: web_request.Request):
    """Process login"""
    data = await request.post()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        raise web.HTTPFound('/login?error=Please enter username and password')
    
    try:
        database = await get_db()
        
        # Use the database's simple execute method
        user = await database.execute_query('get_account_by_username', username=username)
        
        if not user or not verify_password(password, user['password_hash']):
            raise web.HTTPFound('/login?error=Invalid username or password')
        
        # Create simple session
        session = await aiohttp_session.get_session(request)
        session['user_id'] = user['id']
        session['username'] = user['username']
        
        raise web.HTTPFound('/characters')
        
    except web.HTTPFound:
        # Re-raise HTTP redirects
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise web.HTTPFound('/login?error=Login failed')

async def register_page(request: web_request.Request):
    """Registration form"""
    error = request.query.get('error', '')
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Register - Outwar Clone</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }}
            .container {{ max-width: 400px; margin: 100px auto; padding: 30px; background: #333; border-radius: 10px; }}
            .title {{ text-align: center; color: #ff6600; margin-bottom: 30px; }}
            .form-group {{ margin: 20px 0; }}
            label {{ display: block; margin-bottom: 5px; }}
            input {{ width: 100%; padding: 10px; border: none; border-radius: 5px; background: #555; color: white; }}
            .btn {{ width: 100%; padding: 15px; background: #ff6600; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 1.1em; }}
            .btn:hover {{ background: #ff8833; }}
            .error {{ color: #ff4444; text-align: center; margin: 10px 0; }}
            .links {{ text-align: center; margin-top: 20px; }}
            .links a {{ color: #ff6600; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2 class="title">REGISTER</h2>
            
            {f'<div class="error">{error}</div>' if error else ''}
            
            <form method="post">
                <div class="form-group">
                    <label>Username:</label>
                    <input type="text" name="username" required minlength="3" maxlength="20">
                </div>
                <div class="form-group">
                    <label>Email (optional):</label>
                    <input type="email" name="email">
                </div>
                <div class="form-group">
                    <label>Password:</label>
                    <input type="password" name="password" required minlength="6">
                </div>
                <div class="form-group">
                    <label>Confirm Password:</label>
                    <input type="password" name="confirm_password" required>
                </div>
                <button type="submit" class="btn">REGISTER</button>
            </form>
            
            <div class="links">
                <a href="/login">Already have an account? Login</a><br>
                <a href="/">Back to Home</a>
            </div>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def register(request: web_request.Request):
    """Process registration"""
    data = await request.post()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')
    
    # Validation
    if not username or len(username) < 3:
        raise web.HTTPFound('/register?error=Username must be at least 3 characters')
    
    if not password or len(password) < 6:
        raise web.HTTPFound('/register?error=Password must be at least 6 characters')
    
    if password != confirm_password:
        raise web.HTTPFound('/register?error=Passwords do not match')
    
    # Hash password
    pwd_hash, salt = hash_password(password)
    password_hash = f"{pwd_hash}:{salt}"
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        try:
            # Check if username exists
            existing_user = await database.queries.get_account_by_username(conn, username=username)
            if existing_user:
                raise web.HTTPFound('/register?error=Username already exists')
            
            # Create account
            await database.queries.create_account(conn, username=username, password_hash=password_hash, email=email or None)
            await conn.commit()
            
        except web.HTTPFound:
            # Re-raise HTTP redirects
            raise
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise web.HTTPFound('/register?error=Username or email already exists')
            raise web.HTTPFound('/register?error=Registration failed')
    
    # Success - redirect to login
    raise web.HTTPFound('/login?success=Account created successfully')

async def logout(request: web_request.Request):
    """Process logout"""
    session = await aiohttp_session.get_session(request)
    session_id = session.get('session_id')
    
    if session_id:
        database = await get_db()
        async with await database.get_connection() as conn:
            await database.queries.delete_session(conn, session_id=session_id)
            await conn.commit()
    
    session.clear()
    raise web.HTTPFound('/')