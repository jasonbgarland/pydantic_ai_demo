# Game Mechanics Implementation Guide

**Status**: ✅ **COMPLETE** - All mechanics implemented and tested (January 2026)
**Purpose**: Reference documentation for the implemented game mechanics supporting narrative scenarios.

---

## Core Mechanics Needed

### 1. Turn Counter System

**Purpose**: Track turns after crystal is taken to create time pressure during escape.

**Implementation**:

```python
# In session state (Redis)
{
    "collapse_triggered": false,
    "turns_since_collapse": 0,
    "collapse_turn_limit": 7
}
```

**Logic**:

- When player executes `take crystal` command → set `collapse_triggered = true`
- Increment `turns_since_collapse` with each command after trigger
- Check if `turns_since_collapse >= collapse_turn_limit` → trigger game over
- Reset on new game or load

**Narrative Integration**:

- Turn 0: "You grab the crystal. Deep rumbling begins!"
- Turn 1-2: "Minor rockfall. Move quickly!"
- Turn 3-4: "Rocks falling! Ceiling cracking!"
- Turn 5-6: "HEAVY COLLAPSE! Dangerous!"
- Turn 7+: "The cave seals shut. You're trapped. GAME OVER."

---

### 2. Environmental State System

**Purpose**: Track collapse progression and affect room descriptions dynamically.

**Implementation**:

```python
# Environmental states
ENVIRONMENTAL_STATES = {
    "normal": {
        "description_modifier": "",
        "damage_chance": 0.0
    },
    "minor_collapse": {
        "description_modifier": "Small rocks fall from the ceiling.",
        "damage_chance": 0.1,
        "damage_amount": 5
    },
    "moderate_collapse": {
        "description_modifier": "Rocks crash down! The ceiling cracks ominously!",
        "damage_chance": 0.3,
        "damage_amount": 10
    },
    "severe_collapse": {
        "description_modifier": "MASSIVE COLLAPSE! Boulders rain down!",
        "damage_chance": 0.6,
        "damage_amount": 20
    },
    "critical_collapse": {
        "description_modifier": "The cave is sealing shut!",
        "damage_chance": 0.9,
        "damage_amount": 30
    }
}

def get_environmental_state(turns_since_collapse: int) -> str:
    if turns_since_collapse == 0:
        return "normal"
    elif turns_since_collapse <= 2:
        return "minor_collapse"
    elif turns_since_collapse <= 4:
        return "moderate_collapse"
    elif turns_since_collapse <= 6:
        return "severe_collapse"
    else:
        return "critical_collapse"
```

**Integration**:

- RoomDescriptor agent checks environmental state
- Appends state-specific description to room narrative
- Triggers damage rolls based on state

---

### 3. Health/Damage System

**Purpose**: Warriors tank damage, others avoid or shield from it.

**Implementation**:

```python
# Character base stats (already in main.py)
CHARACTER_STATS = {
    "Warrior": {
        "health": 100,
        "strength": 18,
        "magic": 10,
        "agility": 12,
        "defense": 16
    },
    "Wizard": {
        "health": 70,
        "strength": 10,
        "magic": 18,
        "agility": 12,
        "defense": 10
    },
    "Rogue": {
        "health": 80,
        "strength": 12,
        "magic": 10,
        "agility": 18,
        "defense": 12
    }
}

# Damage calculation
def apply_environmental_damage(
    character_class: str,
    environmental_state: str,
    active_abilities: List[str]
) -> tuple[int, str]:
    """
    Returns: (damage_amount, narrative_description)
    """
    state_info = ENVIRONMENTAL_STATES[environmental_state]

    # Check if damage occurs
    if random.random() > state_info["damage_chance"]:
        return (0, "You dodge the falling debris!")

    base_damage = state_info["damage_amount"]

    # Class-specific modifiers
    if character_class == "Warrior":
        # Warriors have high defense, reduce damage
        actual_damage = int(base_damage * 0.5)
        narrative = f"Rocks hit you for {actual_damage} damage, but your resilience keeps you going!"

    elif character_class == "Wizard":
        # Wizards can shield
        if "shield" in active_abilities:
            actual_damage = int(base_damage * 0.2)
            narrative = f"Your magic shield deflects most damage! {actual_damage} damage taken."
        else:
            actual_damage = base_damage
            narrative = f"Rocks strike you for {actual_damage} damage! Cast a shield!"

    elif character_class == "Rogue":
        # Rogues dodge automatically with agility
        dodge_chance = 0.7  # 70% dodge
        if random.random() < dodge_chance:
            actual_damage = 0
            narrative = "Your agility lets you dodge the falling rocks!"
        else:
            actual_damage = int(base_damage * 0.7)
            narrative = f"A rock clips you for {actual_damage} damage, but you stay nimble!"

    return (actual_damage, narrative)
```

