# Agentic AI RPG Demo

A multi-agent AI text adventure game built with PydanticAI, FastAPI, and Next.js to showcase modern AI frameworks and patterns.

## 🎮 Overview

This project demonstrates:

- **Multi-agent orchestration** with PydanticAI framework
- **Character class system** with RPG mechanics (Warrior, Wizard, Rogue)
- **Session management** with Redis for game state persistence
- **Vector embeddings** with ChromaDB for narrative context
- **Modern web stack** with FastAPI backend and Next.js frontend
- **Comprehensive testing** with both unit and integration tests

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Next.js UI   │◄──►│   FastAPI API    │◄──►│   PydanticAI    │
│  (Port 3000)   │    │  (Port 8001)     │    │    Agents       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
            ┌───────▼──┐  ┌─────▼────┐  ┌───▼─────┐
            │  Redis   │  │PostgreSQL│  │ChromaDB │
            │(Sessions)│  │(Persistence)│ │(Vector) │
            └──────────┘  └──────────┘  └─────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Setup

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd agentic_ai_rpg_demo
   ```

2. **Configure environment:**

   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

3. **Start the services:**

   ```bash
   docker-compose up -d
   ```

4. **Verify setup:**

   ```bash
   # Check all services are running
   docker-compose ps

   # Test API health
   curl http://localhost:8001/health
   ```

## 🧪 Testing

The project uses a comprehensive testing strategy with both **mocked unit tests** and **toggle-able integration tests**.

### Test Structure

```
backend/tests/
├── __init__.py
├── test_sessions_unit.py      # Fast mocked unit tests
└── test_sessions_integration.py  # Real HTTP integration tests
```

### Running Tests

#### Option 1: Using Development Workflow Script (Recommended)

```bash
# Show all available commands
./scripts/dev.sh

# Run specific commands
./scripts/dev.sh test        # Run all tests
./scripts/dev.sh test-unit   # Run unit tests only
./scripts/dev.sh test-int    # Run integration tests only
./scripts/dev.sh lint        # Check code quality
./scripts/dev.sh status      # Show service status
```

#### Option 2: Using Individual Helper Scripts

```bash
# Run unit tests only (fast, mocked)
./scripts/test-unit.sh

# Run integration tests (requires running services)
./scripts/test-integration.sh

# Run all tests
./scripts/test-all.sh

# Check code quality
./scripts/lint.sh
```

#### Option 3: Manual Commands

```bash
# Start services first
docker-compose up -d

# Unit tests only (external calls mocked)
docker-compose exec backend python -m unittest tests.test_sessions_unit -v

# Integration tests (real HTTP calls)
docker-compose exec -e RUN_INTEGRATION_TESTS=1 backend python -m unittest tests.test_sessions_integration -v

# All tests (unit + integration when flag set)
docker-compose exec backend python -m unittest discover -v
docker-compose exec -e RUN_INTEGRATION_TESTS=1 backend python -m unittest discover -v

# Code quality check
docker-compose exec backend pylint app/ tests/
```

### Test Philosophy

- **Unit Tests**: Fast, isolated, mock external dependencies (Redis, HTTP calls)
- **Integration Tests**: Slower, real HTTP calls, full workflow validation
- **CI/CD Friendly**: Integration tests disabled by default, enabled with `RUN_INTEGRATION_TESTS=1`

## 🎯 API Endpoints

### Health & Info

- `GET /` - API status and service connectivity
- `GET /health` - Simple health check

### Character System

- `GET /character/classes` - Available character classes with stats
- `POST /character/create` - Create a new character
- `GET /character/stats/{class}` - Get stat template for character class

### Game Sessions

- `POST /game/start` - Start new game session with character
- `POST /game/{id}/command` - Send command to game session
- `GET /game/{id}/state` - Get current game session state

## 🔧 Development

### Project Structure

```
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── main.py         # Main FastAPI app with endpoints
│   │   ├── agents/         # PydanticAI agents (coming soon)
│   │   └── __init__.py
│   ├── tests/              # Comprehensive test suite
│   └── requirements.txt
├── frontend/               # Next.js application
├── scripts/               # Development helper scripts
│   ├── dev.sh             # Main development workflow script
│   ├── setup.sh           # Initial project setup
│   ├── test-all.sh        # Run all tests (unit + integration)
│   ├── test-unit.sh       # Run unit tests only
│   ├── test-integration.sh # Run integration tests only
│   └── lint.sh            # Code quality checks
└── docker-compose.yml     # Multi-service Docker setup
```

### Adding New Features

1. **Write tests first** (TDD approach)
2. **Unit tests** for business logic (use mocks)
3. **Integration tests** for API workflows
4. **Run linting** before committing
5. **Update documentation** as needed

### Environment Variables

Key variables in `.env`:

- `OPENAI_API_KEY` - Required for PydanticAI agents
- `DATABASE_URL` - PostgreSQL connection for persistence
- `REDIS_URL` - Redis connection for session management
- `CHROMA_URL` - ChromaDB for vector embeddings

## 🐳 Docker Services

| Service  | Port | Purpose            |
| -------- | ---- | ------------------ |
| frontend | 3000 | Next.js UI         |
| backend  | 8001 | FastAPI API        |
| postgres | 5432 | Persistent storage |
| redis    | 6379 | Session management |
| chroma   | 8000 | Vector database    |

## 📚 Tech Stack

- **Backend**: FastAPI, PydanticAI, Redis, PostgreSQL
- **Frontend**: Next.js, React, TypeScript
- **AI/ML**: PydanticAI, ChromaDB, OpenAI
- **Testing**: unittest, httpx, mocking
- **Infrastructure**: Docker Compose, Python 3.11

## 📝 License

This project is for demonstration purposes.

---

**Happy adventuring!** 🗡️🧙‍♂️🏹
