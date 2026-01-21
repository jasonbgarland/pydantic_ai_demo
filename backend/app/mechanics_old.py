"""
Game mechanics module for adventure engine.

Handles game systems like turn counters, collapse triggers,
environmental states, damage, and victory/defeat conditions.
"""
import random
from typing import Dict
from enum import Enum


class GameStatus(str, Enum):
    """Game status states."""
    ACTIVE = "active"
    VICTORY = "victory"
    DEFEAT = "defeat"


class DefeatReason(str, Enum):
    """Reasons for game defeat."""
    DEATH = "death"
    TRAPPED_BY_COLLAPSE = "trapped_by_collapse"
    TRAPPED_IN_DEAD_END = "trapped_in_dead_end"


class CollapseManager:
    """Manages the cave collapse system triggered by taking the crystal."""

    DEFAULT_TURN_LIMIT = 7

    @staticmethod
    def trigger_collapse(session: Dict) -> str:
        """
        Trigger the collapse sequence when crystal is taken.

        Args:
            session: Game session dict

        Returns:
            Narrative description of collapse starting
        """
        session["collapse_triggered"] = True
        session["turns_since_collapse"] = 0
        session["collapse_turn_limit"] = CollapseManager.DEFAULT_TURN_LIMIT

        return (
            "As you grasp the Crystal of Echoing Depths, a deep rumbling begins! "
            "The pedestal's pressure plate releases with a grinding sound. "
            "Ancient mechanisms activate throughout the cave system. "
            "The collapse has begun - you must escape immediately!"
        )

    @staticmethod
    def increment_collapse_turn(session: Dict) -> None:
        """
        Increment the turn counter during collapse sequence.

        Args:
            session: Game session dict
        """
        if session.get("collapse_triggered", False):
            session["turns_since_collapse"] = session.get("turns_since_collapse", 0) + 1

    @staticmethod
    def is_collapse_active(session: Dict) -> bool:
        """Check if collapse is currently active."""
        return session.get("collapse_triggered", False)

    @staticmethod
    def get_turns_since_collapse(session: Dict) -> int:
        """Get number of turns since collapse started."""
        return session.get("turns_since_collapse", 0)

    @staticmethod
    def get_turn_limit(session: Dict) -> int:
        """Get the turn limit before critical failure."""
        return session.get("collapse_turn_limit", CollapseManager.DEFAULT_TURN_LIMIT)

    @staticmethod
    def is_time_running_out(session: Dict) -> bool:
        """Check if player is running out of time (>= turn limit)."""
        if not CollapseManager.is_collapse_active(session):
            return False

        turns = CollapseManager.get_turns_since_collapse(session)
        limit = CollapseManager.get_turn_limit(session)
        return turns >= limit

    @staticmethod
    def get_urgency_level(session: Dict) -> str:
        """
        Get urgency level based on turns elapsed.

        Returns:
            "none", "minor", "moderate", "severe", or "critical"
        """
        if not CollapseManager.is_collapse_active(session):
            return "none"

        turns = CollapseManager.get_turns_since_collapse(session)

        if turns == 0:
            return "none"
        if turns <= 2:
            return "minor"
        if turns <= 4:
            return "moderate"
        if turns <= 6:
            return "severe"
        return "critical"

    @staticmethod
    def get_collapse_narrative(session: Dict) -> str:
        """
        Get narrative description based on collapse progression.

        Returns:
            String describing current collapse state
        """
        urgency = CollapseManager.get_urgency_level(session)
        turns = CollapseManager.get_turns_since_collapse(session)

        narratives = {
            "none": "",
            "minor": (
                f"[Turn {turns}/{CollapseManager.get_turn_limit(session)}] "
                "Small rocks tumble from the ceiling. You hear ominous creaking. "
                "Move quickly!"
            ),
            "moderate": (
                f"[Turn {turns}/{CollapseManager.get_turn_limit(session)}] "
                "Rocks crash down around you! The ceiling cracks ominously. "
                "The collapse is intensifying!"
            ),
            "severe": (
                f"[Turn {turns}/{CollapseManager.get_turn_limit(session)}] "
                "HEAVY ROCKFALL! Boulders smash into the ground! "
                "The cave is coming down - RUN!"
            ),
            "critical": (
                f"[Turn {turns}/{CollapseManager.get_turn_limit(session)}] "
                "CRITICAL COLLAPSE! Massive sections of ceiling give way! "
                "Passages are sealing shut! ESCAPE NOW!"
            )
        }

        return narratives.get(urgency, "")