**Session State**:

```python
{
    "current_health": 100,
    "max_health": 100,
    "active_abilities": ["shield"],  # Wizard's cast shield
    "status_effects": []
}
```

---

### 4. Class-Specific Abilities

**Purpose**: Let each class use unique abilities during challenges.

**Implementation**:

#### Warrior Abilities

```python
WARRIOR_ABILITIES = {
    "break rocks": {
        "description": "Use strength to smash through obstructions",
        "effect": "clear_minor_obstacle",
        "cooldown": 0,
        "narrative": "You smash through the debris with raw strength!"
    },
    "jump across": {
        "description": "Athletic leap across gap (risky without equipment)",
        "effect": "attempt_chasm_cross",
        "success_rate": 0.3,  # Without rope
        "with_equipment": 0.8,
        "narrative_success": "Your powerful legs launch you across!",
        "narrative_failure": "You leap but fall short! (Take damage or death)"
    },
    "tank damage": {
        "description": "Ignore damage and push forward (passive)",
        "effect": "damage_reduction",
        "reduction": 0.5,
        "narrative": "You grit your teeth and power through!"
    }
}
```

#### Wizard Abilities

```python
WIZARD_ABILITIES = {
    "cast shield": {
        "description": "Magical protection from falling rocks",
        "effect": "add_status_effect",
        "status": "shielded",
        "duration": 3,  # turns
        "cooldown": 5,
        "narrative": "A shimmering barrier surrounds you!"
    },
    "cast levitate": {
        "description": "Float across chasm safely",
        "effect": "attempt_chasm_cross",
        "success_rate": 0.6,  # Without rope
        "with_equipment": 0.9,
        "narrative_success": "You float gracefully across the gap!",
        "narrative_failure": "The spell falters and you fall!"
    },
    "cast light": {
        "description": "Magical illumination",
        "effect": "add_status_effect",
        "status": "illuminated",
        "duration": 10,
        "narrative": "Magical light surrounds you!"
    },
    "cast telekinesis": {
        "description": "Clear obstacles while moving",
        "effect": "auto_clear_obstacles",
        "duration": 2,
        "narrative": "Debris floats aside as you approach!"
    }
}
```

#### Rogue Abilities

```python
ROGUE_ABILITIES = {
    "scale walls": {
        "description": "Climb chasm walls using agility",
        "effect": "attempt_chasm_cross",
        "success_rate": 0.5,  # Without equipment
        "with_equipment": 0.85,
        "narrative_success": "You nimbly scale the wall!",
        "narrative_failure": "You slip and fall!"
    },
    "dash": {
        "description": "Sprint through danger at double speed",
        "effect": "extra_movement",
        "cooldown": 3,
        "narrative": "You burst into a sprint, covering ground rapidly!"
    },
    "dodge": {
        "description": "Automatically avoid environmental hazards (passive)",
        "effect": "environmental_damage_avoidance",
        "dodge_chance": 0.7,
        "narrative": "You weave through falling rocks!"
    },
    "grapple": {
        "description": "Use grappling hook to traverse",
        "effect": "attempt_chasm_cross",
        "requires_item": "grappling_hook",
        "success_rate": 0.9,
        "narrative": "Your hook catches perfectly!"
    }
}
```

**Command Parsing**:

