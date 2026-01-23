#!/bin/bash
# Run unit tests only (fast, mocked)

echo "🧪 Running Unit Tests (Mocked)..."
echo "================================="

# Ensure services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "⚠️  Starting Docker services..."
    docker-compose up -d
    sleep 5
fi

# Run all unit tests with verbose output (discover pattern: test_*_unit.py)
docker-compose exec backend python -m unittest discover -v -s tests -p "test_*_unit.py"

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✅ All unit tests passed!"
else
    echo "❌ Some unit tests failed!"
    exit $exit_code
fi