#!/bin/bash

# Setup script for the Multi-Agent Document Analysis System

set -e

echo "=========================================="
echo "Multi-Agent System Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip -q

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize Knowledge Base
echo ""
echo "Initializing Knowledge Base (Chunking & Embedding)..."
python3 scripts/setup_knowledge_base.py

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Run validation tests"
echo "🧪 Running validation tests..."
export PYTHONPATH=$PWD
python -m pytest tests/

echo "✅ System Ready!
To start:
1. Start MCP Server: uvicorn mcp_server.main:app --port 8000
2. Run Orchestrator: python orchestration/main.py 'Your query'"
echo ""
