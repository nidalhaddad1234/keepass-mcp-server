#!/bin/bash
# Complete setup script for publishing KeePass MCP Server to GitHub
set -e

echo "🚀 KeePass MCP Server - GitHub Publishing Setup"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: Run this script from the keepass-mcp-server directory${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Step 1: Installing UV (modern Python package manager)${NC}"
if ! command -v uv &> /dev/null; then
    echo "Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo -e "${GREEN}✅ UV installed successfully${NC}"
else
    echo -e "${GREEN}✅ UV already installed${NC}"
fi

echo -e "${BLUE}🔧 Step 2: Setting up modern Python environment${NC}"
uv sync --all-extras
echo -e "${GREEN}✅ Dependencies installed with UV${NC}"

echo -e "${BLUE}📝 Step 3: Initializing Git repository${NC}"
if [ ! -d ".git" ]; then
    git init
    git add .
    git commit -m "Initial commit: KeePass MCP Server v1.0.0

Features:
- Complete KeePass 2.x integration
- Model Context Protocol (MCP) server
- 15+ credential management tools
- FastMCP implementation
- Security features and audit logging
- Modern Python packaging with UV
- GitHub Actions CI/CD pipeline"
    echo -e "${GREEN}✅ Git repository initialized${NC}"
else
    echo -e "${GREEN}✅ Git repository already exists${NC}"
fi

echo -e "${BLUE}🔍 Step 4: Running quality checks${NC}"
echo "Running linting..."
uv run black src/ || echo "⚠️  Black formatting needs fixes"
uv run isort src/ || echo "⚠️  Import sorting needs fixes"
uv run flake8 src/ --count --max-line-length=88 || echo "⚠️  Flake8 found issues"

echo -e "${BLUE}📋 Step 5: Building package${NC}"
uv build
echo -e "${GREEN}✅ Package built successfully${NC}"

echo -e "${BLUE}✅ Step 6: Checking package${NC}"
uv add --dev twine
uv run twine check dist/*
echo -e "${GREEN}✅ Package passes all checks${NC}"

echo ""
echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo ""
echo "1. Create GitHub repository:"
echo "   ${BLUE}gh repo create keepass-mcp-server --public --description 'Model Context Protocol server for secure KeePass credential management'${NC}"
echo ""
echo "2. Set up GitHub token for MCP:"
echo "   - Go to GitHub Settings > Developer settings > Personal access tokens"
echo "   - Create a new token with repo permissions"
echo "   - Replace 'YOUR_GITHUB_TOKEN_HERE' in Claude config"
echo ""
echo "3. Push to GitHub:"
echo "   ${BLUE}git remote add origin https://github.com/YOUR_USERNAME/keepass-mcp-server.git${NC}"
echo "   ${BLUE}git branch -M main${NC}"
echo "   ${BLUE}git push -u origin main${NC}"
echo ""
echo "4. Set up PyPI publishing (optional):"
echo "   - Create account on https://pypi.org"
echo "   - Generate API token"
echo "   - Add as GitHub secret: PYPI_API_TOKEN"
echo ""
echo "5. Restart Claude Desktop to load GitHub MCP"
echo ""
echo -e "${GREEN}🔗 Repository will be available at:${NC}"
echo "   https://github.com/YOUR_USERNAME/keepass-mcp-server"
echo ""
echo -e "${GREEN}📦 Package will be installable via:${NC}"
echo "   ${BLUE}pip install keepass-mcp-server${NC}"
echo "   ${BLUE}uv add keepass-mcp-server${NC}"
