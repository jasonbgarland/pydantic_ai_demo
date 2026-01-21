# 🗡️ Rogue Playthrough Guide - Crystal of Echoing Depths

**Character Class**: Rogue  
**Playstyle**: Agility, speed, and quick thinking  
**Victory Strategy**: Use dash ability and natural agility to navigate quickly

---

## 🎮 Access the Game

**Frontend**: http://localhost:3000  
**Backend API**: http://localhost:8001

---

## 📋 Complete Rogue Walkthrough (Success Path)

### Step 1: Start a New Game

**Character Setup:**

- Name: `ShadowBlade` (or any name you like)
- Class: `Rogue`
- Click "Start New Game"

### Step 2: Cave Entrance (Starting Location)

**Commands to try:**

```
look around
```

**Expected**: Description of cave entrance, mentions rope on wall, hints about exploring north

```
examine rope
```

**Expected**: Details about magical rope - lightweight, perfect for agile rogues

```
take magical rope
```

**Expected**: "You take the magical rope" - Added to inventory

```
inventory
```

**Expected**: Shows `magical_rope` in your inventory

```
examine north
```

**Expected**: Hints about a hidden alcove to the north with useful equipment

```
go north
```

**Expected**: Move to Hidden Alcove

---

### Step 3: Hidden Alcove (Optional but Recommended)

**Commands to try:**

```
look around
```

**Expected**: Description of hidden storage area, mentions climbing gear and journal

```
examine alcove
```

**Expected**: Detailed description of what's available

```
examine explorer journal
```

**Expected**: **CRITICAL** - This contains the complete walkthrough! Read carefully.

```
take explorer journal
```

**Expected**: Journal added to inventory

```
examine climbing gear
```

**Expected**: Professional climbing equipment, great for rogues

```
take climbing gear
```

**Expected**: Climbing gear added to inventory

```
examine grappling hook
```

**Expected**: Alternative crossing tool, especially good for rogues

```
take grappling hook
```

**Expected**: Grappling hook added to inventory

```
inventory
```

**Expected**: Shows all your equipment (rope, journal, climbing gear, grappling hook)

```
go south
```

**Expected**: Return to Cave Entrance

---

### Step 4: Cave Entrance → Yawning Chasm

```
look around
```

**Expected**: Back at cave entrance

```
go east
```

**Expected**: Move to Yawning Chasm - **THE CRITICAL CHALLENGE**

---

### Step 5: Yawning Chasm - Cross the Gap

**This is the main obstacle. You have multiple options as a Rogue:**

#### Option A: Use Grappling Hook (Recommended for Rogues)

```
examine chasm
```

**Expected**: Description of the dangerous gap, crossing methods

```
use grappling hook
```

**Expected**: Secure crossing - low failure rate for rogues with agility

#### Option B: Use Magical Rope

```
secure rope
```

**Expected**: Rope anchored for safe crossing

```
cross chasm
```

**Expected**: Use rope to cross safely

#### Option C: Use Dash Ability (Rogue-Specific!)

```
dash
```

**Expected**: Use your rogue dash ability to sprint across the chasm

**After Successful Crossing:**

```
go east
```

**Expected**: Move to Crystal Treasury

---

### Step 6: Crystal Treasury - The Treasure!

```
look around
```

**Expected**: Glittering treasury, crystal on pedestal, **WARNINGS about trap**

```
examine crystal
```

**Expected**: Beautiful Crystal of Echoing Depths, warnings about collapse

```
examine murals
```

**Expected**: Ancient warnings about the trap mechanism

**WARNING: Taking the crystal triggers the collapse! You'll have ~7 turns to escape!**

```
take crystal
```

**Expected**:

- "You grab the crystal. Deep rumbling begins!"
- `collapse_triggered: true`
- Turn counter starts

---

### Step 7: ESCAPE SEQUENCE (Speed is Critical!)

**You have approximately 7 turns before the cave seals shut!**

#### Turn 1: Leave Treasury

```
go west
```

**Expected**: Back to Yawning Chasm - **Environmental effects begin** (minor rockfall)

#### Turn 2: Cross Back Quickly

**Option A: If rope was secured earlier:**

```
cross chasm
```

**Expected**: Quick crossing using anchored rope

**Option B: Use Dash Ability (FASTEST!):**

```
dash
```

**Expected**: Sprint across the chasm at high speed, minimal turn cost

**Option C: Use grappling hook:**

```
use grappling hook
```