class EnvironmentalState:
    """Manages environmental state changes during collapse."""

    # Environmental state data by urgency level
    ENVIRONMENTAL_EFFECTS = {
        "none": {
            "description": "",
            "damage_chance": 0.0,
            "damage_amount": 0,
            "room_modifier": ""
        },
        "minor": {
            "description": "Small rocks tumble from the ceiling. Dust fills the air.",
            "damage_chance": 0.1,
            "damage_amount": 5,
            "room_modifier": "The walls tremble. Small rocks rain down intermittently."
        },
        "moderate": {
            "description": "Rocks crash down! The ceiling cracks ominously!",
            "damage_chance": 0.3,
            "damage_amount": 10,
            "room_modifier": (
                "Cracks spread across the ceiling! "
                "Larger rocks fall with alarming frequency!"
            )
        },
        "severe": {
            "description": "HEAVY ROCKFALL! Boulders smash into the ground!",
            "damage_chance": 0.6,
            "damage_amount": 20,
            "room_modifier": (
                "MASSIVE ROCKFALL! The ceiling is giving way! "
                "Boulders crash down everywhere!"
            )
        },
        "critical": {
            "description": "CRITICAL COLLAPSE! The cave is sealing shut!",
            "damage_chance": 0.9,
            "damage_amount": 30,
            "room_modifier": (
                "TOTAL COLLAPSE! Entire sections of ceiling crash down! "
                "Passages sealing!"
            )
        }
    }

    @staticmethod
    def get_environmental_state(session: Dict) -> str:
        """
        Get current environmental state based on collapse progression.

        Args:
            session: Game session dict

        Returns:
            Environmental state key: "none", "minor", "moderate", "severe", or "critical"
        """
        if not CollapseManager.is_collapse_active(session):
            return "none"

        return CollapseManager.get_urgency_level(session)

    @staticmethod
    def get_room_modifier(session: Dict) -> str:
        """
        Get room description modifier based on environmental state.

        This text should be appended to room descriptions during collapse.

        Args:
            session: Game session dict

        Returns:
            Additional text to append to room description
        """
        state = EnvironmentalState.get_environmental_state(session)
        return EnvironmentalState.ENVIRONMENTAL_EFFECTS[state]["room_modifier"]

    @staticmethod
    def get_damage_chance(session: Dict) -> float:
        """
        Get chance of taking environmental damage.

        Args:
            session: Game session dict

        Returns:
            Probability of damage (0.0 to 1.0)
        """
        state = EnvironmentalState.get_environmental_state(session)
        return EnvironmentalState.ENVIRONMENTAL_EFFECTS[state]["damage_chance"]

    @staticmethod
    def get_damage_amount(session: Dict) -> int:
        """
        Get base damage amount for current environmental state.

        Args:
            session: Game session dict

        Returns:
            Base damage amount (before class modifiers)
        """
        state = EnvironmentalState.get_environmental_state(session)
        return EnvironmentalState.ENVIRONMENTAL_EFFECTS[state]["damage_amount"]

    @staticmethod
    def should_apply_environmental_modifier(session: Dict, location: str) -> bool:
        """
        Check if environmental modifiers should be applied to this location.

        Args:
            session: Game session dict
            location: Current location name

        Returns:
            True if environmental effects should be shown
        """
        # Only apply during active collapse
        if not CollapseManager.is_collapse_active(session):
            return False

        # Apply to all indoor locations except the outside
        excluded_locations = ["outside", "exit", "escaped"]
        return location.lower() not in excluded_locations


