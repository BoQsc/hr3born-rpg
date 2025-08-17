from aiohttp import web, web_request
import random

from database import get_db
from handlers.auth import require_login
from handlers.character import get_current_character

async def supplies_main(request: web_request.Request):
    """Supplies shop interface"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    # Define supply categories and items
    supply_items = {
        'consumables': [
            {'id': 'health_potion_small', 'name': 'Small Health Potion', 'price': 500, 'description': 'Restores 100 HP instantly', 'icon': '🧪', 'effect': '+100 HP'},
            {'id': 'health_potion_large', 'name': 'Large Health Potion', 'price': 2000, 'description': 'Restores 500 HP instantly', 'icon': '🧪', 'effect': '+500 HP'},
            {'id': 'rage_potion', 'name': 'Rage Potion', 'price': 1000, 'description': 'Restores 50 Rage instantly', 'icon': '⚡', 'effect': '+50 Rage'},
            {'id': 'energy_drink', 'name': 'Energy Drink', 'price': 750, 'description': 'Increases energy for 1 hour', 'icon': '🥤', 'effect': '+Energy Boost'},
        ],
        'equipment': [
            {'id': 'repair_kit', 'name': 'Equipment Repair Kit', 'price': 3000, 'description': 'Repairs all equipped items', 'icon': '🔧', 'effect': 'Repair All'},
            {'id': 'upgrade_stone', 'name': 'Upgrade Stone', 'price': 5000, 'description': 'Enhances equipment stats', 'icon': '💎', 'effect': '+5% Stats'},
            {'id': 'enchant_scroll', 'name': 'Enchantment Scroll', 'price': 7500, 'description': 'Adds magical properties', 'icon': '📜', 'effect': 'Random Enchant'},
        ],
        'special': [
            {'id': 'exp_boost', 'name': 'Experience Booster', 'price': 10000, 'description': '2x EXP for 2 hours', 'icon': '📈', 'effect': '2x EXP (2h)'},
            {'id': 'gold_boost', 'name': 'Gold Fortune', 'price': 8000, 'description': '1.5x Gold for 2 hours', 'icon': '💰', 'effect': '1.5x Gold (2h)'},
            {'id': 'teleport_scroll', 'name': 'Teleport Scroll', 'price': 2500, 'description': 'Instantly return to town', 'icon': '🌀', 'effect': 'Instant Travel'},
        ]
    }
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Supplies Shop - Outwar</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: Arial, sans-serif; background: #1a1a1a; color: #ffffff; }}
            
            /* Shop Background */
            .shop-bg {{ 
                background: linear-gradient(135deg, #2d1a0a 0%, #4a2d1a 50%, #2d1a0a 100%);
                min-height: 100vh;
                background-image: 
                    radial-gradient(circle at 20% 50%, rgba(255, 165, 0, 0.1) 0%, transparent 50%),
                    radial-gradient(circle at 80% 30%, rgba(139, 69, 19, 0.1) 0%, transparent 50%);
            }}
            
            /* Top Navigation */
            .top-nav {{ background: linear-gradient(180deg, #000 0%, #333 100%); height: 40px; display: flex; }}
            .nav-tab {{ padding: 8px 20px; color: #ccc; cursor: pointer; border-radius: 8px 8px 0 0; }}
            .nav-tab.active {{ background: linear-gradient(180deg, #ff8c00 0%, #ffd700 100%); color: #000; font-weight: bold; }}
            
            /* Header Status Bar */
            .status-bar {{ background: linear-gradient(180deg, #ffd700 0%, #ff8c00 100%); height: 30px; padding: 5px 15px; display: flex; justify-content: space-between; align-items: center; color: #000; font-size: 11px; font-weight: bold; }}
            .status-left {{ display: flex; gap: 15px; align-items: center; }}
            .status-right {{ display: flex; gap: 10px; }}
            .status-icon {{ width: 16px; height: 16px; border-radius: 50%; background: #333; }}
            
            /* Main Container */
            .main-container {{ padding: 20px; max-width: 1200px; margin: 0 auto; }}
            
            /* Shop Header */
            .shop-header {{ background: rgba(45, 45, 45, 0.9); border: 1px solid #ff8c00; border-radius: 8px; padding: 20px; margin-bottom: 20px; text-align: center; }}
            .shop-title {{ color: #ff8c00; font-size: 32px; font-weight: bold; margin-bottom: 10px; }}
            .shop-subtitle {{ color: #ffd700; font-size: 16px; margin-bottom: 15px; }}
            .gold-display {{ color: #ffd700; font-size: 20px; font-weight: bold; }}
            
            /* Category Tabs */
            .category-tabs {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 30px; }}
            .category-tab {{ padding: 12px 24px; background: #444; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; transition: all 0.3s; }}
            .category-tab.active {{ background: #ff8c00; color: #000; font-weight: bold; }}
            .category-tab:hover {{ background: #555; }}
            .category-tab.active:hover {{ background: #ffaa00; }}
            
            /* Items Grid */
            .items-container {{ background: rgba(45, 45, 45, 0.9); border: 1px solid #ff8c00; border-radius: 12px; padding: 25px; }}
            .items-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }}
            
            /* Item Cards */
            .item-card {{ 
                background: #333;
                border: 2px solid #555;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                transition: all 0.3s;
            }}
            .item-card:hover {{ border-color: #ff8c00; transform: translateY(-3px); }}
            
            .item-icon {{ font-size: 48px; margin-bottom: 15px; }}
            .item-name {{ font-size: 18px; font-weight: bold; color: #ffd700; margin-bottom: 10px; }}
            .item-description {{ color: #ccc; margin-bottom: 15px; font-size: 13px; line-height: 1.4; }}
            .item-effect {{ 
                background: rgba(0, 255, 0, 0.1);
                border: 1px solid #00aa00;
                padding: 8px;
                border-radius: 5px;
                color: #00ff00;
                font-size: 12px;
                margin-bottom: 15px;
            }}
            .item-price {{ color: #ffd700; font-size: 20px; font-weight: bold; margin-bottom: 15px; }}
            
            .buy-btn {{ 
                width: 100%;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                background: linear-gradient(45deg, #ff8c00, #ffaa00);
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.3s;
            }}
            .buy-btn:hover {{ background: linear-gradient(45deg, #ffaa00, #ffcc00); }}
            .buy-btn:disabled {{ background: #666; cursor: not-allowed; }}
            
            /* Shop Keeper */
            .shopkeeper {{ 
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 80px;
                height: 80px;
                background: linear-gradient(45deg, #8b4513, #cd853f);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
                border: 3px solid #ffd700;
                cursor: pointer;
                transition: all 0.3s;
            }}
            .shopkeeper:hover {{ transform: scale(1.1); }}
            
            /* Quantity Selector */
            .quantity-controls {{ display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 15px; }}
            .quantity-btn {{ 
                width: 30px;
                height: 30px;
                background: #555;
                color: white;
                border: none;
                border-radius: 50%;
                cursor: pointer;
                font-weight: bold;
            }}
            .quantity-input {{ 
                width: 60px;
                text-align: center;
                padding: 5px;
                background: #444;
                border: 1px solid #666;
                border-radius: 5px;
                color: white;
            }}
        </style>
    </head>
    <body class="shop-bg">
        <!-- Top Navigation -->
        <div class="top-nav">
            <div class="nav-tab" onclick="window.location.href='/game'">Explore World</div>
            <div class="nav-tab" onclick="window.location.href='/challenges'">Dungeons</div>
            <div class="nav-tab" onclick="window.location.href='/challenges'">Challenges</div>
            <div class="nav-tab" onclick="window.location.href='/marketplace'">Marketplace</div>
            <div class="nav-tab" onclick="window.location.href='/rankings'">Rankings</div>
            <div class="nav-tab" onclick="window.location.href='/casino'">Casino</div>
        </div>
        
        <!-- Header Status Bar -->
        <div class="status-bar">
            <div class="status-left">
                <span>{character.name}</span>
                <span>🔴</span>
                <span>🕐 {character.id % 12 + 1}:{(character.id * 7) % 60:02d}am</span>
                <span>Level: {character.level}</span>
                <span>EXP: {character.experience:,}</span>
                <span>RAGE: {character.rage_current}</span>
            </div>
            <div class="status-right">
                <div class="status-icon"></div>
                <div class="status-icon"></div>
                <div class="status-icon"></div>
                <div class="status-icon"></div>
            </div>
        </div>
        
        <!-- Main Container -->
        <div class="main-container">
            <!-- Shop Header -->
            <div class="shop-header">
                <div class="shop-title">🏪 GENERAL SUPPLIES</div>
                <div class="shop-subtitle">Essential items for your adventures • Quality guaranteed</div>
                <div class="gold-display">💰 Your Gold: {character.gold:,}g</div>
            </div>
            
            <!-- Category Tabs -->
            <div class="category-tabs">
                <button class="category-tab active" onclick="switchCategory('consumables')">🧪 Consumables</button>
                <button class="category-tab" onclick="switchCategory('equipment')">🔧 Equipment</button>
                <button class="category-tab" onclick="switchCategory('special')">⭐ Special Items</button>
            </div>
            
            <!-- Items Container -->
            <div class="items-container">
                <div id="consumables" class="items-grid">
                    {generate_item_cards(supply_items['consumables'], character)}
                </div>
                <div id="equipment" class="items-grid" style="display: none;">
                    {generate_item_cards(supply_items['equipment'], character)}
                </div>
                <div id="special" class="items-grid" style="display: none;">
                    {generate_item_cards(supply_items['special'], character)}
                </div>
            </div>
        </div>
        
        <!-- Shop Keeper -->
        <div class="shopkeeper" onclick="showShopkeeperDialog()">👨‍💼</div>
        
        <script>
        function switchCategory(category) {{
            // Hide all categories
            document.querySelectorAll('.items-grid').forEach(grid => {{
                grid.style.display = 'none';
            }});
            
            // Remove active class from all tabs
            document.querySelectorAll('.category-tab').forEach(tab => {{
                tab.classList.remove('active');
            }});
            
            // Show selected category
            document.getElementById(category).style.display = 'grid';
            
            // Add active class to clicked tab
            event.target.classList.add('active');
        }}
        
        function adjustQuantity(itemId, delta) {{
            const input = document.getElementById(`qty-${{itemId}}`);
            const current = parseInt(input.value) || 1;
            const newValue = Math.max(1, Math.min(99, current + delta));
            input.value = newValue;
            updateTotalPrice(itemId);
        }}
        
        function updateTotalPrice(itemId) {{
            const quantity = parseInt(document.getElementById(`qty-${{itemId}}`).value) || 1;
            const basePrice = parseInt(document.getElementById(`price-${{itemId}}`).dataset.basePrice);
            const totalPrice = basePrice * quantity;
            document.getElementById(`total-${{itemId}}`).textContent = totalPrice.toLocaleString() + 'g';
        }}
        
        function buyItem(itemId, itemName, basePrice) {{
            const quantity = parseInt(document.getElementById(`qty-${{itemId}}`).value) || 1;
            const totalPrice = basePrice * quantity;
            
            if (confirm(`Buy ${{quantity}}x ${{itemName}} for ${{totalPrice.toLocaleString()}}g?`)) {{
                fetch('/supplies/buy', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        item_id: itemId,
                        quantity: quantity,
                        total_price: totalPrice
                    }})
                }})
                .then(response => {{
                    if (response.ok) {{
                        alert(`Successfully purchased ${{quantity}}x ${{itemName}}!`);
                        location.reload();
                    }} else {{
                        alert('Purchase failed. You may not have enough gold.');
                    }}
                }});
            }}
        }}
        
        function showShopkeeperDialog() {{
            alert('👨‍💼 Shopkeeper: "Welcome to my shop! I have the finest supplies in all the land. Everything you need for your adventures!"');
        }}
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

def generate_item_cards(items, character):
    """Generate HTML for item cards"""
    cards_html = ""
    for item in items:
        can_afford = character.gold >= item['price']
        
        cards_html += f"""
        <div class="item-card">
            <div class="item-icon">{item['icon']}</div>
            <div class="item-name">{item['name']}</div>
            <div class="item-description">{item['description']}</div>
            <div class="item-effect">{item['effect']}</div>
            
            <div class="quantity-controls">
                <button class="quantity-btn" onclick="adjustQuantity('{item['id']}', -1)">-</button>
                <input type="number" class="quantity-input" id="qty-{item['id']}" value="1" min="1" max="99" onchange="updateTotalPrice('{item['id']}')">
                <button class="quantity-btn" onclick="adjustQuantity('{item['id']}', 1)">+</button>
            </div>
            
            <div class="item-price">
                <span id="total-{item['id']}">{item['price']:,}g</span>
                <span id="price-{item['id']}" data-base-price="{item['price']}" style="display: none;"></span>
            </div>
            
            <button class="buy-btn" {"disabled" if not can_afford else ""} onclick="buyItem('{item['id']}', '{item['name']}', {item['price']})">
                {"INSUFFICIENT GOLD" if not can_afford else "BUY ITEM"}
            </button>
        </div>
        """
    
    return cards_html

async def buy_supplies(request: web_request.Request):
    """Handle supply purchases"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        return web.Response(text="Character not found", status=400)
    
    try:
        data = await request.json()
        item_id = data.get('item_id')
        quantity = int(data.get('quantity', 1))
        total_price = int(data.get('total_price', 0))
        
        # Validate purchase
        if character.gold < total_price:
            return web.Response(text="Insufficient gold", status=400)
        
        if quantity < 1 or quantity > 99:
            return web.Response(text="Invalid quantity", status=400)
        
        # Update character gold
        database = await get_db()
        async with database.get_connection_context() as conn:
            await conn.execute('UPDATE characters SET gold = gold - ? WHERE id = ?', 
                             (total_price, character.id))
            await conn.commit()
        
        return web.Response(text="Purchase successful")
        
    except Exception as e:
        return web.Response(text=f"Purchase failed: {e}", status=400)