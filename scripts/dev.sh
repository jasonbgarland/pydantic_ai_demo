#!/bin/bash
# Development workflow script

echo "🚀 Agentic AI RPG Demo - Development Workflow"
echo "=============================================="
echo ""

# Show available commands
echo "Available commands:"
echo ""
echo "  🛠️  setup     - Initial project setup"
echo "  🧪 test      - Run all tests (unit + integration)"
echo "  ⚡ test-unit - Run unit tests only (fast)"
echo "  🌐 test-int  - Run integration tests only"  
echo "  🔍 lint      - Run code quality checks"
echo "  📋 status    - Show service status"
echo "  🗒️  logs      - Show service logs"
echo "  🔄 restart   - Restart all services"
echo "  🛑 stop      - Stop all services"
echo "  🧹 clean     - Stop and remove containers/volumes"
echo ""

if [ $# -eq 0 ]; then
    echo "Usage: $0 <command>"
    echo ""
    echo "Example: $0 test"
    exit 1
fi

command=$1

case $command in
    setup)
        echo "🛠️  Setting up development environment..."
        ./scripts/setup.sh
        ;;
    test)
        echo "🧪 Running all tests..."
        ./scripts/test-all.sh
        ;;
    test-unit)
        echo "⚡ Running unit tests..."
        ./scripts/test-unit.sh
        ;;
    test-int)
        echo "🌐 Running integration tests..."
        ./scripts/test-integration.sh
        ;;
    lint)
        echo "🔍 Running code quality checks..."
        ./scripts/lint.sh
        ;;
    status)
        echo "📋 Service status:"
        docker-compose ps
        ;;
    logs)
        echo "🗒️  Service logs (press Ctrl+C to exit):"
        docker-compose logs -f
        ;;
    restart)
        echo "🔄 Restarting services..."
        docker-compose restart
        echo "✅ Services restarted!"
        ;;
    stop)
        echo "🛑 Stopping services..."
        docker-compose stop
        echo "✅ Services stopped!"
        ;;
    clean)
        echo "🧹 Cleaning up containers and volumes..."
        read -p "⚠️  This will remove all data. Continue? (y/N): " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            docker-compose down -v --remove-orphans
            echo "✅ Cleanup complete!"
        else
            echo "❌ Cleanup cancelled."
        fi
        ;;
    *)
        echo "❌ Unknown command: $command"
        echo ""
        echo "Available commands: setup, test, test-unit, test-int, lint, status, logs, restart, stop, clean"
        exit 1
        ;;
esac