class DamageSystem:
    """Manages damage calculation and application."""

    # Class-specific damage reduction percentages
    CLASS_DAMAGE_REDUCTION = {
        "Warrior": 0.5,   # Warriors tank damage - 50% reduction
        "Wizard": 0.3,    # Wizards have magical shields - 30% reduction
        "Rogue": 0.4      # Rogues dodge - 40% reduction
    }

    @staticmethod
    def calculate_damage(base_damage: int, character_class: str) -> int:
        """
        Calculate actual damage after applying class-specific reduction.

        Args:
            base_damage: Base damage amount before reduction
            character_class: Character class name

        Returns:
            Actual damage amount after class reduction
        """
        reduction = DamageSystem.CLASS_DAMAGE_REDUCTION.get(character_class, 0.0)
        actual_damage = int(base_damage * (1.0 - reduction))
        return max(0, actual_damage)  # Ensure non-negative

    @staticmethod
    def apply_environmental_damage(session: Dict) -> Dict[str, any]:
        """
        Apply environmental damage during collapse.

        Uses damage chance from environmental state to determine if damage occurs,
        then applies class-specific damage reduction.

        Args:
            session: Game session dict

        Returns:
            Dict with:
                - damage_applied: int (actual damage dealt)
                - damage_occurred: bool (whether damage was dealt)
                - narrative: str (description of damage or avoidance)
        """
        result = {
            "damage_applied": 0,
            "damage_occurred": False,
            "narrative": ""
        }

        # Only apply damage during active collapse
        if not CollapseManager.is_collapse_active(session):
            return result

        # Get damage parameters from environmental state
        damage_chance = EnvironmentalState.get_damage_chance(session)
        base_damage = EnvironmentalState.get_damage_amount(session)

        # Roll for damage
        if random.random() < damage_chance:
            # Damage occurs - apply class reduction
            character_class = session.get("character", {}).get("class", "")
            actual_damage = DamageSystem.calculate_damage(base_damage, character_class)

            # Apply damage to health
            current_health = session.get("current_health", 100)
            new_health = max(0, current_health - actual_damage)
            session["current_health"] = new_health

            result["damage_applied"] = actual_damage
            result["damage_occurred"] = True
            result["narrative"] = DamageSystem.get_damage_narrative(
                actual_damage, character_class, new_health
            )

        return result

    @staticmethod
    def get_damage_narrative(damage: int, character_class: str, remaining_health: int) -> str:
        """
        Generate narrative description of damage taken.

        Args:
            damage: Amount of damage taken
            character_class: Character class name
            remaining_health: Health remaining after damage

        Returns:
            Narrative description of the damage event
        """
        # Class-specific damage narratives
        class_narratives = {
            "Warrior": [
                (
                    f"A boulder crashes down! You raise your shield, "
                    f"absorbing most of the impact. (-{damage} HP)"
                ),
                (
                    f"Rocks rain down on you! "
                    f"Your armor deflects the worst of it. (-{damage} HP)"
                ),
                (
                    f"You brace yourself as debris falls! "
                    f"Your warrior training minimizes the damage. (-{damage} HP)"
                )
            ],
            "Wizard": [
                (
                    f"Falling rocks strike! Your magical shield flares, "
                    f"reducing the impact. (-{damage} HP)"
                ),
                (
                    f"Debris crashes around you! "
                    f"Your protective ward absorbs some damage. (-{damage} HP)"
                ),
                (
                    f"Rocks fall! "
                    f"Your arcane barrier partially deflects them. (-{damage} HP)"
                )
            ],
            "Rogue": [
                f"Rocks fall! You twist aside, but can't avoid them all. (-{damage} HP)",
                (
                    f"Debris rains down! "
                    f"Your reflexes save you from the worst. (-{damage} HP)"
                ),
                f"You dodge falling rocks, but one clips you. (-{damage} HP)"
            ]
        }

        narratives = class_narratives.get(
            character_class,
            [f"Falling rocks strike you! (-{damage} HP)"]
        )

        narrative = random.choice(narratives)

        # Add health warning if low
        if remaining_health <= 20:
            narrative += f" ⚠️ CRITICAL HEALTH: {remaining_health} HP remaining!"
        elif remaining_health <= 50:
            narrative += f" Health: {remaining_health} HP"

        return narrative


