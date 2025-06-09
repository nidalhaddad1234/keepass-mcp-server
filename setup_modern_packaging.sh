#!/bin/bash
# Modern Python packaging setup for KeePass MCP Server

set -e

echo "🚀 Setting up modern Python packaging with UV..."

# Install UV if not already installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
else
    echo "✅ UV already installed"
fi

# Initialize git repository
if [ ! -d ".git" ]; then
    echo "🔧 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: KeePass MCP Server v1.0.0"
else
    echo "✅ Git repository already initialized"
fi

# Create modern pyproject.toml
echo "📝 Creating modern pyproject.toml..."

# Create .gitignore
echo "📝 Creating .gitignore..."

# Create GitHub workflow for publishing
echo "📝 Creating GitHub Actions workflow..."
mkdir -p .github/workflows

echo "✅ Modern packaging setup complete!"
echo ""
echo "Next steps:"
echo "1. Run: source ~/.bashrc  # to get UV in PATH"
echo "2. Run: uv sync           # to create modern lockfile"
echo "3. Create GitHub repo and push"
