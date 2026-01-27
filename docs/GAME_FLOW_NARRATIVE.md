# Game Flow Narrative Design

## Crystal of Echoing Depths - AI RPG Demo

**Status**: ✅ **IMPLEMENTED** (January 2026)  
**Version**: 2.0 - Simplified Demo  
**Purpose**: AI-powered text adventure demonstrating agent orchestration

> **Note**: This is a demonstration of AI agent capabilities, not a full RPG.  
> The focus is on natural language understanding and agent coordination.

---

## Overview

A simple 5-room adventure demonstrating AI agent capabilities:

1. **Explore** the cave using natural language commands
2. **Cross the chasm** using items and problem-solving
3. **Retrieve** the Crystal of Echoing Depths
4. **Exit** to achieve victory

**Key Features**:

- Natural language command parsing (AI-powered)
- Dynamic room descriptions (AI-generated)
- Intelligent item interactions
- Simple puzzle mechanics (chasm crossing, victory conditions)

---

## Room Network

```
[Hidden Alcove]
       |
       | (north/south)
       |
[Cave Entrance] ---(east/west)--- [Yawning Chasm] ---(east/west)--- [Crystal Treasury]
                                         |
                                         | (south/north)
                                         |
                                  [Collapsed Passage]
```

**Starting Location**: Cave Entrance  
**Victory Condition**: Possess the crystal + use "exit" or "escape" command at Cave Entrance  
**Implementation Notes**:

- No health/damage system (simplified for demo)
- No turn limits (removed for accessibility)
- No class-specific mechanics (all classes play identically)
- Focus is on natural language understanding and agent orchestration

---

## Simple Playthrough Guide

### Step 1: Cave Entrance (Starting Point)

**Example Commands** (natural language works!):

- `look around` / `examine the cave` - AI generates room description
- `take rope` / `grab the rope from the wall` - Pick up the rope
- `go north` / `explore north` - Discover Hidden Alcove (optional)
- `go east` / `head east` - Enter Yawning Chasm (main path)

**Key Items**:

- **Magical Rope**: Required for crossing the chasm

**Recommended Path**:

1. Take the rope from the wall
2. Optionally explore north to Hidden Alcove
3. Head east to the chasm

---

### Scene 2: Hidden Alcove (Optional)

**Available Actions**:

- `look around` - Describes hidden storage area
- `examine alcove` - Reveals ancient climbing gear
- `setep alcove` - Alternative to examine
- `take climbing gear` - Adds gear to inventory (if available)
- Example Commands\*\*:

- `look around` / `what's here?` - AI describes the alcove
- `examine alcove` / `search the area` - Look for items
- `take climbing gear` / `pick up the journal` - Grab items
- `go south` / `return to entrance` - Go back

**Optional Items**:

- **Climbing Gear**: Extra flavor for chasm crossing
- **Explorer's Journal**: Contains helpful hints

**Note**: This room is purely optional and exists to demonstrate exploration mechanics

- `look around` - Describes dangerous chasm, width, darkness below
- `examine chasm` - Reveals depth, danger, need for rope
- `use rope` - Attempt to cross with rope (success if rope in inventory)
- `cross chasm` - Attempt without equipment (risky)
- `go west` - Return to Cave Entrance (retreat)
- `go south` - Discover Collapsed Passage (blocked/dangerous)

**Example Commands**:

- `look around` / `examine the chasm` - AI describes the dangerous gap
- `cross chasm` / `use rope to cross` - Main puzzle solution
- `go west` - Return to Cave Entrance
- `go south` - Discover Collapsed Passage (dead end)

**Puzzle Mechanics**:

- **With rope**: Successfully cross to east side (sets temp_flag: chasm_east_side)
- **Without rope**: AI narrative warns you can't cross safely
- **Crossing back**: Toggles the temp_flag, allowing movement west again
- **Movement validation**: RoomDescriptor agent checks temp_flags before allowing east/west movement

**Implementation Note**: This demonstrates stateful AI agents that remember crossing status using temp_flags

- `look around` - Describes treasury, crystal on pedestal, murals
- `examine crystal` - Reveals it's the Crystal of Echoing Depths
- `examine murals` - Warning about taking the crystal (triggers trap)
- `examine pedestal` - Describes pressure mechanism
- `read journal` - If explorer's journal exists, warns of trap
- `take crystal` - **TRIGGER EVENT**: Cave begins to collapse
- `go west` - Return to chasm (escape route)

**Key Items**:

- **Crystal of Echoing Depths**: Victory item, triggers collapse

**Success Path**:

1. Player examines room thoroughly
2. Player reads warnings (understands risk)
3. Player prepares for escape (faces west)
4. Player takes crystal
5. Player immediately flees west

**Failure Paths**:

- **Unprepared**: Takes crystal while exploring, wastes time
- **Reads warnings but ignores**: Takes crystal anyway, slow to react
- **Explores too much after trigger**: Trapped by collapse

