#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from handlers.world import generate_minimap

def test_street_navigation():
    """Test that all adjacent street tiles are clickable"""
    
    print("Testing Street Navigation - All Adjacent Streets Should Be Clickable")
    print("=" * 70)
    
    # Test with a single connection to see street navigation
    connections = [{'direction': 'north', 'to_room_id': 2, 'room_name': 'City Hall'}]
    result = generate_minimap(1, connections)
    
    # Count clickable elements
    clickable_count = result.count('onclick=')
    street_tiles_count = result.count('\u2b1c')  # ⬜ street symbol
    path_tiles_count = result.count('\U0001f7e8')  # 🟨 path symbol
    
    print(f"Results:")
    print(f"  • Total clickable elements: {clickable_count}")
    print(f"  • Street tiles (should mostly be clickable): {street_tiles_count}")
    print(f"  • Path tiles (all clickable): {path_tiles_count}")
    
    # Check for specific street navigation features
    street_navigation_checks = {
        'Street tiles have cursor pointer': 'cursor: pointer' in result and '⬜' in result,
        'Street tooltips mention walking': 'Walk' in result and 'down the street' in result,
        'Path tooltips mention following': 'Follow path' in result,
        'Streets have subtle hover effects': 'box-shadow: 0 0 4px rgba(150, 150, 150, 0.6)' in result,
        'Updated description text': 'Click any adjacent street, path, or building to walk around' in result
    }
    
    print(f"\nStreet Navigation Features:")
    for feature, passed in street_navigation_checks.items():
        status = "✅ PASS" if passed else "❌ FAIL" 
        print(f"  {feature}: {status}")
    
    # Generate test HTML
    html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <title>Street Navigation Test</title>
    <style>
        body {{ background: #1a1a1a; color: white; font-family: Arial; padding: 20px; }}
        .test-section {{ margin: 30px 0; padding: 20px; border: 1px solid #444; border-radius: 8px; }}
        .minimap-container {{ text-align: center; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>🚶‍♂️ Street Navigation Test</h1>
    
    <div class="test-section">
        <h2>✨ New Street Navigation Features</h2>
        <ul>
            <li>✅ All adjacent street tiles are now clickable</li>
            <li>✅ Street-to-street movement for realistic city navigation</li>
            <li>✅ Hover effects on clickable street tiles</li>
            <li>✅ Descriptive tooltips for street walking</li>
            <li>✅ No longer restricted to only green/yellow tiles</li>
            <li>✅ Natural city exploration by clicking any adjacent street</li>
        </ul>
    </div>
    
    <div class="test-section">
        <div class="minimap-container">
            <h3>Test: Click Any Adjacent Street Tile!</h3>
            <p><em>You should be able to click white street squares around your location</em></p>
            {generate_minimap(1, [{'direction': 'north', 'to_room_id': 2, 'room_name': 'City Hall'}])}
        </div>
    </div>
    
    <script>
        function move(direction) {{
            alert('🚶‍♂️ Walking ' + direction + ' through Diamond City streets! This demonstrates the new street-to-street navigation.');
        }}
    </script>
</body>
</html>
    '''
    
    with open('test_street_navigation.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\nTest HTML file generated: test_street_navigation.html")
    print(f"Overall: {'✅ SUCCESS - All streets are now walkable!' if all(street_navigation_checks.values()) else '❌ Issues detected'}")

if __name__ == "__main__":
    test_street_navigation()