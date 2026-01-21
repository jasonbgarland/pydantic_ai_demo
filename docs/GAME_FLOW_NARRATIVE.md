# Game Flow Narrative Design

## Crystal of Echoing Depths - Complete Playthrough Scenarios

**Status**: ✅ **IMPLEMENTED & TESTED** (January 2026)  
**Version**: 1.0  
**Original Design**: December 28, 2025  
**Purpose**: Complete game flow scenarios - fully implemented with all mechanics and content

---

## Overview

A 5-room adventure with a classic three-act structure where players must:

1. **Explore** the cave and cross the dangerous chasm
2. **Retrieve** the Crystal of Echoing Depths treasure
3. **Escape** the collapsing cave before being trapped

Each character class (Warrior, Wizard, Rogue) has unique approaches to challenges.

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
**Victory Condition**: Exit west from Cave Entrance with the crystal  
**Failure Conditions**: Die from fall, trapped by collapse, fail to escape in time

---

## Act 1: Exploration and Crossing the Chasm

### Scene 1: Cave Entrance (Starting Point)

**Available Actions**:

- `look around` - Describes the cave entrance, mentions rope on wall
- `examine rope` - Describes magical rope (can be taken)
- `take rope` - Adds rope to inventory
- `go north` - Discover Hidden Alcove (optional)
- `go east` - Enter Yawning Chasm (main path)

**Key Items**:

- **Magical Rope**: Essential for crossing chasm safely

**Success Path**:

1. Player examines surroundings
2. Player takes rope
3. Player moves east to chasm

**Failure Path**:

- Skip rope → Increased difficulty at chasm
- Go east immediately → Miss optional gear from alcove

---

### Scene 2: Hidden Alcove (Optional)

**Available Actions**:

- `look around` - Describes hidden storage area
- `examine alcove` - Reveals ancient climbing gear
- `search alcove` - Alternative to examine
- `take climbing gear` - Adds gear to inventory (if available)
- `go south` - Return to Cave Entrance

**Key Items**:

- **Climbing Gear**: Provides bonus for chasm crossing

**Success Path**:

1. Player explores thoroughly
2. Player finds and takes climbing gear
3. Player returns to entrance and continues east

**Failure Path**:

- Miss this room entirely → No bonus gear
- Don't examine carefully → Miss the gear

---

### Scene 3: Yawning Chasm (Critical Challenge)

**Available Actions**:

- `look around` - Describes dangerous chasm, width, darkness below
- `examine chasm` - Reveals depth, danger, need for rope
- `use rope` - Attempt to cross with rope (success if rope in inventory)
- `cross chasm` - Attempt without equipment (risky)
- `go west` - Return to Cave Entrance (retreat)
- `go south` - Discover Collapsed Passage (blocked/dangerous)

**Class-Specific Approaches**:

#### Warrior Approach:

- **With rope**: Uses strength to secure rope firmly, crosses safely
- **Without rope**: Attempts daring leap (AGI check, high risk)
- **Unique action**: `jump across` - Strength-based athletic feat
- **Success rate**: 80% with rope, 30% without

#### Wizard Approach:

- **With rope**: Uses magic to levitate rope into perfect position
- **Without rope**: Casts feather fall or levitation spell
- **Unique action**: `cast levitate` - Magic-based crossing
- **Success rate**: 90% with rope, 60% with spell, 20% without

#### Rogue Approach:

- **With rope**: Uses agility to traverse rope gracefully
- **Without rope**: Uses grappling hook or climbs walls
- **Unique action**: `scale walls` - Agility-based climbing
- **Success rate**: 85% with rope, 50% with climbing gear, 25% without

**Success Path**:

1. Player has rope in inventory
2. Player uses rope to cross
3. System narrates successful crossing based on class
4. Player moves east to Crystal Treasury

**Failure Paths**:

- **No equipment**:
  - Warrior: Falls into chasm (instant death or severe injury)
  - Wizard: Spell fails, falls (takes damage, can retry)
  - Rogue: Loses grip, falls (takes damage, can retry if agile enough)
- **Equipment but bad execution**: Takes damage, can retry
- **Critical failure**: Death, game over

---

## Act 2: The Treasure

### Scene 4: Crystal Treasury (Prize)

**Available Actions**:

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

## Act 3: The Escape

### Scene 5: Escape Sequence (Time Pressure)

**Turn Limit**: 5-7 turns depending on class and equipment

**Environmental Changes**:

- Turn 1 after trigger: Minor rockfall, navigation normal
- Turn 2-3: Moderate rockfall, descriptions show urgency
- Turn 4-5: Heavy rockfall, damage possible, descriptions panicked
- Turn 6+: Severe collapse, high damage risk, passages closing

**Escape Route**: Crystal Treasury → Yawning Chasm → Cave Entrance → West Exit

**Available Actions** (All locations):

- `go [direction]` - Move toward exit
- `run [direction]` - Move faster (may skip description)
- `use crystal` - Crystal glows, provides light in darkness
- Movement commands have increased urgency in narration

**Class-Specific Advantages**:

#### Warrior:

- **High health**: Can tank rockfall damage
- **Strength**: Can smash through minor obstructions
- **Unique**: `break rocks` - Clear blocked passages
- **Speed**: Slower but resilient

#### Wizard:

- **Magic shield**: Can deflect falling rocks (1-2 uses)
- **Telekinesis**: Can clear path without stopping
- **Unique**: `cast shield` - Protect from damage
- **Speed**: Normal, but protected

#### Rogue:

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

