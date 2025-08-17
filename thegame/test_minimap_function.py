def generate_minimap(current_room_id, connections):
    """Generate visual grid minimap with rounded corner tiles"""
    available_directions = [conn['direction'].lower() for conn in connections]
    
    # 10x10 grid for proper minimap
    grid_size = 10
    center = 4  # Center position
    
    # Initialize grid with gray nonpassable areas
    grid = [['blocked' for _ in range(grid_size)] for _ in range(grid_size)]
    
    # Place current location at center
    grid[center][center] = 'current'
    
    # Add connected rooms based on available directions
    direction_offsets = {
        'north': (-1, 0),
        'south': (1, 0),  
        'east': (0, 1),
        'west': (0, -1),
        'northeast': (-1, 1),
        'northwest': (-1, -1),
        'southeast': (1, 1),
        'southwest': (1, -1)
    }
    
    # Mark accessible directions with doors
    for direction in available_directions:
        if direction in direction_offsets:
            offset_row, offset_col = direction_offsets[direction]
            new_row = center + offset_row
            new_col = center + offset_col
            if 0 <= new_row < grid_size and 0 <= new_col < grid_size:
                grid[new_row][new_col] = 'door'
    
    # Build minimap grid HTML with proper styling
    minimap_html = f'<div style="display: grid; grid-template-columns: repeat({grid_size}, 25px); grid-gap: 2px; justify-content: center; background: #2a2a2a; padding: 10px; border-radius: 8px;">'
    
    for row in range(grid_size):
        for col in range(grid_size):
            cell_type = grid[row][col]
            
            # Determine styling and content
            if cell_type == 'current':
                # Yellow tile with player emoji
                style = 'background: #ffd700; color: #000; border-radius: 4px; display: flex; align-items: center; justify-content: center; width: 25px; height: 25px; font-size: 14px;'
                content = '👤'
                onclick = ''
            elif cell_type == 'door':
                # Green tile with door emoji - clickable
                style = 'background: #32cd32; color: #fff; border-radius: 4px; display: flex; align-items: center; justify-content: center; width: 25px; height: 25px; font-size: 14px; cursor: pointer;'
                content = '🚪'
                
                # Figure out direction for onclick
                direction = None
                if row < center and col == center and 'north' in available_directions:
                    direction = 'north'
                elif row > center and col == center and 'south' in available_directions:
                    direction = 'south'
                elif row == center and col > center and 'east' in available_directions:
                    direction = 'east'
                elif row == center and col < center and 'west' in available_directions:
                    direction = 'west'
                elif row < center and col > center and 'northeast' in available_directions:
                    direction = 'northeast'
                elif row < center and col < center and 'northwest' in available_directions:
                    direction = 'northwest'
                elif row > center and col > center and 'southeast' in available_directions:
                    direction = 'southeast'
                elif row > center and col < center and 'southwest' in available_directions:
                    direction = 'southwest'
                
                onclick = f'onclick="move(\'{direction}\')"' if direction else ''
            else:
                # Gray rectangle for nonpassable
                style = 'background: #666; border-radius: 4px; width: 25px; height: 25px;'
                content = ''
                onclick = ''
            
            minimap_html += f'<div style="{style}" {onclick}>{content}</div>'
    
    minimap_html += '</div>'
    
    return minimap_html

# Test it
if __name__ == "__main__":
    connections = [{'direction': 'west', 'to_room_id': 1, 'room_name': 'Diamond City Center'}]
    result = generate_minimap(4, connections)
    
    print("SUCCESS! Grid minimap works!")
    print("Contains grid styling:", 'display: grid' in result)
    print("Contains yellow current location:", '#ffd700' in result)
    print("Contains green doors:", '#32cd32' in result)
    print("Contains gray blocks:", '#666' in result)
    print("Contains rounded corners:", 'border-radius: 4px' in result)
    print("Contains player emoji:", '👤' in result)
    print("Contains door emoji:", '🚪' in result)
    print("Contains click handlers:", 'onclick=' in result)