**Expected**: Quick swing across

#### Turn 3: Head West

```
go west
```

**Expected**: Back at Cave Entrance - **Heavier collapse** (rocks falling, possible damage)

**Rogue Advantage**: You may automatically dodge falling rocks!

#### Turn 4: ESCAPE!

```
go west
```

**Expected**:

- 🎉 **VICTORY!**
- "You burst out of the cave with the crystal!"
- Game status: `victory`

---

## 🎯 Alternative Approaches

### Speed Run (Minimal Commands)

1. `take magical rope`
2. `go east` (to chasm)
3. `dash` (cross chasm)
4. `go east` (to treasury)
5. `take crystal` (trigger collapse)
6. `go west` (back to chasm)
7. `dash` (cross back)
8. `go west` (to entrance)
9. `go west` (VICTORY!)

**Total**: ~9 commands, ~5 minutes

### Thorough Explorer

- Visit all rooms including Collapsed Passage (dead end)
- Read all item descriptions
- Examine everything
- Collect all equipment
- Learn the layout before taking crystal
- Execute perfect escape

---

## 🗡️ Rogue Class Abilities

### Dash

- **Command**: `dash`
- **Effect**: Sprint forward at high speed
- **Best Used**: Crossing chasm, escaping collapse
- **Cooldown**: Limited uses

### Natural Dodge

- **Passive Ability**: Automatically dodge some falling rocks
- **Effect**: Reduces damage from environmental hazards
- **Advantage**: Better survivability during collapse

### Agility Bonus

- **Effect**: Higher success rate for acrobatic actions
- **Applies to**: Grappling hook, rope climbing, jumping

---

## ⚠️ Failure Scenarios to Avoid

### 1. Fall to Death

**How it happens:**

- Try to cross chasm without equipment or abilities
- Command: `go east` at chasm without crossing first

**Prevention:**

- Always use rope, grappling hook, or dash ability
- Secure rope before crossing

### 2. Trapped by Collapse

**How it happens:**

- Take too many turns after grabbing crystal
- Turn 7+: Cave seals shut

**Prevention:**

- Move quickly after taking crystal
- Use dash to save turns
- Don't explore or examine things during escape

### 3. Wrong Direction

**How it happens:**

- Go to Collapsed Passage (south from chasm) during escape
- It's a dead end!

**Prevention:**

- Always go WEST to escape
- Read the journal for the correct path

---

## 💡 Pro Tips for Rogue Players

1. **Dash is Your Friend**: Use it for both crossing and escape
2. **Equipment Still Helps**: Even with abilities, equipment reduces risk
3. **Read the Journal**: The explorer's journal literally tells you everything
4. **Anchor the Rope**: Secure rope at chasm for quick recross during escape
5. **Don't Panic**: You have 7 turns - that's plenty if you're decisive
6. **Trust Your Agility**: Rogues have the highest success rate for acrobatic moves

---

## 📊 Expected Gameplay Metrics

**Success Rate**: 70-90% (depending on equipment collection)
**Playtime**: 5-15 minutes
**Commands**: 9-30 (speed run vs thorough)
**Death Rate**: Higher than Warrior, lower than Wizard
**Fun Factor**: High - fast-paced and rewarding

---

## 🐛 Testing Commands

Want to test specific mechanics? Try these:

```
# Test inventory system
inventory
examine magical rope

# Test ability system
dash

# Test class-specific hints
examine chasm

# Test environmental effects
# (These only appear after taking crystal)
look around

# Test health status
# (Automatically shown if you take damage)
```

---

## 🎬 Narrative Highlights to Watch For

- **Opening**: Mysterious cave entrance descriptions
- **Discovery**: Finding the hidden alcove and journal
- **Challenge**: Standing at the edge of the chasm
- **Triumph**: Grabbing the crystal and triggering the trap
- **Tension**: Racing against the collapse
- **Victory**: Bursting out into daylight with the treasure!

---

## ✅ Victory Conditions

To win, you must:

1. ✅ Be at Cave Entrance
2. ✅ Have the crystal in inventory
3. ✅ Use command `go west` to exit

**Victory Narrative**: Epic description of your successful escape!

---

## 🎮 Ready to Play!

1. Open http://localhost:3000
2. Create character: Rogue named "ShadowBlade"
3. Follow the walkthrough above
4. Enjoy the adventure!

**Good luck, Shadow! May your reflexes be quick and your blade sharp!** 🗡️✨
