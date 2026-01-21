"""Intent Parser Agent - AI-powered command classification.

This agent demonstrates the Classification Pattern:
- Takes unstructured natural language input
- Uses AI to understand player intent
- Returns structured ParsedCommand output

This replaces 192 lines of manual parsing rules with AI-powered classification.
"""
from typing import Optional
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field

from app.agents.command_models import CommandType, ParsedCommand


class IntentClassification(BaseModel):
    """AI's classification of player intent."""
    command_type: str = Field(description="Type of command: movement, examine, pickup, drop, use, talk, attack, look, inventory, ability, or unknown")
    action: str = Field(description="The main action verb (e.g., 'go', 'examine', 'take')")
    target: Optional[str] = Field(default=None, description="Object or entity being acted upon (e.g., 'crystal', 'door')")
    direction: Optional[str] = Field(default=None, description="Direction for movement (north, south, east, west, up, down, chasm, etc.)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in classification (0-1)")


# System prompt that teaches the AI how to classify commands
SYSTEM_PROMPT = """You are an expert at understanding player intent in text adventure games.

Your job is to classify natural language commands into structured intents.

Command Types:
- movement: Player wants to move (go north, walk east, head south, cross chasm, etc.)
- examine: Player wants to look at something (examine crystal, look at door, inspect wall)
- pickup: Player wants to take an item (take crystal, grab rope, pick up torch)
- drop: Player wants to drop an item (drop sword, put down shield)
- use: Player wants to use an item (use key, activate lever, apply bandage)
- talk: Player wants to talk to someone (talk to guard, speak with wizard)
- attack: Player wants to attack something (attack goblin, hit door)
- look: Player wants to look around the current location (look, look around)
- inventory: Player wants to check inventory (inventory, check bag, what do I have)
- ability: Player wants to use a class ability (dash, illuminate, sneak, cast shield)
- unknown: Command doesn't fit any category or is unclear

Movement directions include: north, south, east, west, up, down, chasm (special)

Examples:
- "go north" → movement, action=go, direction=north
- "grab the shiny crystal" → pickup, action=grab, target=crystal
- "what's in my bag?" → inventory, action=inventory
- "examine the ancient door" → examine, action=examine, target=door
- "dash to the exit" → ability, action=ability, target=dash
- "cross the chasm" → movement, action=cross, direction=chasm, target=chasm

Be flexible with natural language variations. Understand synonyms and context.
Extract the core intent even if the phrasing is unusual."""


def _create_intent_parser_agent() -> Agent[None, IntentClassification]:
    """Create the PydanticAI agent for intent parsing."""
    return Agent(
        "openai:gpt-4o-mini",  # Fast and cheap for classification
        output_type=IntentClassification,
        system_prompt=SYSTEM_PROMPT,
    )


class IntentParser:
    """
    AI-powered command intent parser.
    
    Demonstrates the Classification Pattern:
    - Unstructured input (natural language)
    - AI processing (GPT-4 understands intent)
    - Structured output (ParsedCommand)
    """
    
    def __init__(self):
        """Initialize the intent parser with lazy agent creation."""
        self._agent: Optional[Agent[None, IntentClassification]] = None
    
    @property
    def agent(self) -> Agent[None, IntentClassification]:
        """Lazy-load the agent on first use."""
        if self._agent is None:
            self._agent = _create_intent_parser_agent()
        return self._agent
    
    async def parse_command(self, raw_command: str) -> ParsedCommand:
        """
        Parse a raw text command into structured intent using AI.
        
        Args:
            raw_command: Natural language command from player
            
        Returns:
            ParsedCommand with AI-classified intent
        """
        # Handle empty commands
        if not raw_command or not raw_command.strip():
            return ParsedCommand(
                command_type=CommandType.UNKNOWN,
                action="",
                confidence=0.0
            )
        
        # Use AI to classify intent
        result = await self.agent.run(raw_command)
        classification = result.output
        
        # Map string command_type to enum
        try:
            cmd_type = CommandType(classification.command_type.lower())
        except ValueError:
            cmd_type = CommandType.UNKNOWN
        
        # Build ParsedCommand from AI classification
        return ParsedCommand(
            command_type=cmd_type,
            action=classification.action,
            target=classification.target,
            direction=classification.direction,
            confidence=classification.confidence
        )
