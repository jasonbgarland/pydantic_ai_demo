#!/bin/bash
# Database migration helper script

set -e

cd "$(dirname "$0")/../backend"

# Use localhost for host machine, postgres for inside Docker
export DATABASE_URL="postgresql://adventure:development_password@localhost:5432/adventure_engine"

case "$1" in
  "migrate")
    echo "🔄 Generating new migration..."
    ../.venv/bin/alembic revision --autogenerate -m "${2:-Auto-generated migration}"
    ;;
  "upgrade")
    echo "⬆️  Applying migrations..."
    ../.venv/bin/alembic upgrade head
    ;;
  "downgrade")
    echo "⬇️  Rolling back one migration..."
    ../.venv/bin/alembic downgrade -1
    ;;
  "history")
    echo "📜 Migration history:"
    ../.venv/bin/alembic history
    ;;
  "current")
    echo "📍 Current migration:"
    ../.venv/bin/alembic current
    ;;
  "tables")
    echo "📊 Database tables:"
    docker exec agentic_ai_rpg_demo-postgres-1 psql -U adventure -d adventure_engine -c "\dt"
    ;;
  *)
    echo "Usage: $0 {migrate|upgrade|downgrade|history|current|tables}"
    echo ""
    echo "Commands:"
    echo "  migrate [message]  - Generate new migration"
    echo "  upgrade            - Apply pending migrations"
    echo "  downgrade          - Roll back one migration"
    echo "  history            - Show migration history"
    echo "  current            - Show current migration"
    echo "  tables             - List database tables"
    exit 1
    ;;
esac