class AbilitySystem:
    """Manages class-specific abilities and their execution."""

    # Define abilities for each class
    ABILITIES = {
        "Warrior": {
            "jump": {
                "description": "Leap across the chasm using raw strength",
                "locations": ["yawning_chasm"],
                "success_rate": 0.7,
                "can_fail": True
            },
            "break": {
                "description": "Smash through obstacles with brute force",
                "targets": ["rocks", "boulder", "debris"],
                "success_rate": 0.8,
                "can_fail": True
            }
        },
        "Wizard": {
            "cast_shield": {
                "description": "Create magical barrier to block next damage",
                "duration_turns": 1,
                "success_rate": 1.0,
                "can_fail": False
            },
            "cast_levitate": {
                "description": "Float across the chasm safely",
                "locations": ["yawning_chasm"],
                "success_rate": 0.9,
                "can_fail": True
            },
            "cast_telekinesis": {
                "description": "Move objects from a distance",
                "targets": ["crystal", "rope", "rocks"],
                "success_rate": 0.85,
                "can_fail": True
            }
        },
        "Rogue": {
            "scale": {
                "description": "Climb walls to find alternate paths",
                "locations": ["yawning_chasm", "hidden_alcove"],
                "success_rate": 0.8,
                "can_fail": True
            },
            "dash": {
                "description": "Sprint across the chasm at high speed",
                "locations": ["yawning_chasm"],
                "success_rate": 0.75,
                "can_fail": True
            },
            "dodge": {
                "description": "Enhanced dodge for next turn (passive)",
                "duration_turns": 1,
                "success_rate": 1.0,
                "can_fail": False
            }
        }
    }

    @staticmethod
    def parse_ability_command(command: str, character_class: str) -> Dict[str, any]:
        """
        Parse a command to check if it's an ability use.

        Args:
            command: User command string
            character_class: Character class name

        Returns:
            Dict with:
                - is_ability: bool (whether command is an ability)
                - ability_name: str (ability key)
                - target: str (optional target)
        """
        result = {
            "is_ability": False,
            "ability_name": None,
            "target": None
        }

        command_lower = command.lower()

        # Get abilities for this class
        class_abilities = AbilitySystem.ABILITIES.get(character_class, {})

        # Check each ability
        for ability_key, ability_data in class_abilities.items():
            # Handle multi-word abilities (e.g., "cast_shield" -> "cast shield")
            ability_phrases = [
                ability_key,
                ability_key.replace("_", " "),
            ]

            for phrase in ability_phrases:
                if phrase not in command_lower:
                    continue

                result["is_ability"] = True
                result["ability_name"] = ability_key

                # Extract target if present
                if "targets" in ability_data:
                    words = command_lower.split()
                    for target in ability_data["targets"]:
                        if any(target in word for word in words):
                            result["target"] = target
                            break

                return result

        return result

    @staticmethod
    def can_use_ability(
            ability_name: str,
            character_class: str,
            location: str,
            target: str = None
    ) -> Dict[str, any]:
        """
        Check if an ability can be used in current context.

        Args:
            ability_name: Ability key
            character_class: Character class name
            location: Current location
            target: Optional target object

        Returns:
            Dict with:
                - can_use: bool
                - reason: str (explanation if cannot use)
        """
        result = {"can_use": True, "reason": ""}

        # Check if class has this ability
        class_abilities = AbilitySystem.ABILITIES.get(character_class, {})
        if ability_name not in class_abilities:
            return {
                "can_use": False,
                "reason": f"{character_class}s don't have the '{ability_name}' ability."
            }

        ability = class_abilities[ability_name]

        # Check location restrictions
        if "locations" in ability:
            if location not in ability["locations"]:
                return {
                    "can_use": False,
                    "reason": f"You can't use {ability_name} here."
                }

        # Check target restrictions
        if "targets" in ability and target:
            if target not in ability["targets"]:
                return {
                    "can_use": False,
                    "reason": f"You can't use {ability_name} on {target}."
                }

        return result

    @staticmethod
    def _execute_warrior_ability(
            ability_name: str, success: bool, target: str, session: Dict  # pylint: disable=unused-argument
    ) -> tuple:
        """Execute warrior abilities. Returns (narrative, effects)."""
        effects = {}
        if ability_name == "jump":
            if success:
                narrative = (
                    "You gather your strength and LEAP across the chasm! "
                    "Your warrior training pays off - you land safely on the other side!"
                )
                effects["crossed_chasm"] = True
            else:
                narrative = (
                    "You attempt to jump, but misjudge the distance! "
                    "You barely catch the edge and pull yourself up. (-15 HP)"
                )
                effects["damage_taken"] = 15
        elif ability_name == "break":
            if success:
                narrative = (
                    f"You raise your weapon and SMASH through the {target or 'obstacle'}! "
                    "Debris scatters everywhere. The path is clear!"
                )
                effects[f"broke_{target or 'obstacle'}"] = True
            else:
                narrative = (
                    f"You strike the {target or 'obstacle'}, but it holds firm. "
                    "The impact jars your arm. (-5 HP)"
                )
                effects["damage_taken"] = 5
        else:
            narrative = "Unknown warrior ability."

        return narrative, effects

    @staticmethod
    def _execute_wizard_ability(
            ability_name: str, success: bool, target: str, ability_data: Dict
    ) -> tuple:
        """Execute wizard abilities. Returns (narrative, effects)."""
        effects = {}
        if ability_name == "cast_shield":
            narrative = (
                "You weave arcane energy into a shimmering barrier! "
                "The next source of damage will be completely blocked."
            )
            effects["shield_active"] = True
            effects["shield_turns_remaining"] = ability_data.get("duration_turns", 1)
        elif ability_name == "cast_levitate":
            if success:
                narrative = (
                    "You speak words of power and float gracefully across the chasm! "
                    "Magic carries you safely to the other side."
                )
                effects["crossed_chasm"] = True
            else:
                narrative = (
                    "You begin to levitate, but the spell falters mid-chasm! "
                    "You fall but manage to grab a ledge. (-10 HP)"
                )
                effects["damage_taken"] = 10
        elif ability_name == "cast_telekinesis":
            if success:
                narrative = (
                    f"You focus your mind and the {target or 'object'} "
                    f"rises into the air, obeying your will!"
                )
                effects[f"moved_{target or 'object'}"] = True
            else:
                narrative = (
                    "You concentrate hard, but the mental strain is too much. "
                    "The object slips from your telekinetic grasp."
                )
        else:
            narrative = "Unknown wizard ability."

        return narrative, effects

    @staticmethod
    def _execute_rogue_ability(
            ability_name: str, success: bool, session: Dict, ability_data: Dict
    ) -> tuple:
        """Execute rogue abilities. Returns (narrative, effects)."""
        effects = {}
        if ability_name == "scale":
            if success:
                if session.get("location") == "yawning_chasm":
                    narrative = (
                        "You scale down the chasm wall with practiced ease, "
                        "finding handholds invisible to others. "
                        "You reach the bottom and cross safely!"
                    )
                    effects["crossed_chasm"] = True
                else:
                    narrative = (
                        "You climb the walls, discovering a hidden ledge! "
                        "From here, you can see things others would miss."
                    )
                    effects["found_secret"] = True
            else:
                narrative = (
                    "You begin climbing but a handhold crumbles! "
                    "You fall a short distance. (-8 HP)"
                )
                effects["damage_taken"] = 8
        elif ability_name == "dash":
            if success:
                narrative = (
                    "You sprint forward and DASH across the chasm at incredible speed! "
                    "Your momentum carries you safely across!"
                )
                effects["crossed_chasm"] = True
            else:
                narrative = (
                    "You dash forward but slip near the edge! "
                    "You catch yourself but twist your ankle. (-12 HP)"
                )
                effects["damage_taken"] = 12
        elif ability_name == "dodge":
            narrative = (
                "You enter a heightened state of awareness. "
                "Your reflexes are enhanced for the next turn!"
            )
            effects["dodge_active"] = True
            effects["dodge_turns_remaining"] = ability_data.get("duration_turns", 1)
        else:
            narrative = "Unknown rogue ability."

        return narrative, effects

    @staticmethod
    def execute_ability(
            ability_name: str,
            character_class: str,
            session: Dict,
            target: str = None
    ) -> Dict[str, any]:
        """
        Execute an ability and return results.

        Args:
            ability_name: Ability key
            character_class: Character class name
            session: Game session dict
            target: Optional target

        Returns:
            Dict with:
                - success: bool
                - narrative: str
                - effects: Dict (state changes to apply)
        """
        class_abilities = AbilitySystem.ABILITIES.get(character_class, {})
        ability = class_abilities.get(ability_name, {})

        # Roll for success
        success_rate = ability.get("success_rate", 1.0)
        success = random.random() < success_rate

        # Execute class-specific ability
        if character_class == "Warrior":
            narrative, effects = AbilitySystem._execute_warrior_ability(
                ability_name, success, target, session
            )
        elif character_class == "Wizard":
            narrative, effects = AbilitySystem._execute_wizard_ability(
                ability_name, success, target, ability
            )
        elif character_class == "Rogue":
            narrative, effects = AbilitySystem._execute_rogue_ability(
                ability_name, success, session, ability
            )
        else:
            narrative = "Unknown character class."
            effects = {}

        # Apply damage if ability failed and caused damage
        if "damage_taken" in effects:
            current_health = session.get("current_health", 100)
            session["current_health"] = max(0, current_health - effects["damage_taken"])

        # Apply other effects to session
        for key, value in effects.items():
            if key not in ["damage_taken"]:
                session[key] = value

        return {
            "success": success,
            "narrative": narrative,
            "effects": effects
        }

    @staticmethod
    def get_available_abilities(character_class: str, location: str = None) -> list:
        """
        Get list of abilities available to a character class.

        Args:
            character_class: Character class name
            location: Optional location to filter location-specific abilities

        Returns:
            List of ability names with descriptions
        """
        class_abilities = AbilitySystem.ABILITIES.get(character_class, {})
        available = []

        for ability_name, ability_data in class_abilities.items():
            # Check location restrictions
            if location and "locations" in ability_data:
                if location not in ability_data["locations"]:
                    continue

            available.append({
                "name": ability_name,
                "description": ability_data["description"]
            })

        return available


