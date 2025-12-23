"""Quick test of RAG integration."""
import sys
sys.path.insert(0, 'backend')

from app.tools.rag_tools import query_world_lore, get_room_description

# Test 1: Query world lore
print("=" * 60)
print("Test 1: General query about caves")
print("=" * 60)
results = query_world_lore("dark cave entrance crystals", max_results=3)
for i, result in enumerate(results, 1):
    print(f"\n{i}. {result[:200]}...")

# Test 2: Location-specific query
print("\n" + "=" * 60)
print("Test 2: Cave Entrance description")
print("=" * 60)
desc = get_room_description("Cave Entrance")
print(desc[:500] + "...")

# Test 3: Location-specific query with filtering
print("\n" + "=" * 60)
print("Test 3: Query with location filter - Yawning Chasm")
print("=" * 60)
results = query_world_lore("rope bridge danger", "Yawning Chasm", max_results=2)
for i, result in enumerate(results, 1):
    print(f"\n{i}. {result[:200]}...")

print("\n" + "=" * 60)
print("RAG test complete!")
print("=" * 60)
