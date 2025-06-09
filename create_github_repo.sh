#!/bin/bash
# Complete GitHub repository creation and publishing script

set -e

echo "🚀 KeePass MCP Server - GitHub Repository Creation"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ Error: Run this script from the keepass-mcp-server directory${NC}"
    exit 1
fi

# Check if gh CLI is available and authenticated
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) is not installed${NC}"
    echo "Please install it first, then run ./setup_github_mcp.sh"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ Not authenticated with GitHub CLI${NC}"
    echo "Please run: gh auth login"
    exit 1
fi

echo -e "${GREEN}✅ GitHub CLI is ready${NC}"

# Get current user info
GITHUB_USER=$(gh api user --jq '.login')
echo -e "${BLUE}📋 GitHub User: $GITHUB_USER${NC}"

# Repository details
REPO_NAME="keepass-mcp-server"
REPO_DESCRIPTION="🔐 Model Context Protocol server for secure KeePass credential management with Claude Desktop"

echo -e "${BLUE}📦 Step 1: Preparing repository...${NC}"

# Initialize git if not already done
if [ ! -d ".git" ]; then
    git init
    echo -e "${GREEN}✅ Git repository initialized${NC}"
fi

# Add and commit all files
git add .
if ! git diff --cached --quiet; then
    git commit -m "🚀 Initial release: KeePass MCP Server v1.0.0

Features:
✅ Complete KeePass 2.x (.kdbx) integration  
✅ Model Context Protocol (MCP) server
✅ 15+ credential management tools
✅ FastMCP implementation for reliable tool registration
✅ Advanced search and filtering capabilities
✅ Secure password generation
✅ Automatic database backup system
✅ Session-based authentication with timeouts
✅ Comprehensive audit logging
✅ Modern Python packaging with UV support
✅ GitHub Actions CI/CD pipeline
✅ Docker support

Security:
🔒 AES-256 database encryption
🔐 Master password + optional key file authentication
🛡️ Session management with auto-timeouts
🔍 Security analysis and weak password detection
📊 Audit logging (operations only, never credentials)

Compatibility:
🐍 Python 3.8+ support
🖥️ Cross-platform (Windows, macOS, Linux)
🤖 Claude Desktop integration
📦 Modern packaging standards"
    echo -e "${GREEN}✅ Changes committed${NC}"
else
    echo -e "${GREEN}✅ Repository is up to date${NC}"
fi

echo -e "${BLUE}📦 Step 2: Creating GitHub repository...${NC}"

# Create GitHub repository
if gh repo create "$REPO_NAME" --public --description "$REPO_DESCRIPTION" --source=. --remote=origin --push; then
    echo -e "${GREEN}✅ GitHub repository created successfully${NC}"
    
    # Set up repository topics/tags
    echo -e "${BLUE}🏷️ Adding repository topics...${NC}"
    gh repo edit --add-topic "keepass,password-manager,mcp,model-context-protocol,claude,ai,security,authentication,python,automation"
    
    # Create and push main branch
    git branch -M main
    git push -u origin main
    
    echo -e "${GREEN}✅ Repository published successfully${NC}"
    
    # Repository information
    REPO_URL="https://github.com/$GITHUB_USER/$REPO_NAME"
    echo ""
    echo -e "${GREEN}🎉 Repository Created Successfully!${NC}"
    echo -e "${BLUE}📍 Repository URL: $REPO_URL${NC}"
    echo ""
    
    # Set up GitHub repository settings
    echo -e "${BLUE}⚙️ Configuring repository settings...${NC}"
    
    # Enable issues, discussions, and wiki
    gh repo edit --enable-issues --enable-discussions --enable-wiki
    
    # Set up branch protection (optional)
    echo -e "${YELLOW}🛡️ Would you like to set up branch protection for 'main'? (y/n)${NC}"
    read -r setup_protection
    if [ "$setup_protection" = "y" ] || [ "$setup_protection" = "Y" ]; then
        gh api repos/$GITHUB_USER/$REPO_NAME/branches/main/protection \
            --method PUT \
            --field required_status_checks='{"strict":true,"contexts":["test"]}' \
            --field enforce_admins=true \
            --field required_pull_request_reviews='{"required_approving_review_count":1}' \
            --field restrictions=null || echo "Branch protection setup failed (may require admin permissions)"
    fi
    
    echo ""
    echo -e "${YELLOW}📋 Next Steps:${NC}"
    echo "1. 🔗 Visit your repository: $REPO_URL"
    echo "2. 📝 Customize the repository description and README if needed"
    echo "3. 🏷️ Create your first release to trigger PyPI publishing:"
    echo "   ${BLUE}gh release create v1.0.0 --title 'v1.0.0 - Initial Release' --notes-file CHANGELOG.md${NC}"
    echo "4. 🔧 Set up PyPI publishing secrets (if you want automated publishing):"
    echo "   • Go to repository Settings > Secrets and variables > Actions"
    echo "   • Add: PYPI_API_TOKEN (from https://pypi.org/manage/account/token/)"
    echo "   • Add: TEST_PYPI_API_TOKEN (from https://test.pypi.org/manage/account/token/)"
    echo ""
    echo -e "${GREEN}📦 Your package will be installable via:${NC}"
    echo "   ${BLUE}pip install keepass-mcp-server${NC}"
    echo "   ${BLUE}uv add keepass-mcp-server${NC}"
    echo ""
    echo -e "${GREEN}🔗 Installation from GitHub:${NC}"
    echo "   ${BLUE}pip install git+$REPO_URL.git${NC}"
    echo "   ${BLUE}uv add git+$REPO_URL.git${NC}"
    
else
    echo -e "${RED}❌ Failed to create GitHub repository${NC}"
    echo "The repository might already exist or there could be a permissions issue."
    echo "You can create it manually at: https://github.com/new"
    exit 1
fi
