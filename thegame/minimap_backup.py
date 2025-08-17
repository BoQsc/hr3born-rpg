def generate_minimap(current_room_id, connections):
    """Generate simple text-based minimap matching original style"""
    available_directions = [conn['direction'].lower() for conn in connections]
    
    # Build simple text minimap that matches the .minimap CSS
    minimap = ""
    minimap += "╔═══════════════════╗\n"
    minimap += "║ DIAMOND CITY      ║\n"
    minimap += "╠═══════════════════╣\n"
    
    # Show available directions
    north = "    NORTH: Hall     " if "north" in available_directions else "                   "
    minimap += f"║{north}║\n"
    
    west = "WEST:" if "west" in available_directions else "     "
    center = "  @  "  # Current location
    east = ":EAST" if "east" in available_directions else "     "
    minimap += f"║{west}{center}{east}║\n"
    
    south = "   SOUTH: Area     " if "south" in available_directions else "                   "
    minimap += f"║{south}║\n"
    
    sw = "SW: Casino" if "southwest" in available_directions else "          "
    minimap += f"║{sw}         ║\n"
    
    minimap += "╚═══════════════════╝"
    
    return minimap