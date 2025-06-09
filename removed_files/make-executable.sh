#!/bin/bash
# Make all scripts executable and show hosting options summary

echo "🔧 Making scripts executable..."

chmod +x setup-hosting.sh
chmod +x deploy-docker.sh
chmod +x deploy-vps.sh
chmod +x deploy-railway.sh
chmod +x setup_claude_desktop.sh
chmod +x test_setup.sh
chmod +x run_tests.sh
chmod +x docker-demo.sh
chmod +x docker-quickref.sh
chmod +x cleanup_migration.sh
chmod +x complete_cleanup.sh
chmod +x setup_fastmcp_claude.sh

echo "✅ All scripts are now executable!"
echo ""
echo "🌐 Your hosting options:"
echo ""
echo "🚀 QUICK START:"
echo "   ./setup-hosting.sh          # Interactive hosting setup"
echo ""
echo "📍 LOCAL HOSTING:"
echo "   ./setup_claude_desktop.sh   # Integrate with Claude Desktop (legacy)"
echo "   ./setup_fastmcp_claude.sh    # Setup FastMCP integration (recommended)"
echo ""
echo "🐳 DOCKER HOSTING:"
echo "   ./deploy-docker.sh dev       # Development with test DB"
echo "   ./deploy-docker.sh prod      # Production deployment"
echo ""
echo "🖥️ VPS HOSTING:"
echo "   ./deploy-vps.sh <ip> <user>  # Deploy to your server"
echo ""
echo "☁️ CLOUD HOSTING:"
echo "   ./deploy-railway.sh          # Deploy to Railway"
echo ""
echo "🧪 TESTING:"
echo "   python test_fastmcp_setup.py   # Test FastMCP setup"
echo "   ./test_setup.sh              # Setup test environment"
echo "   ./run_tests.sh all           # Run all tests"
echo ""
echo "📚 Read HOSTING.md for detailed hosting guide"
echo "🎉 Your KeePass MCP Server is ready to deploy!"
