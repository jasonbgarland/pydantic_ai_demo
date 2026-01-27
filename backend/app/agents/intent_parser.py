"""Intent Parser Agent - AI-powered command classification.

This agent demonstrates the Classification Pattern:
- Takes unstructured natural language input
- Uses AI to understand player intent
- Returns structured ParsedCommand output

"""
from typing import Optional
from pydantic_ai import Agent
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
- movement: Player wants to move (go north, walk east, head south, cross chasm, dash across, run to, etc.)
- examine: Player wants to look at something (examine crystal, look at door, inspect wall)
- pickup: Player wants to take an item (take/get/grab/acquire/pick/obtain/retrieve + item name)
- drop: Player wants to drop an item (drop/put/place/leave/discard/release + item name)
- use: Player wants to use an item (use/secure/tie/anchor/apply/activate + item name)
- talk: Player wants to talk to someone (talk to guard, speak with wizard)
- attack: Player wants to attack something (attack goblin, hit door)
- look: Player wants to look around the current location (look, look around)
- inventory: Player wants to check inventory (inventory, check bag, what do I have)
- ability: Player wants to use a NAMED class ability (use illuminate, cast sneak, activate shield)
- unknown: Command doesn't fit any category or is unclear

Movement directions include: north, south, east, west, up, down

Special movement phrases:
- "cross chasm" / "cross bridge" → use context to determine direction (usually east from cave entrance)
- "dash across" → movement with the direction after "across"

IMPORTANT:
- "dash" in movement context (dash across, dash to) = movement, NOT ability
- "secure rope" or "tie rope" = use (using the rope item)
- "cross chasm" when at yawning_chasm means "go east" (to crystal treasury)
- For pickup/drop/use commands, reject compound actions:
  - "take rope and torch" → unknown (multiple items not allowed)
  - "drop sword, shield, and helmet" → unknown (multiple items not allowed)
  - "take rope" → pickup (single item is OK)

Examples:
- "go north" → movement, action=go, direction=north
- "go east" → movement, action=go, direction=east
- "dash across chasm" → movement, action=dash, direction=east
- "cross the chasm" → movement, action=cross, direction=east
- "grab the shiny crystal" → pickup, action=grab, target=crystal
- "secure rope" → use, action=secure, target=rope
- "use rope to cross" → use, action=use, target=rope
- "what's in my bag?" → inventory, action=inventory
- "examine the ancient door" → examine, action=examine, target=door
- "use illuminate" → ability, action=ability, target=illuminate
- "take rope and torch" → unknown (compound pickup not allowed)

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