class GrappleSystem:
    """Manages the grappling hook mechanic for crossing gaps."""

    @staticmethod
    def can_use_grapple(session: Dict) -> Dict[str, any]:
        """
        Check if grappling hook can be used at current location.

        Args:
            session: Game session dict

        Returns:
            Dict with:
                - can_use: bool
                - reason: str (explanation if cannot use)
                - success_chance: float (0-1, varies by class)
        """
        location = session.get("location", "")
        inventory = session.get("inventory", [])
        character_class = session.get("character_class", "Warrior")

        # Must have the grappling hook
        if "grappling_hook" not in inventory:
            return {
                "can_use": False,
                "reason": "You don't have a grappling hook.",
                "success_chance": 0.0
            }

        # Must be at the chasm
        if location != "yawning_chasm":
            return {
                "can_use": False,
                "reason": "There's nowhere appropriate to use the grappling hook here.",
                "success_chance": 0.0
            }

        # Already crossed
        if session.get("crossed_chasm", False):
            return {
                "can_use": False,
                "reason": "You're already across the chasm.",
                "success_chance": 0.0
            }

        # Class-specific success rates
        success_chances = {
            "Warrior": 0.85,  # High strength for throwing, good success rate
            "Wizard": 0.75,   # Can use magic to guide hook, decent success
            "Rogue": 0.95     # Agility and precision, best success rate
        }

        return {
            "can_use": True,
            "reason": "",
            "success_chance": success_chances.get(character_class, 0.8)
        }

    @staticmethod
    def use_grapple(session: Dict) -> Dict[str, any]:
        """
        Use the grappling hook to cross the chasm.

        Args:
            session: Game session dict

        Returns:
            Dict with:
                - success: bool
                - narrative: str
                - effects: Dict (state changes)
        """
        can_use = GrappleSystem.can_use_grapple(session)
        if not can_use["can_use"]:
            return {
                "success": False,
                "narrative": can_use["reason"],
                "effects": {}
            }

        # Roll for success
        character_class = session.get("character_class", "Warrior")
        roll = random.random()
        success_chance = can_use["success_chance"]

        if roll <= success_chance:
            # Success - class-specific narratives
            narratives = {
                "Warrior": (
                    "You hurl the grappling hook with tremendous force! "
                    "It arcs across the chasm and catches on a sturdy outcropping. "
                    "You test the rope with a mighty pull - it holds firm. "
                    "Hand over hand, you cross the chasm with raw strength!"
                ),
                "Wizard": (
                    "You focus your will and throw the grappling hook. "
                    "A whisper of telekinetic magic guides it to a perfect anchor point. "
                    "The hook catches securely. You grip the rope and pull yourself across, "
                    "using minor levitation to reduce the strain."
                ),
                "Rogue": (
                    "With practiced precision, you whirl the grappling hook and release! "
                    "It sails across the chasm in a perfect arc, hooking onto a solid ledge. "
                    "You give it a quick test tug, then swing across with acrobatic grace. "
                    "Your agility makes it look effortless!"
                )
            }

            narrative = narratives.get(
                character_class,
                "You throw the grappling hook across the chasm. "
                "It catches securely and you pull yourself across!"
            )

            effects = {"crossed_chasm": True}

            return {
                "success": True,
                "narrative": narrative,
                "effects": effects
            }

        # Failure - take damage but not fatal
        damage = 15
        current_health = session.get("current_health", 100)
        new_health = max(0, current_health - damage)
        session["current_health"] = new_health

        failure_narratives = {
            "Warrior": (
                f"You throw with great strength, but the hook skitters off the stone! "
                f"You stumble, barking your shin against the edge. (-{damage} HP) "
                "You can try again."
            ),
            "Wizard": (
                f"Your throw lacks power and the hook falls short! "
                f"It swings back and clips your shoulder. (-{damage} HP) "
                "You can try again."
            ),
            "Rogue": (
                f"The hook catches for a moment, then slips free! "
                f"You twist away from the falling gear, wrenching your arm. (-{damage} HP) "
                "You can try again."
            )
        }

        narrative = failure_narratives.get(
            character_class,
            f"The grappling hook misses its mark! You take some damage. (-{damage} HP)"
        )

        return {
            "success": False,
            "narrative": narrative,
            "effects": {"current_health": new_health}
        }


