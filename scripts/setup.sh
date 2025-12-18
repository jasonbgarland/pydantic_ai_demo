#!/bin/bash
# Setup development environment

echo "🛠️  Setting up Agentic AI RPG Demo..."
echo "====================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OpenAI API key!"
fi

# Build and start services
echo "🐳 Building and starting Docker services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Check service health
echo "🏥 Checking service health..."
services=("backend:8000" "frontend:3000" "postgres:5432" "redis:6379" "chroma:8000")
all_healthy=true

for service in "${services[@]}"; do
    name=${service%:*}
    port=${service#*:}
    
    if [ "$name" = "backend" ]; then
        if docker-compose exec backend python -c "import requests; requests.get('http://backend:8000/health', timeout=1)" > /dev/null 2>&1; then
            echo "✅ $name is healthy"
        else
            echo "❌ $name is not responding"
            all_healthy=false
        fi
    else
        if docker-compose ps | grep -q "$name.*Up"; then
            echo "✅ $name is running"
        else
            echo "❌ $name is not running"
            all_healthy=false
        fi
    fi
done

echo ""
if $all_healthy; then
    echo "🎉 Setup complete! Services are running at:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8001"
    echo "   API Docs: http://localhost:8001/docs"
    echo ""
    echo "📚 Next steps:"
    echo "   - Run tests: ./scripts/test-all.sh"
    echo "   - Check code quality: ./scripts/lint.sh"
    echo "   - View logs: docker-compose logs -f"
else
    echo "⚠️  Some services failed to start. Check logs with:"
    echo "   docker-compose logs"
fi