#!/usr/bin/env python3
"""
End-to-end test for save/load functionality
"""

import requests
import json
import time

API_BASE = "http://localhost:8001"

def test_save_load_flow():
    """Test the complete save/load flow"""
    
    print("=== Testing Save/Load Flow ===\n")
    
    # 1. Create a character
    print("1. Creating character...")
    char_response = requests.post(
        f"{API_BASE}/character/create",
        json={
            "name": "TestHero",
            "character_class": "warrior"
        },
        timeout=10
    )
    char_data = char_response.json()
    print(f"   ✓ Character created: {char_data['character']['name']}\n")
    
    # 2. Start a game session
    print("2. Starting game session...")
    session_response = requests.post(
        f"{API_BASE}/game/start",
        json={
            "name": "TestHero",
            "character_class": "warrior"
        },
        timeout=10
    )
    session_data = session_response.json()
    game_id = session_data['game_id']
    print(f"   ✓ Game started with ID: {game_id}\n")
    
    # 3. Execute a few commands to change state
    print("3. Executing commands...")
    commands = ["look around", "go north", "examine room"]
    for cmd in commands:
        cmd_response = requests.post(
            f"{API_BASE}/game/{game_id}/command",
            json={"command": cmd},
            timeout=10
        )
        cmd_data = cmd_response.json()
        print(f"   ✓ Command '{cmd}' -> Turn {cmd_data['turn']}")
    print()
    
    # 4. Save the game
    print("4. Saving game...")
    save_response = requests.post(
        f"{API_BASE}/game/{game_id}/save",
        json={"session_name": "Test Save #1"},
        timeout=10
    )
    save_data = save_response.json()
    print(f"   ✓ Game saved: {save_data['session_name']}")
    print(f"   ✓ Saved at: {save_data['saved_at']}\n")
    
    # 5. List saved games
    print("5. Listing saved games...")
    list_response = requests.get(f"{API_BASE}/game/saves", timeout=10)
    list_data = list_response.json()
    print(f"   ✓ Found {len(list_data['saved_games'])} saved game(s)")
    for save in list_data['saved_games']:
        print(f"     - {save['session_name']}: {save['character_name']} (Turn {save['turn_count']})")
    print()
    
    # 6. Load the game
    print("6. Loading game...")
    load_response = requests.post(
        f"{API_BASE}/game/{game_id}/load",
        timeout=10
    )
    load_data = load_response.json()
    loaded_session = load_data['session']
    print(f"   ✓ Game loaded: {load_data['message']}")
    print(f"   ✓ Location: {loaded_session['location']}")
    print(f"   ✓ Turn count: {loaded_session['turn_count']}")
    print(f"   ✓ Inventory: {loaded_session['inventory']}\n")
    
    # 7. Verify state was restored
    print("7. Verifying state...")
    assert loaded_session['turn_count'] == 3, "Turn count mismatch"
    assert loaded_session['character']['name'] == "TestHero", "Character name mismatch"
    print("   ✓ State verification passed\n")
    
    # 8. Delete the save
    print("8. Deleting save...")
    delete_response = requests.delete(
        f"{API_BASE}/game/{game_id}/save",
        timeout=10
    )
    delete_data = delete_response.json()
    print(f"   ✓ {delete_data['message']}\n")
    
    print("=== All Tests Passed! ✓ ===")

if __name__ == "__main__":
    try:
        test_save_load_flow()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
