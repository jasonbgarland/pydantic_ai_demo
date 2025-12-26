#!/bin/bash
# Test script for WebSocket functionality

set -e

echo "🧪 Running WebSocket Tests..."
echo ""

# Backend WebSocket integration tests
echo "📡 Backend WebSocket Integration Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd backend
RUN_INTEGRATION_TESTS=1 python -m unittest tests.test_websocket_integration -v
echo ""

# Frontend WebSocket hook tests
echo "🔌 Frontend WebSocket Hook Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd ../frontend
npm test -- useGameWebSocket.test.ts
echo ""

echo "✅ All WebSocket tests completed!"
