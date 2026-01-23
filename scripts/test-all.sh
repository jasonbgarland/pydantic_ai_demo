#!/bin/bash
# Run all tests (unit + integration)

echo "🚀 Running All Tests..."
echo "======================"

# Ensure services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "⚠️  Starting Docker services..."
    docker-compose up -d
    sleep 10
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

echo ""
echo "📋 Test Summary:"
echo "================"

# Run unit tests first (skip integration tests)
echo "1️⃣  Unit Tests (All unit test files):"
docker-compose exec backend python -m unittest discover -v -s tests -p "test_*_unit.py"
unit_exit_code=$?

echo ""
echo "2️⃣  Integration Tests (All integration test files):"
docker-compose exec -e RUN_INTEGRATION_TESTS=1 -e API_BASE_URL=http://backend:8000 backend python -m unittest discover -v -s tests -p "test_*_integration.py"
integration_exit_code=$?

echo ""
echo "📊 Results:"
echo "==========="

if [ $unit_exit_code -eq 0 ]; then
    echo "✅ Unit Tests: PASSED"
else
    echo "❌ Unit Tests: FAILED"
fi

if [ $integration_exit_code -eq 0 ]; then
    echo "✅ Integration Tests: PASSED"
else
    echo "❌ Integration Tests: FAILED"
fi

# Overall result
if [ $unit_exit_code -eq 0 ] && [ $integration_exit_code -eq 0 ]; then
    echo ""
    echo "🎉 All tests passed successfully!"
    exit 0
else
    echo ""
    echo "💥 Some tests failed!"
    exit 1
fi