class RopeSystem:
    """Manages rope anchoring and crossing mechanics."""

    @staticmethod
    def can_anchor_rope(session: Dict) -> Dict[str, any]:
        """
        Check if rope can be anchored at current location.

        Args:
            session: Game session dict

        Returns:
            Dict with:
                - can_anchor: bool
                - reason: str (explanation if cannot anchor)
        """
        location = session.get("location", "")
        inventory = session.get("inventory", [])

        # Must have the magical rope
        has_rope = any("rope" in item.lower() for item in inventory)
        if not has_rope:
            return {
                "can_anchor": False,
                "reason": "You don't have a rope to anchor."
            }

        # Must be at the yawning chasm
        if location != "yawning_chasm":
            return {
                "can_anchor": False,
                "reason": "You can only anchor the rope at the yawning chasm."
            }

        # Check if already anchored
        if session.get("rope_anchored", False):
            return {
                "can_anchor": False,
                "reason": "The rope is already anchored here."
            }

        return {"can_anchor": True, "reason": ""}

    @staticmethod
    def anchor_rope(session: Dict) -> Dict[str, any]:
        """
        Anchor the magical rope at the chasm.

        Args:
            session: Game session dict

        Returns:
            Dict with:
                - success: bool
                - narrative: str
        """
        can_anchor = RopeSystem.can_anchor_rope(session)
        if not can_anchor["can_anchor"]:
            return {
                "success": False,
                "narrative": can_anchor["reason"]
            }

        # Anchor the rope
        session["rope_anchored"] = True
        session["rope_anchor_location"] = session.get("location", "yawning_chasm")

        narrative = (
            "You secure the magical rope to a sturdy outcropping. "
            "Its enchanted fibers grip the rock firmly. "
            "The rope stretches across the chasm, ready for quick crossing!"
        )

        return {
            "success": True,
            "narrative": narrative
        }

    @staticmethod
    def can_use_rope(session: Dict) -> Dict[str, any]:
        """
        Check if rope can be used for crossing.

        Args:
            session: Game session dict

        Returns:
            Dict with:
                - can_use: bool
                - reason: str (explanation if cannot use)
        """
        location = session.get("location", "")

        # Must be at the chasm
        if location != "yawning_chasm":
            return {
                "can_use": False,
                "reason": "There's no rope here to use."
            }

        # Rope must be anchored
        if not session.get("rope_anchored", False):
            return {
                "can_use": False,
                "reason": "The rope isn't anchored yet. You need to anchor it first."
            }

        return {"can_use": True, "reason": ""}

    @staticmethod
    def use_rope(session: Dict) -> Dict[str, any]:
        """
        Use the anchored rope to cross the chasm.

        Args:
            session: Game session dict

        Returns:
            Dict with:
                - success: bool
                - narrative: str
                - effects: Dict (state changes)
        """
        can_use = RopeSystem.can_use_rope(session)
        if not can_use["can_use"]:
            return {
                "success": False,
                "narrative": can_use["reason"],
                "effects": {}
            }

        # Successfully use rope
        narrative = (
            "You grab the anchored rope and swing across the chasm! "
            "The magical rope holds firm, carrying you safely to the other side. "
            "This is much faster than climbing or using abilities!"
        )

        effects = {"crossed_chasm": True}

        return {
            "success": True,
            "narrative": narrative,
            "effects": effects
        }

    @staticmethod
    def is_rope_anchored(session: Dict) -> bool:
        """
        Check if rope is currently anchored.

        Args:
            session: Game session dict

        Returns:
            True if rope is anchored
        """
        return session.get("rope_anchored", False)