**Trap Trigger Effects**:

- Rumbling begins immediately
- Rocks start falling from ceiling
- Passages begin to destabilize
- Turn counter starts (player has limited turns to escape)

---

### Step 4: Crystal Treasury (The Goalressure)

**Turn Limit**: 5-7 turns depending on class and equipment

**Example Commands**:

- `look around` / `examine the room` - AI describes the magnificent treasury
- `examine crystal` / `look at the pedestal` - Details about the crystal
- `take crystal` / `grab the Crystal of Echoing Depths` - Win condition item!
- `go west` - Return to chasm

**Key Items**:

- **Crystal of Echoing Depths**: Required for victory

**What Happens When You Take the Crystal**:

1. AI generates dramatic "collapse" narrative (rumbling, danger, urgency)
2. Flag is set: `collapse_triggered = True`
3. This is narrative flavor - no actual gameplay consequences
4. You can now return to the entrance and exit

**Implementation Note**: The collapse is narrative-only. Originally planned as a timed escape sequence but simplified for the demo.

- **High agility**: Dodge falling rocks automatically
- **Stealth/speed**: Move through danger zones faster
- **Unique**: `dash` - Sprint through room (extra movement)
- **Speed**: Fastest escape

**Chasm During Collapse**:

- **With rope still secured**: Quick crossing (1 turn)
- **Rope damaged**: Must use alternative (2 turns)
- **No rope**: Emergency crossing (risky, class-dependent)

**Success Path**:

1. Player takes crystal (Turn 0)
2. Player immediately goes west (Turn 1 - back at chasm)
3. Player crosses chasm with secured rope (Turn 2 - at entrance)
4. Player goes west to exit (Turn 3 - VICTORY)
5. System narrates escape, crystal is secured

# Step 5: Return and Victory

**Return Route**: Crystal Treasury → Yawning Chasm → Cave Entrance

**Example Commands**:

- `go west` / `head back` - Retrace your steps
- `cross chasm` - Cross back over (remember the rope!)
- `exit` / `escape` / `leave the cave` - **Victory command at Cave Entrance**

**Victory Conditions** (both required):

1. **Have the crystal** in your inventory
2. **Use exit/escape command** at Cave Entrance location

**Implementation**: AdventureNarrator agent checks both conditions and triggers victory status

**Why explicit exit?**: Demonstrates intentional game design - simply being at the entrance isn't enough, you must explicitly choose to leave

1. Start at Cave Entrance
2. `go east` - Skip rope entirely (risky)
3. `scale walls` - Use agility to cross
4. `go east` - Enter treasury
5. `examine crystal` - Quick check
6. `take crystal` - Trigger collapse
7. `dash` - Sprint west (Turn 1, extra speed)
8. `scale walls` - Recross chasm quickly (Turn 2)
9. `go west` - Back to entrance (Turn 3)
10. `go west` - EXIT, VICTORY

**Result**: Fastest completion, high risk, style points

---

## Failure Scenarios

### Failure A: Unprepared Warrior Falls

**Mistake**: No rope, attempted jump

1. Start at Cave Entrance
2. `go east` - Skip rope
3. `go east` - Try to enter chasm
4. `jump across` - Attempt athletic feat
5. **SYSTEM**: Strength check fails (no rope)
6. **RESULT**: Fall into chasm, take heavy damage or death
7. **GAME OVER** or **RETRY FROM ENTRANCE** (if survived)

**Lesson**: Need equipment for warrior approach

---

### Failure B: Wizard Trapped by Collapse

**Mistake**: Too slow after taking crystal

1-10. (Successful exploration and crossing) 11. `take crystal` - Trigger collapse (Turn 0) 12. `examine pedestal` - Waste time (Turn 1) 13. `look around` - Waste time (Turn 2) 14. `go west` - Start escape too late (Turn 3) 15. `go west` - At chasm (Turn 4) 16. `use rope` - Crossing (Turn 5) 17. `go west` - Almost there (Turn 6) 18. **SYSTEM**: Major collapse blocks passage (Turn 7) 19. **RESULT**: Trapped, cave collapses completely 20. **GAME OVER**

**Lesson**: Must escape immediately after trigger

---

### Failure C: Rogue Wrong Path

**Mistake**: Went south to Collapsed Passage after trigger

1-10. (Successful exploration and crossing) 11. `take crystal` - Trigger collapse (Turn 0) 12. `go west` - Back to chasm (Turn 1) 13. `go south` - WRONG, enters Collapsed Passage (Turn 2) 14. `look around` - Realizes mistake (Turn 3) 15. `go north` - Try to return (Turn 4) 16. **SYSTEM**: Passage collapses, blocked (Turn 5) 17. **RESULT**: Trapped in dead end, no escape 18. **GAME OVER**

