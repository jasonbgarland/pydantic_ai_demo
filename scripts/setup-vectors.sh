#!/bin/bash
set -e

echo "🌍 Adventure Engine Vector Database Setup"
echo "=========================================="

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ] && ! grep -q "OPENAI_API_KEY=" .env 2>/dev/null; then
    echo "❌ OpenAI API key not found!"
    echo "   Please set OPENAI_API_KEY in your .env file"
    echo "   Example: OPENAI_API_KEY=sk-..."
    exit 1
fi

echo "✅ OpenAI API key configured"

# Create chroma_data directory if it doesn't exist
if [ ! -d "chroma_data" ]; then
    echo "📁 Creating chroma_data directory..."
    mkdir -p chroma_data
fi

# Check if vector database already exists
if [ -f "chroma_data/chroma.sqlite3" ]; then
    echo "🔍 Existing vector database found"
    read -p "   Regenerate embeddings? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing existing database..."
        rm -rf chroma_data/*
    else
        echo "✅ Using existing embeddings"
        exit 0
    fi
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "🐍 Activating Python virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️  Virtual environment not found. Using system Python."
fi

# Install requirements
echo "📦 Installing Python dependencies..."
pip install -r backend/requirements.txt

# Run the seeding script
echo "🌱 Generating embeddings and seeding vector database..."
echo "   This will make API calls to OpenAI and may take a few minutes..."

python backend/seed_world_data.py

if [ $? -eq 0 ]; then
    echo "🎉 Vector database setup complete!"
    echo "   • 41 content chunks embedded and stored"
    echo "   • Ready for Docker Compose with: docker-compose up"
    echo "   • Vector data will persist in ./chroma_data/"
else
    echo "❌ Setup failed. Please check the error messages above."
    exit 1
fi