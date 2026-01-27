# Game Mechanics Reference

**Status**: ✅ **CURRENT** (January 2026)  
**Purpose**: Reference for the game mechanics used in this AI agent demonstration

---

## Overview

This demo uses simple game mechanics focused on demonstrating AI agent capabilities rather than complex RPG systems.

> **Implementation**: [backend/app/mechanics.py](../backend/app/mechanics.py) (297 lines)

---

## Game Mechanics

### 1. Game Status System

Simple state machine for game progression:

```python
class GameStatus(str, Enum):
    IN_PROGRESS = "in_progress"  # Default state
    VICTORY = "victory"          # Player won
    DEFEAT = "defeat"            # Player lost (health only)
```

**Victory Conditions**:

- Player has Crystal of Echoing Depths in inventory
- Player is at cave_entrance location
- Player uses "exit" or "escape" command

**Defeat Conditions**:

- Player health reaches 0

---

### 2. Character Abilities

Each class has simple abilities to demonstrate tool calling:

```python
ABILITIES = {
    "Warrior": {
        "dash": "Sprint forward with warrior strength"
    },
    "Wizard": {
        "illuminate": "Create magical light"
    },
    "Rogue": {
        "sneak": "Move silently through shadows"
    }
}
```

**Implementation Note**: These are **flavor only**. Classes don't have different stats or gameplay mechanics - this keeps the demo simple.
Note\*\*: Classes are cosmetic - they don't affect gameplay mechanics

---

### 3. Temp Flags System

Temporary state flags for stateful navigation:

```python
session["temp_flags"] = {
    "chasm_east_side": True,  # Player is on east side of chasm
    # Add more flags as needed for puzzles
}
```

**Chasm Crossing Example**:

1. Player at yawning_chasm (west side)
2. `cross chasm` → Sets `chasm_east_side: True`
3. `go east` → Allowed because flag is True
4. `cross chasm` again → Toggles flag to False
5. `go west` → Allowed because flag is False

**Used By**: RoomDescriptor agent for movement validation

---

### 4. Collapse Trigger (Narrative Only)

Flag-based narrative event:

```python
session["collapse_triggered"] = False  # Default
session["turns_since_collapse"] = 0    # Tracked for narrative
```

**When Player Takes Crystal**:

1. Set `collapse_triggered = True`
2. AI generates dramatic "cave collapsing" narrative
3. Creates narrative urgency to return to entrance

**Note**: This is narrative flavor - there are no enforced turn limits or damage from the collapse.

---

## Implementation Details

### Core Functions (backend/app/mechanics.py)

```python
def check_victory_condition(session: Dict) -> bool:
    """Check if game_status is victory."""
    return session.get("game_status") == GameStatus.VICTORY

def check_defeat_conditions(session: Dict) -> Optional[DefeatReason]:
    """Check if player health <= 0."""
    health = session.get("character", {}).get("health", 100)
    return DefeatReason.HEALTH_DEPLETED if health <= 0 else None

def initialize_game_mechanics(session: Dict) -> None:
    """Set default values for game status."""
    session.setdefault("game_status", GameStatus.IN_PROGRESS)
    session.setdefault("defeat_reason", None)
```

### Simple Ability System

```python
class SimpleAbilitySystem:
    """Demonstrates tool calling without complex mechanics."""

    @staticmethod
    def can_use_ability(ability_name: str, character_class: str) -> Dict:
        """Check if character class has this ability."""
        # Returns: {"can_use": bool, "reason": str}

    @staticmethod
    def use_ability(ability_name: str, character_class: str, game_state: Dict) -> Dict:
        """Execute ability and return narrative."""
        # Returns: {"success": bool, "narrative": str, "effects": dict}
```

---

## Session State Schema

**Minimal state tracked in Redis**:

```python
session = {
    # Identity
    "game_id": "uuid-string",
    "character_name": "PlayerName",
    "character_class": "Warrior",  # Cosmetic only

    # Location & Inventory
    "location": "cave_entrance",
    "inventory": ["rope", "crystal_of_echoing_depths"],

    # Game Status
    "game_status": "in_progress",  # or "victory" or "defeat"
    "defeat_reason": None,

    # State Flags
    "temp_flags": {"chasm_east_side": True},
    "collapse_triggered": False,
    "turns_since_collapse": 0,  # Tracked but not enforced

    # Metadata
    "turn_count": 15,
    "command_history": [...]
}
```

---

## Design Philosophy

**Why So Simple?**

This demo showcases **AI agent capabilities**, not RPG mechanics:

✅ **What We Demonstrate**:

- Natural language understanding
- Multi-agent coordination
- Tool use and function calling
- Stateful navigation puzzles
- Dynamic content generation
- RAG database integration

❌ **What We Don't Need**:

- Combat systems
- Damage calculations
- Character progression
- Equipment bonuses
- Complex puzzle logic
- Fail states (except health)

---

## Testing

**Unit Tests**: [backend/tests/test_mechanics_unit.py](../backend/tests/test_mechanics_unit.py)

```bash
cd backend
python -m unittest tests.test_mechanics_unit -v
```

**Test Coverage**:

- Victory condition checking
- Defeat condition checking
- Ability system (can_use, use_ability)
- Session initialization

---

## What This Demonstrates

This implementation showcases AI agent capabilities:

- **Natural language understanding** - Varied command phrasings
- **Multi-agent coordination** - Agents working together
- **Tool use and function calling** - Agents invoking specific tools
- **Stateful navigation** - temp_flags for puzzle state
- **Dynamic content generation** - AI-generated narratives
- **RAG database integration** - Contextual information retrieval

---

## Related Documentation

- [AI_AGENTS.md](AI_AGENTS.md) - Agent architecture and tools
- [GAME_FLOW_NARRATIVE.md](GAME_FLOW_NARRATIVE.md) - Playthrough guide
- [CONTENT_GENERATION_SUMMARY.md](CONTENT_GENERATION_SUMMARY.md) - World content overview
