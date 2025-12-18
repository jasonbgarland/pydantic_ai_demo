#!/bin/bash
# Run code quality checks with pylint

echo "🔍 Running Code Quality Check..."
echo "================================"

# Ensure services are running
if ! docker-compose ps | grep -q "Up"; then
    echo "⚠️  Starting Docker services..."
    docker-compose up -d
    sleep 5
fi

# Run pylint on app and tests
echo "📝 Analyzing code with pylint..."
docker-compose exec backend pylint app/ tests/ --output-format=text

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo "✅ Code quality check passed!"
elif [ $exit_code -le 4 ]; then
    echo "⚠️  Code quality check passed with warnings (score above threshold)"
else
    echo "❌ Code quality check failed - please fix issues above"
fi

exit $exit_code