**Failure Paths**:

- **Too slow**: Trapped at turn 7+, cave collapses, death
- **Falls at chasm**: Takes damage, may die from fall + collapse
- **Wrong direction**: Goes south to Collapsed Passage (dead end), trapped
- **Hesitates**: Explores more rooms after trigger, trapped

---

## Complete Success Scenarios

### Scenario A: Thorough Warrior

**Character**: Warrior "Throg"  
**Playstyle**: Methodical, strength-based

1. Start at Cave Entrance
2. `look around` - Learn about environment
3. `take rope` - Secure rope
4. `go north` - Explore alcove
5. `examine alcove` - Find climbing gear
6. `take climbing gear` - Bonus equipment
7. `go south` - Return to entrance
8. `go east` - Enter chasm
9. `use rope` - Cross safely with strength
10. `go east` - Enter treasury
11. `examine murals` - Read warning
12. `examine crystal` - Understand prize
13. `take crystal` - Trigger collapse
14. `go west` - Back to chasm (Turn 1)
15. `use rope` - Recross quickly (Turn 2)
16. `go west` - Back to entrance (Turn 3)
17. `go west` - EXIT, VICTORY

**Result**: Perfect score, all items, no damage

---

### Scenario B: Quick Wizard

**Character**: Wizard "Mystara"  
**Playstyle**: Fast, magic-focused

1. Start at Cave Entrance
2. `take rope` - Grab essential item
3. `go east` - Skip optional alcove
4. `use rope` - Cross with magic-assisted rope
5. `go east` - Enter treasury
6. `take crystal` - Immediate trigger
7. `cast shield` - Protect during escape
8. `go west` - Rush back (Turn 1)
9. `go west` - Recross chasm (Turn 2)
10. `go west` - Back to entrance (Turn 3)
11. `go west` - EXIT, VICTORY

**Result**: Fast completion, magic protection, efficient

---

### Scenario C: Risky Rogue

**Character**: Rogue "Shadow"  
**Playstyle**: Agile, minimal equipment

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

---

## Testing Scenarios

Each scenario should be tested via API with:

1. Session creation with specific character class
2. Sequence of commands
3. Expected responses at each step
4. Final state verification (victory/defeat)

### Test Categories:

#### A. Success Tests (9 scenarios)

- Warrior: Full exploration path
- Warrior: Minimal path
- Warrior: With all equipment
- Wizard: Magic-focused path
- Wizard: Minimal path
- Wizard: Emergency spell usage
- Rogue: Agility path
- Rogue: Stealth path
- Rogue: Speed run

#### B. Failure Tests (6 scenarios)

- Each class: Death from chasm fall
- Each class: Trapped by collapse timing
- Each class: Wrong direction after trigger

#### C. Edge Cases (6 scenarios)

- Take crystal without examining
- Try to go back after triggering collapse
- Use crystal in different rooms
- Attempt to cross chasm multiple ways
- Backtrack to Hidden Alcove after chasm
- Damage from rockfall but successful escape

**Total Test Scenarios**: 21 automated tests

---

## Content Gaps to Fill

Based on scenarios above, we need to add:

### New Items:

- [ ] Climbing Gear (in Hidden Alcove)
- [ ] Explorer's Journal (in Crystal Treasury, optional)
- [ ] Grappling Hook (alternative for Rogue, maybe in alcove)

### Room Enhancements:

- [ ] Yawning Chasm: Add depth description, danger warnings
- [ ] Hidden Alcove: Add climbing gear details
- [ ] Crystal Treasury: Add murals with warnings, pedestal description
- [ ] Collapsed Passage: Add "this is a dead end" warning
- [ ] Cave Entrance: Add exit description to the west

### Class-Specific Actions:

- [ ] Warrior: `jump across`, `break rocks`
- [ ] Wizard: `cast levitate`, `cast shield`, `cast light`
- [ ] Rogue: `scale walls`, `dash`, `grapple`

### Game Mechanics:

- [ ] Turn counter after crystal trigger
- [ ] Progressive collapse descriptions (environmental state)
- [ ] Fall damage system
- [ ] Death/game over handling
- [ ] Victory condition detection
- [ ] Rope state (secured vs unsecured)

### Narrative Variations:

- [ ] Class-specific crossing descriptions
- [ ] Class-specific trap escape descriptions
- [ ] Equipment-influenced descriptions
- [ ] Damage/health status descriptions
- [ ] Urgency levels in collapse narration

---

## Implementation Priority

### Phase 1: Core Path (Minimal Viable)

1. Ensure rope works for chasm crossing
2. Crystal trigger mechanism
3. Basic escape route (5 turns to exit)
4. Victory detection at west exit
5. Failure detection at turn limit

### Phase 2: Class Differentiation

1. Class-specific crossing methods
2. Class-specific escape abilities
3. Stat-based success rates

### Phase 3: Full Experience

1. All optional items
2. All room examination details
3. Progressive collapse descriptions
4. Damage and health system

---

## Success Metrics

A complete playthrough should have:

- ✅ Clear goal understanding (get crystal, escape)
- ✅ Fair warning of dangers (murals, journal)
- ✅ Multiple valid approaches (class-based)
- ✅ Appropriate time pressure (collapse sequence)
- ✅ Satisfying victory (narrative closure)
- ✅ Learnable failure (can retry with knowledge)

**Target completion time**: 10-20 commands for success path  
**Target failure rate**: 30-40% on first attempt (learning curve)  
**Target retry success**: 80%+ on second attempt (applied knowledge)