def initialize_game_mechanics(session: Dict) -> None:
    """
    Initialize game mechanics fields in a new session.

    Args:
        session: Game session dict to initialize
    """
    # Turn counter system
    session.setdefault("turn_count", 0)

    # Health system
    session.setdefault("current_health", 100)
    session.setdefault("max_health", 100)

    # Collapse system
    session.setdefault("collapse_triggered", False)
    session.setdefault("turns_since_collapse", 0)
    session.setdefault("collapse_turn_limit", CollapseManager.DEFAULT_TURN_LIMIT)

    # Rope system
    session.setdefault("rope_anchored", False)
    session.setdefault("rope_anchor_location", None)

    # Game status
    session.setdefault("status", GameStatus.ACTIVE)
    session.setdefault("defeat_reason", None)


def should_trigger_collapse(command: str, session: Dict) -> bool:
    """
    Check if command should trigger the collapse sequence.

    Args:
        command: Player command string
        session: Game session dict

    Returns:
        True if collapse should trigger, False otherwise
    """
    cmd_lower = command.lower()

    # Check if taking the crystal
    is_take_command = any(word in cmd_lower for word in ["take", "grab", "get", "pick up"])
    is_crystal = "crystal" in cmd_lower
    at_treasury = session.get("location", "") == "crystal_treasury"
    not_already_triggered = not session.get("collapse_triggered", False)

    return is_take_command and is_crystal and at_treasury and not_already_triggered


def check_victory_condition(session: Dict) -> bool:
    """
    Check if player has achieved victory.

    Victory conditions:
    - Player has the crystal in inventory
    - Player is at cave_entrance (starting location)
    - This represents successfully escaping with the treasure

    Args:
        session: Game session dict

    Returns:
        True if victory achieved, False otherwise
    """
    has_crystal = "crystal_of_echoing_depths" in session.get("inventory", [])
    at_entrance = session.get("location", "").lower() == "cave_entrance"

    # Alternative victory: Successfully escaped (went west from entrance with crystal)
    # This would be indicated by a special location or flag
    escaped = session.get("escaped", False)

    return (has_crystal and at_entrance) or escaped


