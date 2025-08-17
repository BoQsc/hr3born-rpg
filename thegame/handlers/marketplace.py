from aiohttp import web, web_request
from typing import Dict, List, Optional
import json

from database import get_db
from handlers.auth import require_login
from handlers.character import get_current_character

async def marketplace_main(request: web_request.Request):
    """Main marketplace interface - Outwar style"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    # Get filter parameters
    item_type = request.query.get('type', 'all')
    min_level = request.query.get('min_level', '1')
    max_level = request.query.get('max_level', '95')
    sort_by = request.query.get('sort', 'name')
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        # Get marketplace listings (using character inventory as sample listings)
        if item_type == 'all':
            listings_query = '''
                SELECT ci.id as listing_id, ci.item_id, ci.quantity, ci.transfers_remaining,
                       i.name, i.level_requirement, i.attack, i.hit_points,
                       i.fire_damage, i.kinetic_damage, i.arcane_damage, i.holy_damage, i.shadow_damage,
                       i.chaos_damage, i.vile_damage,
                       es.name as slot_name, ir.name as rarity_name, ir.color,
                       c.name as seller_name, c.level as seller_level,
                       (i.attack + i.hit_points + i.fire_damage + i.kinetic_damage + i.arcane_damage + i.holy_damage + i.shadow_damage + i.chaos_damage + i.vile_damage) * ir.power_multiplier as estimated_price
                FROM character_inventory ci
                JOIN items i ON ci.item_id = i.id
                JOIN equipment_slots es ON i.slot_id = es.id
                JOIN item_rarities ir ON i.rarity_id = ir.id
                JOIN characters c ON ci.character_id = c.id
                WHERE i.level_requirement >= :min_level AND i.level_requirement <= :max_level
                ORDER BY estimated_price DESC
                LIMIT 50
            '''
        else:
            listings_query = '''
                SELECT ci.id as listing_id, ci.item_id, ci.quantity, ci.transfers_remaining,
                       i.name, i.level_requirement, i.attack, i.hit_points,
                       i.fire_damage, i.kinetic_damage, i.arcane_damage, i.holy_damage, i.shadow_damage,
                       i.chaos_damage, i.vile_damage,
                       es.name as slot_name, ir.name as rarity_name, ir.color,
                       c.name as seller_name, c.level as seller_level,
                       (i.attack + i.hit_points + i.fire_damage + i.kinetic_damage + i.arcane_damage + i.holy_damage + i.shadow_damage + i.chaos_damage + i.vile_damage) * ir.power_multiplier as estimated_price
                FROM character_inventory ci
                JOIN items i ON ci.item_id = i.id
                JOIN equipment_slots es ON i.slot_id = es.id
                JOIN item_rarities ir ON i.rarity_id = ir.id
                JOIN characters c ON ci.character_id = c.id
                WHERE es.name = :item_type AND i.level_requirement >= :min_level AND i.level_requirement <= :max_level
                ORDER BY estimated_price DESC
                LIMIT 50
            '''
        
        listings = await conn.execute(listings_query, {
            'item_type': item_type,
            'min_level': int(min_level),
            'max_level': int(max_level)
        })
        listings = await listings.fetchall()
    
    # Build listings HTML
    listings_html = build_marketplace_listings(listings, character)
    
    # Build filter controls
    filter_controls = build_filter_controls(item_type, min_level, max_level, sort_by)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Marketplace - Outwar</title>
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
            
            /* Main Container */
            .main-container {{ padding: 20px; }}
            
            /* Marketplace Header */
            .marketplace-header {{ background: #2d2d2d; border: 1px solid #555; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
            .marketplace-title {{ color: #4169e1; font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 15px; }}
            .marketplace-nav {{ display: flex; justify-content: center; gap: 15px; margin-bottom: 15px; }}
            .marketplace-tab {{ padding: 8px 16px; background: #444; color: white; border: none; border-radius: 5px; cursor: pointer; }}
            .marketplace-tab.active {{ background: #4169e1; }}
            .marketplace-tab:hover {{ background: #555; }}
            .marketplace-tab.active:hover {{ background: #5578ff; }}
            
            /* Filter Controls */
            .filter-controls {{ background: #333; border: 1px solid #555; border-radius: 5px; padding: 15px; margin-bottom: 20px; }}
            .filter-row {{ display: flex; gap: 15px; align-items: center; margin-bottom: 10px; }}
            .filter-label {{ color: #ccc; min-width: 80px; }}
            .filter-input {{ padding: 5px; background: #444; border: 1px solid #666; border-radius: 3px; color: white; }}
            .filter-select {{ padding: 5px; background: #444; border: 1px solid #666; border-radius: 3px; color: white; }}
            .filter-btn {{ padding: 8px 15px; background: #4169e1; color: white; border: none; border-radius: 5px; cursor: pointer; }}
            .filter-btn:hover {{ background: #5578ff; }}
            
            /* Listings Grid */
            .listings-container {{ background: #2d2d2d; border: 1px solid #555; border-radius: 8px; padding: 20px; }}
            .listings-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
            .listings-title {{ font-weight: bold; }}
            .listings-count {{ color: #ccc; font-size: 12px; }}
            
            .listings-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 15px; }}
            .listing-card {{ background: #333; border: 2px solid #555; border-radius: 8px; padding: 15px; }}
            .listing-card:hover {{ border-color: #777; }}
            
            .listing-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }}
            .listing-item-name {{ font-weight: bold; color: white; }}
            .listing-rarity {{ font-size: 10px; padding: 2px 6px; border-radius: 3px; }}
            .listing-price {{ color: #ffd700; font-weight: bold; font-size: 16px; }}
            
            .listing-stats {{ margin: 8px 0; font-size: 11px; }}
            .stat-line {{ margin: 2px 0; }}
            .stat-positive {{ color: #32cd32; }}
            .stat-elemental {{ color: #ff8c00; }}
            
            .listing-meta {{ display: flex; justify-content: space-between; align-items: center; margin-top: 10px; font-size: 10px; color: #ccc; }}
            .listing-seller {{ color: #88ccff; }}
            .listing-level {{ color: #ccc; }}
            
            .listing-actions {{ display: flex; gap: 8px; margin-top: 10px; }}
            .buy-btn {{ padding: 6px 12px; background: #00aa00; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; }}
            .buy-btn:hover {{ background: #00cc00; }}
            .buy-btn:disabled {{ background: #666; cursor: not-allowed; }}
            .bid-btn {{ padding: 6px 12px; background: #ff8800; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 11px; }}
            .bid-btn:hover {{ background: #ffaa00; }}
            
            /* Search Panel */
            .search-panel {{ background: #333; border: 1px solid #555; border-radius: 5px; padding: 15px; margin-bottom: 20px; }}
            .search-input {{ width: 300px; padding: 8px; background: #444; border: 1px solid #666; border-radius: 3px; color: white; }}
            .search-btn {{ padding: 8px 15px; background: #4169e1; color: white; border: none; border-radius: 3px; cursor: pointer; margin-left: 10px; }}
            
            /* No listings message */
            .no-listings {{ text-align: center; color: #ccc; padding: 40px; font-style: italic; }}
        </style>
    </head>
    <body>
        <!-- Top Navigation -->
        <div class="top-nav">
            <div class="nav-tab" onclick="window.location.href='/game'">Explore World</div>
            <div class="nav-tab" onclick="window.location.href='/challenges'">Dungeons</div>
            <div class="nav-tab" onclick="window.location.href='/challenges'">Challenges</div>
            <div class="nav-tab active">Marketplace</div>
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
                <span>GOLD: {character.gold:,}</span>
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
            <!-- Marketplace Header -->
            <div class="marketplace-header">
                <div class="marketplace-title">🛒 MARKETPLACE</div>
                <div class="marketplace-nav">
                    <button class="marketplace-tab active">Browse Items</button>
                    <button class="marketplace-tab">My Listings</button>
                    <button class="marketplace-tab">Sell Items</button>
                    <button class="marketplace-tab">Purchase History</button>
                    <button class="marketplace-tab">Auction House</button>
                </div>
                <div style="text-align: center; font-size: 12px; color: #ccc;">
                    Trade items with other players • Secure transactions • No scams
                </div>
            </div>
            
            <!-- Search Panel -->
            <div class="search-panel">
                <input type="text" class="search-input" placeholder="Search for items by name..." id="searchInput">
                <button class="search-btn" onclick="searchItems()">SEARCH</button>
                <button class="search-btn" onclick="clearSearch()" style="background: #666;">CLEAR</button>
            </div>
            
            <!-- Filter Controls -->
            <div class="filter-controls">
                {filter_controls}
            </div>
            
            <!-- Listings Container -->
            <div class="listings-container">
                <div class="listings-header">
                    <div class="listings-title">Available Items</div>
                    <div class="listings-count">{len(listings)} items found</div>
                </div>
                
                <div class="listings-grid">
                    {listings_html}
                </div>
            </div>
        </div>
        
        <script>
        function buyItem(listingId, price, itemName) {{
            if (confirm(`Purchase ${{itemName}} for ${{price:,}} gold?`)) {{
                fetch('/marketplace/buy/' + listingId, {{method: 'POST'}})
                .then(response => {{
                    if (response.ok) {{
                        alert('Purchase successful!');
                        location.reload();
                    }} else {{
                        alert('Purchase failed. You may not have enough gold.');
                    }}
                }});
            }}
        }}
        
        function placeBid(listingId, currentPrice, itemName) {{
            const bidAmount = prompt(`Enter your bid for ${{itemName}} (current: ${{currentPrice:,}} gold):`);
            if (bidAmount && !isNaN(bidAmount) && parseInt(bidAmount) > currentPrice) {{
                fetch('/marketplace/bid/' + listingId, {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{bid: parseInt(bidAmount)}})
                }})
                .then(response => {{
                    if (response.ok) {{
                        alert('Bid placed successfully!');
                        location.reload();
                    }} else {{
                        alert('Bid failed.');
                    }}
                }});
            }}
        }}
        
        function applyFilters() {{
            const type = document.getElementById('typeFilter').value;
            const minLevel = document.getElementById('minLevel').value;
            const maxLevel = document.getElementById('maxLevel').value;
            const sort = document.getElementById('sortBy').value;
            
            const params = new URLSearchParams({{
                type: type,
                min_level: minLevel,
                max_level: maxLevel,
                sort: sort
            }});
            
            window.location.href = '/marketplace?' + params.toString();
        }}
        
        function searchItems() {{
            const query = document.getElementById('searchInput').value;
            if (query.trim()) {{
                window.location.href = '/marketplace?search=' + encodeURIComponent(query);
            }}
        }}
        
        function clearSearch() {{
            document.getElementById('searchInput').value = '';
            window.location.href = '/marketplace';
        }}
        </script>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

def build_marketplace_listings(listings, character):
    """Build marketplace listings HTML"""
    if not listings:
        return '<div class="no-listings">No items available at the moment.<br>Check back later or adjust your filters.</div>'
    
    listings_html = ""
    for listing in listings:
        # Calculate estimated price based on item power
        estimated_price = int(listing['estimated_price'] * 100)
        
        # Build stats display
        stats_html = ""
        if listing['attack'] > 0:
            stats_html += f'<div class="stat-line stat-positive">+{listing["attack"]} ATK</div>'
        if listing['hit_points'] > 0:
            stats_html += f'<div class="stat-line stat-positive">+{listing["hit_points"]} HP</div>'
        
        # Add elemental damages
        elemental_stats = []
        if listing['fire_damage'] > 0:
            elemental_stats.append(f'Fire +{listing["fire_damage"]}')
        if listing['kinetic_damage'] > 0:
            elemental_stats.append(f'Kinetic +{listing["kinetic_damage"]}')
        if listing['arcane_damage'] > 0:
            elemental_stats.append(f'Arcane +{listing["arcane_damage"]}')
        if listing['holy_damage'] > 0:
            elemental_stats.append(f'Holy +{listing["holy_damage"]}')
        if listing['shadow_damage'] > 0:
            elemental_stats.append(f'Shadow +{listing["shadow_damage"]}')
        if listing['chaos_damage'] > 0:
            elemental_stats.append(f'Chaos +{listing["chaos_damage"]}')
        if listing['vile_damage'] > 0:
            elemental_stats.append(f'Vile +{listing["vile_damage"]}')
        
        if elemental_stats:
            stats_html += f'<div class="stat-line stat-elemental">{", ".join(elemental_stats)}</div>'
        
        # Check if character can afford
        can_afford = character.gold >= estimated_price
        
        # Determine if it's own listing
        own_listing = listing['seller_name'] == character.name
        
        listings_html += f"""
        <div class="listing-card">
            <div class="listing-header">
                <div>
                    <div class="listing-item-name" style="color: {listing['color']}">{listing['name']}</div>
                    <span class="listing-rarity" style="background: {listing['color']}; color: #000;">{listing['rarity_name']}</span>
                </div>
                <div class="listing-price">{estimated_price:,}g</div>
            </div>
            
            <div class="listing-stats">
                <div class="stat-line">Level Req: {listing['level_requirement']}</div>
                <div class="stat-line">Slot: {listing['slot_name'].title()}</div>
                {stats_html}
            </div>
            
            <div class="listing-meta">
                <div>
                    <span class="listing-seller">{listing['seller_name']}</span>
                    <span class="listing-level">(Lv{listing['seller_level']})</span>
                </div>
                <div>Transfers: {listing['transfers_remaining']}</div>
            </div>
            
            <div class="listing-actions">
                {'<button class="buy-btn" disabled>Your Item</button>' if own_listing else 
                 f'<button class="buy-btn" {"" if can_afford else "disabled"} onclick="buyItem({listing['listing_id']}, {estimated_price}, \'{listing['name']}\')">BUY NOW</button>'}
                {'<button class="bid-btn" disabled>Your Item</button>' if own_listing else
                 f'<button class="bid-btn" onclick="placeBid({listing['listing_id']}, {estimated_price}, \'{listing['name']}\')">PLACE BID</button>'}
            </div>
        </div>
        """
    
    return listings_html

def build_filter_controls(item_type, min_level, max_level, sort_by):
    """Build filter controls HTML"""
    item_types = [
        ('all', 'All Items'),
        ('weapon', 'Weapons'),
        ('head', 'Helmets'),
        ('chest', 'Chest Armor'),
        ('legs', 'Leg Armor'),
        ('boots', 'Boots'),
        ('shield', 'Shields'),
        ('accessory1', 'Accessories'),
        ('ring1', 'Rings')
    ]
    
    type_options = ""
    for value, label in item_types:
        selected = "selected" if value == item_type else ""
        type_options += f'<option value="{value}" {selected}>{label}</option>'
    
    return f"""
    <div class="filter-row">
        <span class="filter-label">Item Type:</span>
        <select class="filter-select" id="typeFilter">
            {type_options}
        </select>
        
        <span class="filter-label">Level Range:</span>
        <input type="number" class="filter-input" id="minLevel" value="{min_level}" min="1" max="95" style="width: 60px;">
        <span style="color: #ccc;">to</span>
        <input type="number" class="filter-input" id="maxLevel" value="{max_level}" min="1" max="95" style="width: 60px;">
        
        <span class="filter-label">Sort By:</span>
        <select class="filter-select" id="sortBy">
            <option value="name" {"selected" if sort_by == "name" else ""}>Name</option>
            <option value="price_low" {"selected" if sort_by == "price_low" else ""}>Price (Low to High)</option>
            <option value="price_high" {"selected" if sort_by == "price_high" else ""}>Price (High to Low)</option>
            <option value="level" {"selected" if sort_by == "level" else ""}>Level</option>
            <option value="newest" {"selected" if sort_by == "newest" else ""}>Newest</option>
        </select>
        
        <button class="filter-btn" onclick="applyFilters()">APPLY FILTERS</button>
    </div>
    """

async def buy_item(request: web_request.Request):
    """Buy an item from marketplace"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    listing_id = int(request.match_info['listing_id'])
    
    database = await get_db()
    async with database.get_connection_context() as conn:
        # Get listing details
        listing_query = await conn.execute('''
            SELECT ci.character_id, ci.item_id, ci.quantity,
                   i.name, (i.attack + i.hit_points + i.fire_damage + i.kinetic_damage + i.arcane_damage + i.holy_damage + i.shadow_damage + i.chaos_damage + i.vile_damage) * ir.power_multiplier * 100 as price
            FROM character_inventory ci
            JOIN items i ON ci.item_id = i.id
            JOIN item_rarities ir ON i.rarity_id = ir.id
            WHERE ci.id = :listing_id
        ''', {'listing_id': listing_id})
        listing = await listing_query.fetchone()
        
        if not listing:
            raise web.HTTPNotFound()
        
        price = int(listing['price'])
        
        # Check if buyer has enough gold
        if character.gold < price:
            return web.Response(text="Insufficient gold", status=400)
        
        # Check if trying to buy own item
        if listing['character_id'] == character.id:
            return web.Response(text="Cannot buy your own item", status=400)
        
        # Process transaction
        # Remove item from seller's inventory
        await conn.execute('DELETE FROM character_inventory WHERE id = :listing_id', {'listing_id': listing_id})
        
        # Add item to buyer's inventory
        await database.queries.add_to_inventory(conn, character_id=character.id, 
                                              item_id=listing['item_id'], quantity=1, transfers_remaining=10)
        
        # Transfer gold
        await conn.execute('UPDATE characters SET gold = gold - :price WHERE id = :buyer_id', 
                          {'price': price, 'buyer_id': character.id})
        await conn.execute('UPDATE characters SET gold = gold + :price WHERE id = :seller_id', 
                          {'price': price, 'seller_id': listing['character_id']})
        
        await conn.commit()
    
    return web.Response(text="Purchase successful")

async def sell_item(request: web_request.Request):
    """List item for sale"""
    await require_login(request)
    character = await get_current_character(request)
    
    if not character:
        raise web.HTTPFound('/characters')
    
    # This would implement selling interface
    # For now, redirect to main marketplace
    raise web.HTTPFound('/marketplace')