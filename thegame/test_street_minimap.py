#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from handlers.world import generate_minimap

def test_street_minimap():
    """Test the new street-based minimap generation"""
    
    print("Testing Street-Based Minimap Generation")
    print("=" * 50)
    
    # Test different connection scenarios
    test_cases = [
        {
            'name': 'Single West Connection',
            'room_id': 4, 
            'connections': [{'direction': 'west', 'to_room_id': 1, 'room_name': 'Diamond City Center'}]
        },
        {
            'name': 'Multiple Directions', 
            'room_id': 1,
            'connections': [
                {'direction': 'east', 'to_room_id': 4, 'room_name': 'Fight Arena'},
                {'direction': 'north', 'to_room_id': 2, 'room_name': 'City Hall'},
                {'direction': 'southwest', 'to_room_id': 3, 'room_name': 'Casino'}
            ]
        },
        {
            'name': 'All 8 Directions',
            'room_id': 5,
            'connections': [
                {'direction': 'north', 'to_room_id': 2, 'room_name': 'City Hall'},
                {'direction': 'south', 'to_room_id': 6, 'room_name': 'Arena'},
                {'direction': 'east', 'to_room_id': 7, 'room_name': 'Casino'}, 
                {'direction': 'west', 'to_room_id': 8, 'room_name': 'Marketplace'},
                {'direction': 'northeast', 'to_room_id': 9, 'room_name': 'Temple'},
                {'direction': 'northwest', 'to_room_id': 10, 'room_name': 'Barracks'},
                {'direction': 'southeast', 'to_room_id': 11, 'room_name': 'Tavern'},
                {'direction': 'southwest', 'to_room_id': 12, 'room_name': 'Bank'}
            ]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['name']}")
        print("-" * 40)
        
        result = generate_minimap(test_case['room_id'], test_case['connections'])
        
        # Check for key features
        checks = {
            'Grid Layout': 'display: grid' in result,
            'Proper Sizing': 'width: 300px' in result and 'height: 300px' in result,
            'Street Navigation': '🟨' in result,  # Path symbols
            'Current Location': '👤' in result,  # Player symbol
            'Walkable Streets': '⬜' in result,   # Street symbols
            'City Buildings': any(symbol in result for symbol in ['🏢', '🌳', '🏪', '🏛️', '🏟️', '🎰', '🛒']),
            'Clickable Elements': 'onclick=' in result,
            'Proper Container': 'margin: 0 auto' in result,
            'Description Text': 'Diamond City Streets' in result
        }
        
        for check_name, passed in checks.items():
            status = "PASS" if passed else "FAIL"
            print(f"  {check_name}: {status}")
        
        # Count specific elements (using unicode escapes to avoid encoding issues)
        street_count = result.count('\u2b1c')  # ⬜
        path_count = result.count('\U0001f7e8')  # 🟨
        building_count = result.count('\U0001f3e2') + result.count('\U0001f333') + result.count('\U0001f3ea')  # 🏢🌳🏪
        destination_count = result.count('\U0001f3db') + result.count('\U0001f3df') + result.count('\U0001f3b0') + result.count('\U0001f6d2')  # 🏛️🏟️🎰🛒
        
        print(f"  Content Analysis:")
        print(f"    - Streets: {street_count} tiles")
        print(f"    - Walkable Paths: {path_count} tiles") 
        print(f"    - Regular Buildings: {building_count} tiles")
        print(f"    - Special Destinations: {destination_count} tiles")
        
        print(f"  Result: {'SUCCESS - Street minimap properly generated!' if all(checks.values()) else 'ISSUES DETECTED'}")
    
    print("\n" + "=" * 50)
    print("Street Minimap Testing Complete!")
    
    # Generate HTML test file
    html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <title>Street-Based Minimap Test</title>
    <style>
        body {{ background: #1a1a1a; color: white; font-family: Arial; padding: 20px; }}
        .test-section {{ margin: 30px 0; padding: 20px; border: 1px solid #444; border-radius: 8px; }}
        .minimap-container {{ text-align: center; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>🌟 Street-Based Diamond City Minimap Test</h1>
    
    <div class="test-section">
        <h2>✨ New Features</h2>
        <ul>
            <li>✅ 10x10 street grid with proper city layout</li>
            <li>✅ Walkable streets (⬜) throughout the city</li>
            <li>✅ Highlighted paths (🟨) to available destinations</li>
            <li>✅ Special destination buildings (🏛️🏟️🎰🛒)</li>
            <li>✅ Regular city buildings (🏢🌳🏪)</li>
            <li>✅ Proper container sizing (300x300px)</li>
            <li>✅ Clickable navigation to accessible areas</li>
            <li>✅ Visual indicators for walkable vs blocked areas</li>
        </ul>
    </div>
    
    <div class="test-section">
        <div class="minimap-container">
            <h3>Room 4 (Fight Arena) - West to Marketplace</h3>
            {generate_minimap(4, [{'direction': 'west', 'to_room_id': 1, 'room_name': 'Marketplace'}])}
        </div>
        
        <div class="minimap-container">
            <h3>Room 1 (City Center) - Multiple Destinations</h3>
            {generate_minimap(1, [
                {'direction': 'east', 'to_room_id': 4, 'room_name': 'Casino'},
                {'direction': 'north', 'to_room_id': 2, 'room_name': 'City Hall'},
                {'direction': 'southwest', 'to_room_id': 3, 'room_name': 'Bank'}
            ])}
        </div>
    </div>
    
    <script>
        function move(direction) {{
            alert('🚶‍♂️ Walking through Diamond City streets ' + direction + '! This would trigger server navigation.');
        }}
    </script>
</body>
</html>
    '''
    
    with open('test_street_minimap.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Test HTML file generated: test_street_minimap.html")
    return True

if __name__ == "__main__":
    test_street_minimap()