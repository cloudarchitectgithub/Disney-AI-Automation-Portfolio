#!/bin/bash

# Setup environment file for Project 1

echo "🔧 Setting up environment for Project 1"
echo "========================================"
echo ""

# Check if .env exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing .env file"
        exit 0
    fi
fi

# Create .env file
cat > .env << 'EOF'
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional: Override default model
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# N8N Configuration
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=disney2024

# Environment
ENVIRONMENT=development
EOF

echo "✅ Created .env file"
echo ""
echo "⚠️  IMPORTANT: You need to add your OpenRouter API key!"
echo ""
echo "1. Get your API key from: https://openrouter.ai/"
echo "2. Edit .env file:"
echo "   nano .env"
echo "   or"
echo "   open -e .env"
echo ""
echo "3. Replace 'your_openrouter_api_key_here' with your actual key"
echo ""
echo "Example:"
echo "OPENROUTER_API_KEY=sk-or-v1-abc123..."
echo ""

