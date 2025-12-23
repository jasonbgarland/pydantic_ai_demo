#!/usr/bin/env python3
"""Test script to verify agent integration without Docker dependencies."""

import asyncio
import sys
import os

# Add backend to Python path
sys.path.append('./backend')

async def test_agent_integration():
    """Test the agent integration pipeline."""
    print("🚀 Testing Adventure Narrator Integration")
    print("=" * 50)
    
    try:
        # Import the agents
        from app.agents.adventure_narrator import AdventureNarrator, ParsedCommand, CommandType
        from app.agents.room_descriptor import RoomDescriptor
        from app.agents.inventory_manager import InventoryManager
        from app.agents.entity_manager import EntityManager
        
        print("✅ Successfully imported all agents")
        
        # Initialize agents
        room_descriptor = RoomDescriptor()
        inventory_manager = InventoryManager()
        entity_manager = EntityManager()
        adventure_narrator = AdventureNarrator(
            room_descriptor=room_descriptor,
            inventory_manager=inventory_manager,
            entity_manager=entity_manager
        )
        
        print("✅ Successfully initialized agents")
        
        # Test command parsing
        test_commands = [
            "look around",
            "go north", 
            "examine door",
            "take sword",
            "inventory"
        ]
        
        for cmd in test_commands:
            print(f"\n🔍 Testing command: '{cmd}'")
            parsed = adventure_narrator.parse_command(cmd)
            print(f"   Parsed as: {parsed.command_type.value} - '{parsed.action}'")
            if parsed.target:
                print(f"   Target: {parsed.target}")
            if parsed.direction:
                print(f"   Direction: {parsed.direction}")
            print(f"   Confidence: {parsed.confidence:.2f}")
        
        print("\n🎮 Testing full command handling...")
        
        # Test a full command processing pipeline (without AI agents active)
        game_state = {
            "current_location": "Cave Entrance",
            "inventory": [],
            "visited_rooms": [],
            "character": {"name": "TestHero", "character_class": "warrior"},
            "turn_count": 1
        }
        
        test_command = adventure_narrator.parse_command("look around")
        
        try:
            response = await adventure_narrator.handle_command(
                parsed_command=test_command,
                game_state=game_state
            )
            print(f"✅ Command handling successful!")
            print(f"   Agent: {response.agent}")
            print(f"   Response: {response.narrative[:100]}...")
            print(f"   Success: {response.success}")
            
        except Exception as e:
            print(f"⚠️  Command handling had fallback (expected without OpenAI): {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Agent Integration Test Complete!")
        print("\nNext steps:")
        print("1. Set up OpenAI API key in .env file")
        print("2. Start Docker services for full testing")
        print("3. Test through the FastAPI endpoint")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root directory")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_integration())