def check_defeat_conditions(session: Dict) -> tuple[bool, str]:
    """
    Check if player has been defeated.

    Defeat conditions:
    1. Health <= 0 (death from damage)
    2. Collapse turn limit exceeded (trapped by cave-in)
    3. At dead end (collapsed_passage) when time is critical

    Args:
        session: Game session dict

    Returns:
        Tuple of (is_defeated: bool, reason: str)
        Reason will be empty string if not defeated
    """
    # Health check (if health system is implemented)
    current_health = session.get("current_health", 100)
    if current_health <= 0:
        return (True, DefeatReason.DEATH)

    # Dead end trap (at collapsed_passage during critical collapse)
    # Check this BEFORE general time limit to give specific message
    if session.get("location", "") == "collapsed_passage":
        if CollapseManager.is_collapse_active(session):
            urgency = CollapseManager.get_urgency_level(session)
            if urgency in ["severe", "critical"]:
                # Player is at dead end with little time left
                return (True, DefeatReason.TRAPPED_IN_DEAD_END)

    # General collapse timer check
    if CollapseManager.is_time_running_out(session):
        # Player ran out of time during collapse
        return (True, DefeatReason.TRAPPED_BY_COLLAPSE)

    return (False, "")


def update_game_status(session: Dict) -> str:
    """
    Update game status based on victory and defeat conditions.

    Args:
        session: Game session dict (will be modified)

    Returns:
        Status message or empty string if no status change
    """
    # Check victory first (takes precedence)
    if check_victory_condition(session):
        session["status"] = GameStatus.VICTORY
        return get_victory_narrative()

    # Check defeat conditions
    is_defeated, reason = check_defeat_conditions(session)
    if is_defeated:
        session["status"] = GameStatus.DEFEAT
        session["defeat_reason"] = reason
        return get_defeat_narrative(reason)

    # Still active
    session["status"] = GameStatus.ACTIVE
    return ""


def get_victory_narrative() -> str:
    """Get narrative text for victory condition."""
    return (
        "\n\n═══════════════════════════════════════════════════════════\n"
        "🏆 VICTORY! 🏆\n"
        "═══════════════════════════════════════════════════════════\n\n"
        "You burst from the cave entrance into blessed daylight, the Crystal of "
        "Echoing Depths clutched triumphantly in your hands!\n\n"
        "Behind you, the cave system groans and collapses with a thunderous roar, "
        "sealing the treasury forever. Dust billows from the entrance as the rumbling "
        "subsides.\n\n"
        "You've succeeded where countless others failed. The crystal pulses warmly "
        "in your grasp, its blue light dimming now that you're safe.\n\n"
        "The adventure is complete. The treasure is yours. Well done, brave adventurer!"
    )


def get_defeat_narrative(reason: str) -> str:
    """
    Get narrative text for defeat condition.

    Args:
        reason: DefeatReason enum value or string

    Returns:
        Narrative description of defeat
    """
    narratives = {
        DefeatReason.DEATH: (
            "\n\n═══════════════════════════════════════════════════════════\n"
            "💀 DEFEAT - DEATH 💀\n"
            "═══════════════════════════════════════════════════════════\n\n"
            "Your vision fades as injuries overwhelm you. The darkness of the cave "
            "becomes permanent.\n\n"
            "The cave claims another victim. Your adventure ends here.\n\n"
            "GAME OVER"
        ),
        DefeatReason.TRAPPED_BY_COLLAPSE: (
            "\n\n═══════════════════════════════════════════════════════════\n"
            "💀 DEFEAT - TRAPPED 💀\n"
            "═══════════════════════════════════════════════════════════\n\n"
            "The final boulder seals the passage with a thunderous crash. "
            "You're trapped in darkness.\n\n"
            "Your torch flickers and dies. The cave system has become your tomb.\n\n"
            "You took too long to escape. GAME OVER"
        ),
        DefeatReason.TRAPPED_IN_DEAD_END: (
            "\n\n═══════════════════════════════════════════════════════════\n"
            "💀 DEFEAT - DEAD END 💀\n"
            "═══════════════════════════════════════════════════════════\n\n"
            "You realize too late - the collapsed passage has no exit!\n\n"
            "The cave-in seals you in this dead end. The rumbling intensifies "
            "as the ceiling gives way.\n\n"
            "You went the wrong direction during the collapse. GAME OVER"
        )
    }

    return narratives.get(reason, narratives[DefeatReason.DEATH])