```python
def parse_ability_command(command: str, character_class: str) -> Optional[Dict]:
    """
    Recognize class-specific ability commands.
    """
    command_lower = command.lower()

    # Warrior
    if character_class == "Warrior":
        if "break" in command_lower and "rock" in command_lower:
            return WARRIOR_ABILITIES["break rocks"]
        if "jump" in command_lower:
            return WARRIOR_ABILITIES["jump across"]

    # Wizard
    if character_class == "Wizard":
        if "cast" in command_lower:
            if "shield" in command_lower:
                return WIZARD_ABILITIES["cast shield"]
            if "levitate" in command_lower or "float" in command_lower:
                return WIZARD_ABILITIES["cast levitate"]
            if "light" in command_lower:
                return WIZARD_ABILITIES["cast light"]
            if "telekinesis" in command_lower or "move" in command_lower:
                return WIZARD_ABILITIES["cast telekinesis"]

    # Rogue
    if character_class == "Rogue":
        if "scale" in command_lower or "climb" in command_lower:
            return ROGUE_ABILITIES["scale walls"]
        if "dash" in command_lower or "sprint" in command_lower:
            return ROGUE_ABILITIES["dash"]
        if "grapple" in command_lower:
            return ROGUE_ABILITIES["grapple"]

    return None
```

---

### 5. Victory/Defeat Detection

**Purpose**: Recognize win and loss conditions.

**Implementation**:

```python
def check_victory_condition(session_state: Dict) -> bool:
    """
    Victory: At cave_entrance (or outside), has crystal, exit west.
    """
    has_crystal = "crystal_of_echoing_depths" in session_state.get("inventory", [])
    at_entrance = session_state.get("current_location") == "cave_entrance"

    # If at entrance with crystal and go west → VICTORY!
    return has_crystal and at_entrance

def check_defeat_conditions(session_state: Dict) -> tuple[bool, str]:
    """
    Defeat conditions:
    1. Health <= 0 (death)
    2. Collapse turn limit exceeded (trapped)
    3. At dead end when collapse critical (trapped)

    Returns: (is_defeated, reason)
    """
    # Health check
    if session_state.get("current_health", 100) <= 0:
        return (True, "death")

    # Collapse timer check
    if session_state.get("collapse_triggered", False):
        turns = session_state.get("turns_since_collapse", 0)
        limit = session_state.get("collapse_turn_limit", 7)

        if turns >= limit:
            return (True, "trapped_by_collapse")

        # Dead end trap (collapsed_passage during collapse)
        if session_state.get("current_location") == "collapsed_passage":
            if turns >= limit - 2:  # Almost out of time
                return (True, "trapped_in_dead_end")

    return (False, "")

def set_game_status(session_state: Dict):
    """
    Update game status based on conditions.
    """
    # Check victory first
    if check_victory_condition(session_state):
        session_state["status"] = "victory"
        return

    # Check defeat
    is_defeated, reason = check_defeat_conditions(session_state)
    if is_defeated:
        session_state["status"] = "defeat"
        session_state["defeat_reason"] = reason
        return

    # Otherwise active
    session_state["status"] = "active"
```

**Victory Narrative**:

```python
VICTORY_NARRATIVE = """
You burst from the cave entrance into blessed daylight, the Crystal of Echoing Depths
clutched triumphantly in your hands! Behind you, the cave system groans and collapses
with a thunderous roar, sealing the treasury forever.

Dust billows from the entrance as the rumbling subsides. You've succeeded where countless
others failed. The crystal pulses warmly in your grasp, its blue light dimming now that
you're safe.

The adventure is complete. The treasure is yours. Well done, brave adventurer!

🏆 VICTORY! 🏆
"""

DEFEAT_NARRATIVES = {
    "death": "Your vision fades as injuries overwhelm you. The cave claims another victim...",
    "trapped_by_collapse": "The final boulder seals the passage. You're trapped in darkness forever...",
    "trapped_in_dead_end": "You realize too late - the collapsed passage has no exit. The cave becomes your tomb..."
}
```

---

### 6. Rope/Equipment State

**Purpose**: Track if rope is anchored at chasm for quick recrossing during escape.

**Implementation**:

```python
# In session state
{
    "chasm_rope_anchored": false,
    "equipment_state": {
        "magical_rope": {
            "location": "inventory",  # or "anchored_at_chasm"
            "condition": "excellent"
        }
    }
}

# When crossing chasm first time
def use_rope_at_chasm(session_state: Dict) -> str:
    """
    First crossing: Anchor rope, leave it there.
    Return crossing: Use anchored rope quickly.
    """
    if session_state.get("chasm_rope_anchored", False):
        # Quick recross
        return "You quickly traverse the already-anchored rope!"
    else:
        # First cross - anchor it
        session_state["chasm_rope_anchored"] = True
        return "You command the magical rope to anchor itself, then cross carefully..."
```

---

## Integration with Existing Agents

### AdventureNarrator Changes

Add to command processing:

```python
# In process_command method
async def process_command(self, command: str, session_state: Dict) -> str:
    # Check for class-specific abilities first
    ability = parse_ability_command(command, session_state["character_class"])
    if ability:
        return await self.execute_ability(ability, session_state)

    # Check for crystal trigger
    if "take" in command.lower() and "crystal" in command.lower():
        session_state["collapse_triggered"] = True
        session_state["turns_since_collapse"] = 0

    # Increment turn counter if collapse active
    if session_state.get("collapse_triggered", False):
        session_state["turns_since_collapse"] += 1

    # Apply environmental damage if in collapse
    if session_state.get("collapse_triggered", False):
        damage, damage_narrative = apply_environmental_damage(
            session_state["character_class"],
            get_environmental_state(session_state["turns_since_collapse"]),
            session_state.get("active_abilities", [])
        )
        session_state["current_health"] -= damage

    # Check victory/defeat
    set_game_status(session_state)

    # ... rest of command processing
```

### RoomDescriptor Changes

Add environmental state to room descriptions:

```python
# In describe_room method
async def describe_room(self, location: str, session_state: Dict) -> str:
    # Get base room description from RAG
    base_description = await self.get_room_from_rag(location)

    # Add environmental modifiers if collapse active
    if session_state.get("collapse_triggered", False):
        env_state = get_environmental_state(session_state["turns_since_collapse"])
        env_modifier = ENVIRONMENTAL_STATES[env_state]["description_modifier"]
        return f"{base_description}\n\n{env_modifier}"

    return base_description
```

---

## ✅ Implementation Complete

**Status**: All mechanics implemented and tested (January 2026)

Verified implementation:

- ✅ Turn counter increments after crystal taken
- ✅ Environmental state changes with turn count
- ✅ Damage system works for each class
- ✅ Warriors tank damage effectively
- ✅ Wizards can cast shield to reduce damage
- ✅ Rogues dodge automatically
- ✅ Class abilities execute correctly
- ✅ Victory detected at cave entrance + crystal + west
- ✅ Defeat detected for health <= 0
- ✅ Defeat detected for collapse turn limit
- ✅ Defeat detected for dead end trap
- ✅ Rope anchoring works for quick recross
- ✅ Narratives match environmental states
- ✅ All 21 test scenarios pass

**Test Coverage**: 280 total tests (212 passing, 68 skipped - integration tests requiring full stack)

- 117 mechanics unit tests
- 15 game flow scenario tests
- 19 room descriptor tests
- Additional integration and edge case tests

---

## ✅ Implementation Status

All mechanics have been implemented in priority order:

1. ✅ **Turn counter + collapse trigger** - Implemented in CollapseManager
2. ✅ **Victory/defeat detection** - Implemented in game status checks
3. ✅ **Environmental state system** - Progressive collapse states with damage
4. ✅ **Basic damage system** - Class-specific damage resistance
5. ✅ **Class-specific abilities** - AbilitySystem with full class differentiation
6. ✅ **Rope anchoring** - RopeSystem for chasm crossing optimization

**Implementation File**: [backend/app/mechanics.py](../backend/app/mechanics.py) (1167 lines)
**Test File**: [backend/tests/test_mechanics_unit.py](../backend/tests/test_mechanics_unit.py) (1285 lines, 117 tests)

---

## Quick Start Code Snippets

### Add to session initialization (main.py):

```python
session_state = {
    # ... existing fields
    "collapse_triggered": False,
    "turns_since_collapse": 0,
    "collapse_turn_limit": 7,
    "current_health": CHARACTER_STATS[character_class]["health"],
    "max_health": CHARACTER_STATS[character_class]["health"],
    "active_abilities": [],
    "chasm_rope_anchored": False,
    "status": "active",
    "defeat_reason": None
}
```

### Add to command endpoint (main.py):

```python
@app.post("/game/{session_id}/command")
async def execute_command(session_id: str, command_data: CommandRequest):
    # ... existing code

    # After command execution, check status
    if session["status"] == "victory":
        return {
            "narrative": VICTORY_NARRATIVE,
            "status": "victory"
        }

    if session["status"] == "defeat":
        return {
            "narrative": DEFEAT_NARRATIVES[session["defeat_reason"]],
            "status": "defeat"
        }

    # ... return normal response
```

---

This guide provides all the mechanics needed to make the narrative scenarios fully playable!
