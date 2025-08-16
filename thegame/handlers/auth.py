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
        <title>Outwar - Login</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: Arial, sans-serif; background: #1a1a1a; color: #ffffff; }}
            
            /* Top Navigation */
            .top-nav {{ background: linear-gradient(180deg, #000 0%, #333 100%); height: 40px; display: flex; }}
            .nav-tab {{ padding: 8px 20px; color: #ccc; cursor: pointer; border-radius: 8px 8px 0 0; }}
            .nav-tab.active {{ background: linear-gradient(180deg, #ff8c00 0%, #ffd700 100%); color: #000; font-weight: bold; }}
            
            /* Header Status Bar */
            .status-bar {{ background: linear-gradient(180deg, #ffd700 0%, #ff8c00 100%); height: 30px; padding: 5px 15px; display: flex; justify-content: space-between; align-items: center; color: #000; font-size: 11px; font-weight: bold; }}
            .status-left {{ display: flex; gap: 15px; align-items: center; }}
            .status-right {{ display: flex; gap: 10px; }}
            .status-icon {{ width: 16px; height: 16px; border-radius: 50%; background: #333; }}
            
            /* Login Container */
            .login-container {{ padding: 50px 20px; max-width: 500px; margin: 0 auto; }}
            .login-panel {{ background: #2d2d2d; border: 1px solid #555; border-radius: 8px; padding: 40px; }}
            .login-title {{ text-align: center; font-size: 24px; color: #ffd700; margin-bottom: 30px; font-weight: bold; }}
            .outwar-logo {{ text-align: center; margin-bottom: 40px; }}
            .outwar-logo h1 {{ color: #ff8c00; font-size: 36px; text-shadow: 2px 2px 4px rgba(0,0,0,0.5); }}
            .outwar-logo p {{ color: #ccc; font-size: 14px; margin-top: 10px; }}
            
            /* Form Styling */
            .form-group {{ margin: 20px 0; }}
            .form-label {{ display: block; margin-bottom: 8px; color: #ccc; font-size: 12px; font-weight: bold; }}
            .form-input {{ width: 100%; padding: 12px 15px; background: #444; border: 1px solid #666; border-radius: 5px; color: white; font-size: 14px; }}
            .form-input:focus {{ outline: none; border-color: #ffd700; box-shadow: 0 0 5px rgba(255, 215, 0, 0.3); }}
            
            .login-btn {{ width: 100%; padding: 15px; background: linear-gradient(180deg, #ff6600 0%, #cc5500 100%); color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; text-transform: uppercase; }}
            .login-btn:hover {{ background: linear-gradient(180deg, #ff8800 0%, #dd6600 100%); }}
            
            /* Error Message */
            .error-message {{ background: #4a0000; border: 1px solid #ff4444; border-radius: 5px; padding: 10px; margin: 20px 0; text-align: center; color: #ff8888; }}
            
            /* Links */
            .auth-links {{ text-align: center; margin-top: 30px; }}
            .auth-links a {{ color: #88ccff; text-decoration: none; margin: 0 10px; font-size: 12px; }}
            .auth-links a:hover {{ color: #aaddff; text-decoration: underline; }}
            
            /* Footer */
            .auth-footer {{ text-align: center; margin-top: 40px; color: #666; font-size: 10px; }}
        </style>
    </head>
    <body>
        <!-- Top Navigation -->
        <div class="top-nav">
            <div class="nav-tab active">Login</div>
            <div class="nav-tab">Register</div>
            <div class="nav-tab">Explore World</div>
            <div class="nav-tab">Dungeons</div>
            <div class="nav-tab">Challenges</div>
            <div class="nav-tab">All docs</div>
            <div class="nav-tab">News</div>
            <div class="nav-tab">Discord</div>
        </div>
        
        <!-- Header Status Bar -->
        <div class="status-bar">
            <div class="status-left">
                <span>Welcome to Outwar</span>
                <span>🔴</span>
                <span>🕐 Login Required</span>
            </div>
            <div class="status-right">
                <div class="status-icon"></div>
                <div class="status-icon"></div>
                <div class="status-icon"></div>
                <div class="status-icon"></div>
            </div>
        </div>
        
        <!-- Login Container -->
        <div class="login-container">
            <div class="login-panel">
                <div class="outwar-logo">
                    <h1>OUTWAR</h1>
                    <p>The Ultimate MMORPG Experience</p>
                </div>
                
                <div class="login-title">Player Login</div>
                
                {f'<div class="error-message">{error}</div>' if error else ''}
                
                <form method="post">
                    <div class="form-group">
                        <label class="form-label">Username:</label>
                        <input type="text" name="username" class="form-input" required autocomplete="username">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Password:</label>
                        <input type="password" name="password" class="form-input" required autocomplete="current-password">
                    </div>
                    
                    <button type="submit" class="login-btn">Enter Game</button>
                </form>
                
                <div class="auth-links">
                    <a href="/register">Create New Character</a> |
                    <a href="/">Back to Homepage</a>
                </div>
                
                <div class="auth-footer">
                    Outwar Clone - Built with Python & aiohttp
                </div>
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