"""
Simplified game mechanics for AI agent demonstration.

This module provides minimal game mechanics to demonstrate
agent tool calling patterns, not to build a complete RPG.
"""
from typing import Dict, Optional
from enum import Enum


class GameStatus(str, Enum):
    """Game status states."""
    IN_PROGRESS = "in_progress"
    VICTORY = "victory"
    DEFEAT = "defeat"


class DefeatReason(str, Enum):
    """Reasons for game defeat."""
    HEALTH_DEPLETED = "health_depleted"



class SimpleAbilitySystem:
    """
    Minimal ability system to demonstrate AI agent tool calling.
    
    Each character class has simple abilities that agents can invoke.
    This showcases the tool use pattern without complex game mechanics.
    """
    
    ABILITIES = {
        "Warrior": {
            "dash": {
                "description": "Sprint forward with warrior strength",
                "cooldown": 0,
                "effect": "movement_boost"
            }
        },
        "Wizard": {
            "illuminate": {
                "description": "Create magical light to see in darkness",
                "cooldown": 0,
                "effect": "light"
            }
        },
        "Rogue": {
            "sneak": {
                "description": "Move silently through shadows",
                "cooldown": 0,
                "effect": "stealth"
            }
        }
    }
    
    @staticmethod
    def can_use_ability(ability_name: str, character_class: str) -> Dict:
        """
        Check if character can use the specified ability.
        
        Args:
            ability_name: Name of ability to check
            character_class: Character's class (Warrior/Wizard/Rogue)
            
        Returns:
            Dict with can_use (bool) and reason (str)
        """
        # Normalize inputs
        ability_name = ability_name.lower()
        
        # Check if class has this ability
        class_abilities = SimpleAbilitySystem.ABILITIES.get(character_class, {})
        
        if ability_name not in class_abilities:
            return {
                "can_use": False,
                "reason": f"{character_class}s don't have the '{ability_name}' ability."
            }
        
        return {
            "can_use": True,
            "reason": "",
            "ability": class_abilities[ability_name]
        }
    
    @staticmethod
    def use_ability(ability_name: str, character_class: str, game_state: Dict) -> Dict:
        """
        Execute a character ability.
        
        Args:
            ability_name: Name of ability to use
            character_class: Character's class
            game_state: Current game state
            
        Returns:
            Dict with success (bool), narrative (str), and effects (dict)
        """
        # Check if can use
        check = SimpleAbilitySystem.can_use_ability(ability_name, character_class)
        
        if not check["can_use"]:
            return {
                "success": False,
                "narrative": check["reason"],
                "effects": {}
            }
        
        ability = check["ability"]
        ability_name_normalized = ability_name.lower()
        
        # Generate class-specific narrative
        narratives = {
            "dash": f"You burst forward with {character_class.lower()} speed!",
            "illuminate": "Magical light blooms from your fingertips, illuminating the darkness.",
            "sneak": "You melt into the shadows, moving silently."
        }
        
        narrative = narratives.get(ability_name_normalized, f"You use {ability_name}!")
        
        # Simple effect (just for demonstration)
        effects = {
            "ability_used": ability_name_normalized,
            "effect_type": ability["effect"]
        }
        
        return {
            "success": True,
            "narrative": narrative,
            "effects": effects
        }
    
    @staticmethod
    def get_available_abilities(character_class: str) -> list:
        """
        Get list of abilities available to this character class.
        
        Args:
            character_class: Character's class
            
        Returns:
            List of ability names
        """
        return list(SimpleAbilitySystem.ABILITIES.get(character_class, {}).keys())
    
    @staticmethod
    def parse_ability_command(command: str, character_class: str) -> Dict:
        """
        Parse a command to check if it's an ability.
        
        Args:
            command: Player's command text
            character_class: Character's class
            
        Returns:
            Dict with is_ability (bool) and ability_name (str)
        """
        command_lower = command.lower()
        
        # Get abilities for this class
        available = SimpleAbilitySystem.get_available_abilities(character_class)
        
        # Check if any ability name appears in command
        for ability in available:
            if ability.lower() in command_lower:
                return {
                    "is_ability": True,
                    "ability_name": ability
                }
        
        # Also check for "use <ability>" pattern
        if "use" in command_lower or "cast" in command_lower:
            for ability in available:
                if ability.lower() in command_lower:
                    return {
                        "is_ability": True,
                        "ability_name": ability
                    }
        
        return {
            "is_ability": False,
            "ability_name": ""
        }


def check_victory_condition(session: Dict) -> bool:
    """
    Check if player has won the game.
    
    Victory: At cave entrance with crystal, exiting west.
    
    Args:
        session: Game session dict
        
    Returns:
        True if victory condition met
    """
    inventory = session.get("inventory", [])
    
    # Check if crystal is in inventory (handle both string and dict formats)
    has_crystal = False
    for item in inventory:
        if isinstance(item, str) and "crystal" in item:
            has_crystal = True
            break
        elif isinstance(item, dict) and "crystal" in item.get("id", ""):
            has_crystal = True
            break
    
    at_entrance = session.get("location") == "cave_entrance"
    
    return has_crystal and at_entrance


def check_defeat_conditions(session: Dict) -> Optional[DefeatReason]:
    """
    Check if player has been defeated.
    
    Currently simplified - only checks health.
    
    Args:
        session: Game session dict
        
    Returns:
        DefeatReason if defeated, None otherwise
    """
    character = session.get("character", {})
    health = character.get("health", 100)
    
    if health <= 0:
        return DefeatReason.HEALTH_DEPLETED
    
    return None


def update_game_status(session: Dict) -> str:
    """
    Update game status based on current conditions.
    
    Args:
        session: Game session dict
        
    Returns:
        Narrative string if status changed, empty string otherwise
    """
    # Check victory first
    if check_victory_condition(session):
        session["game_status"] = GameStatus.VICTORY
        return get_victory_narrative()
    
    # Check defeat
    defeat_reason = check_defeat_conditions(session)
    if defeat_reason:
        session["game_status"] = GameStatus.DEFEAT
        session["defeat_reason"] = defeat_reason
        return get_defeat_narrative(defeat_reason)
    
    # Otherwise in progress
    session.setdefault("game_status", GameStatus.IN_PROGRESS)
    return ""


def initialize_game_mechanics(session: Dict) -> None:
    """
    Initialize game mechanics fields in session.
    
    Args:
        session: Game session dict to initialize
    """
    # Game status
    session.setdefault("game_status", GameStatus.IN_PROGRESS)
    session.setdefault("defeat_reason", None)


def get_victory_narrative() -> str:
    """Get the victory narrative text."""
    return """
You burst from the cave entrance into blessed daylight, the Crystal of Echoing Depths
clutched triumphantly in your hands! The crystal pulses warmly in your grasp, 
its blue light glowing with ancient power.

The adventure is complete. The treasure is yours. Well done, brave adventurer!

🏆 VICTORY! 🏆
"""


def get_defeat_narrative(reason: Optional[DefeatReason]) -> str:
    """
    Get the defeat narrative text.
    
    Args:
        reason: Reason for defeat
        
    Returns:
        Narrative text for this defeat
    """
    if not reason:
        return ""
    
    if reason == DefeatReason.HEALTH_DEPLETED:
        return """
Your strength fails you. Your vision dims as you collapse to the cold stone floor.
The darkness of the cave claims another adventurer...

💀 DEFEAT - Your health has been depleted. 💀
"""
    
    return "The adventure has ended. Better luck next time, brave adventurer."
