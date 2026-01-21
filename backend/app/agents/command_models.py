"""Shared data models for command processing."""
from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field


class CommandType(str, Enum):
    """Types of commands the adventure narrator can handle."""
    MOVEMENT = "movement"
    EXAMINE = "examine"
    PICKUP = "pickup"
    DROP = "drop"
    USE = "use"
    TALK = "talk"
    ATTACK = "attack"
    LOOK = "look"
    INVENTORY = "inventory"
    ABILITY = "ability"
    UNKNOWN = "unknown"


class ParsedCommand(BaseModel):
    """Structured representation of a player command after parsing."""
    command_type: CommandType
    action: str = Field(description="The main action verb")
    target: Optional[str] = Field(default=None, description="Object being acted upon")
    direction: Optional[str] = Field(default=None, description="Movement direction")
    parameters: Dict = Field(default_factory=dict, description="Additional command parameters")
    confidence: float = Field(default=1.0, description="Parser confidence (0-1)")
