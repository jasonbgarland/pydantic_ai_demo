# AI Agent Environment Configuration

## Overview

The AI agents in this project use PydanticAI framework with OpenAI models for game content generation. The agents are:

- **RoomDescriptor**: Generates rich, immersive room descriptions and handles navigation
- **InventoryManager**: Manages item interactions with realistic constraints
- **EntityManager**: Handles NPC dialogue, combat, and object interactions

## Environment Variables

The agents require these environment variables to be set in your `.env` file:

```bash
# Required - Your OpenAI API key
OPENAI_API_KEY=your-openai-api-key-here

# Optional - OpenAI model to use (default: gpt-4o-mini)
OPENAI_MODEL=gpt-4o-mini
```

## Setup Instructions

1. **Get an OpenAI API Key**:

   - Visit [OpenAI Platform](https://platform.openai.com/api-keys)
   - Create a new API key
   - Copy the key to your clipboard

2. **Configure Environment**:

   - Update the `.env` file in the project root
   - Replace `your-openai-api-key-here` with your actual API key
   - Optionally change the model (gpt-4o-mini, gpt-4o, gpt-3.5-turbo, etc.)

3. **Verify Setup**:
   ```bash
   cd backend
   python -c "from app.agents.room_descriptor import room_descriptor_agent; print('✅ Agents configured' if room_descriptor_agent else '❌ No API key')"
   ```

## Agent Behavior

- **With API Key**: Agents are created as PydanticAI instances with full AI capabilities
- **Without API Key**: Agents default to `None` for testing and development scenarios
- **Tool Registration**: Each agent has specific tools registered for their domain (room features, inventory checks, entity interactions)

## Fallback Mode

The agents gracefully handle missing dependencies:

- If PydanticAI is not installed, agents fallback to `None`
- If OpenAI API key is not set, agents fallback to `None`
- This allows the application to run in testing environments without external dependencies

## Model Configuration

You can change the OpenAI model by setting `OPENAI_MODEL` in your `.env` file:

- `gpt-4o-mini` (default) - Fast and cost-effective
- `gpt-4o` - More capable but slower/expensive
- `gpt-3.5-turbo` - Older but reliable option

## Testing

Unit tests work without API keys by mocking agent behavior. Set `RUN_INTEGRATION_TESTS=1` to test with real API calls.