**Lesson**: Know the exit route before triggering trap
Example Successful Playthrough

Here's a minimal winning sequence (10 commands):

```
1. take rope
2. go east
3. cross chasm
4. go east
5. take crystal
6. go west
7. cross chasm
8. go west
9. exit
```

**Result**: VICTORY! 🏆

**What the AI Agents Do**:

- **IntentParser**: Classifies each command (MOVEMENT, PICKUP, EXIT, etc.)
- **RoomDescriptor**: Generates location descriptions, validates movement
- **InventoryManager**: Handles item pickup/drop with realistic constraints
- **AdventureNarrator**: Orchestrates everything, generates final narrative, checks victory

---

## Longer Explorative Playthrough

For a more thorough experience (20+ commands):

```
1. look around
2. examine the rope on the wall
3. take the magical rope
4. go north
5. look around the alcove
6. take the explorer's journal
7. read the journal
8. take climbing gear
9. go south
10. go east
11. examine the chasm
12. use rope to cross
13. go east
14. look at the murals
15. examine the crystal pedestal
16. take the Crystal of Echoing Depths
17. go west
18. cross back over the chasm
19. go west
20. escape the cave
```

**Result**: VICTORY with full exploration! 🏆 escape

---

## AI Agent Architecture

This game demonstrates coordinated AI agents working together:

### **IntentParser Agent**

- Classifies natural language into command types
- Understands variations ("take rope" = "grab the rope" = "pick up the magical rope")
- Routes commands to appropriate handlers

### **RoomDescriptor Agent**

- Generates dynamic room descriptions from RAG database
- Validates movement between rooms
- Checks temp_flags for stateful navigation (chasm crossing)

### **InventoryManager Agent**

- Handles item pickup/drop with realistic constraints
- Checks if items exist in current location
- Prevents duplicate pickups
- Maintains inventory state

### **AdventureNarrator Agent** (Orchestrator)

- Coordinates all other agents
- Handles special events (crystal collapse, victory)
- Generates final narrative responses
- Manages game state transitions

---

## Technical Implementation Notes

### State Management (Redis)

```python
session = {
    "game_id": "uuid",
    "character_name": "Player",
    "character_class": "Warrior",
    "location": "cave_entrance",
    "inventory": ["rope", "crystal_of_echoing_depths"],
    "temp_flags": {"chasm_east_side": True},
    "collapse_triggered": True,
    "turns_since_collapse": 0,
    "turn_count": 15,
    "game_status": "victory"
}
```

### Key Mechanics

**Chasm Crossing** (`temp_flags`):

- When crossing east: Sets `chasm_east_side: True`
- RoomDescriptor checks this flag before allowing east/west movement
- Crossing back: Toggles flag to `False`

**Crystal Collapse** (narrative only):

- Sets `collapse_triggered: True` when crystal is taken
- AI generates dramatic collapse narrative
- No actual gameplay consequences (originally planned as timed escape)

**Victory Detection**:

- Requires: `has_crystal` AND `at_cave_entrance` AND `exit_command`
- Checked by AdventureNarrator on each command
- Sets `game_status: "victory"`

### RAG Database (ChromaDB)

- Room descriptions stored as embeddings
- Items stored with metadata
- AI agents query for contextual information
- Enables rich, dynamic narrative generation

---

## Testing

**Test Suite**: 85 tests (81 passing, 4 skipped)

**Test Coverage**:

- Unit tests for mechanics, agents, and utils
- Integration tests for full game flow
- Scenario tests for refactored mechanics
- WebSocket streaming tests
- Save/load persistence tests

**Run Tests**:

```bash
cd backend
bash scripts/test-integration.sh  # Full suite
bash scripts/test-unit.sh         # Unit tests only
```

---

## What This Demo Shows

✅ **Natural Language Understanding**: AI parses varied command phrasings  
✅ **Agent Coordination**: Multiple AI agents work together seamlessly  
✅ **Stateful Navigation**: temp_flags enable complex movement puzzles  
✅ **Dynamic Content**: AI generates contextual room descriptions  
✅ **Tool Use**: Agents invoke tools (RAG queries, item checks) effectively  
✅ **Game Logic**: Victory conditions, state management, inventory system

## What This Demo Doesn't Include

❌ **Combat System**: No enemies, no damage  
❌ **Character Stats**: Classes are cosmetic only  
❌ **Time Pressure**: No turn limits (accessibility choice)  
❌ **Complex Puzzles**: Intentionally simple for demonstration  
❌ **Class Abilities**: No special powers (would overcomplicate)

---

## Future Enhancements (Not Implemented)

These were considered but kept out of scope for the demo:

- Health/damage system
- Turn counter with time limits
- Class-specific abilities and stat checks
- Progressive environmental damage
- Multiple endings based on choices
- Save file branching narratives

The current implementation prioritizes **clarity and demonstration value** over game complexity.
