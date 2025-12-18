#!/bin/bash
# Run integration tests (real HTTP calls)

echo "🌐 Running Integration Tests (Real HTTP)..."
echo "==========================================="

# Ensure services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "⚠️  Starting Docker services..."
    docker-compose up -d
    sleep 10  # Give services more time for integration tests
fi

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if docker-compose exec backend python -c "import requests; requests.get('http://backend:8000/health', timeout=1)" > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start within 30 seconds"
        exit 1
    fi
    sleep 1
done

# Run integration tests with environment flag
docker-compose exec -e RUN_INTEGRATION_TESTS=1 backend python -m unittest tests.test_sessions_integration -v

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✅ All integration tests passed!"
else
    echo "❌ Some integration tests failed!"
    exit $exit_code
fi