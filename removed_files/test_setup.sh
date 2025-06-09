#!/bin/bash
# KeePass MCP Server Test Setup Script

set -e

echo "🔧 Setting up KeePass MCP Server test environment..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔋 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install the package in development mode
echo "⚙️ Installing package in development mode..."
pip install -e .

# Create test directories
echo "📁 Creating test directories..."
mkdir -p tests/data
mkdir -p tests/backups
mkdir -p tests/logs

# Create test KeePass database
echo "🔐 Creating test KeePass database..."
python3 -c "
import os
from pathlib import Path
try:
    from pykeepass import create_database
    
    # Create test database
    test_db_path = Path('tests/data/test_database.kdbx')
    test_db_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not test_db_path.exists():
        # Create database with test password
        kp = create_database(str(test_db_path), password='TestPassword123!')
        
        # Add some test entries
        # Development group
        dev_group = kp.add_group(kp.root_group, 'Development')
        kp.add_entry(dev_group, 'GitHub Account', 'developer', 'SecurePassword123!', 
                    url='https://github.com', notes='Test GitHub account')
        kp.add_entry(dev_group, 'GitLab CI', 'ci-user', 'GitLabPassword456!', 
                    url='https://gitlab.com', notes='CI/CD account')
        
        # Personal group
        personal_group = kp.add_group(kp.root_group, 'Personal')
        kp.add_entry(personal_group, 'Email Account', 'john.doe@email.com', 'EmailPass789!', 
                    url='https://mail.google.com', notes='Personal email')
        kp.add_entry(personal_group, 'Social Media', 'johndoe', 'WeakPass', 
                    url='https://twitter.com', notes='Twitter account')
        
        # Work group
        work_group = kp.add_group(kp.root_group, 'Work')
        kp.add_entry(work_group, 'Company Portal', 'john.doe', 'CompanyPass123!', 
                    url='https://company.com/portal', notes='Company intranet')
        
        kp.save()
        print(f'✅ Test database created: {test_db_path}')
    else:
        print(f'✅ Test database already exists: {test_db_path}')
        
except ImportError:
    print('⚠️ PyKeePass not available - install requirements first')
except Exception as e:
    print(f'❌ Error creating test database: {e}')
"

# Create test configuration
echo "⚙️ Creating test configuration..."
cat > tests/.env.test << EOF
# Test Configuration for KeePass MCP Server
KEEPASS_DB_PATH=tests/data/test_database.kdbx
KEEPASS_BACKUP_DIR=tests/backups
KEEPASS_ACCESS_MODE=readwrite
KEEPASS_AUTO_SAVE=true
KEEPASS_BACKUP_COUNT=5
KEEPASS_SESSION_TIMEOUT=3600
KEEPASS_AUTO_LOCK=1800
LOG_LEVEL=DEBUG
LOG_FILE=tests/logs/test.log
AUDIT_LOG=true
USE_KEYCHAIN=false
MASTER_PASSWORD_PROMPT=false
MAX_RETRIES=3
CACHE_TIMEOUT=300
MAX_CONCURRENT_OPERATIONS=5
EOF

# Create Claude Desktop test config
echo "🤖 Creating Claude Desktop test configuration..."
cat > tests/claude_test_config.json << EOF
{
  "mcpServers": {
    "keepass-test": {
      "command": "python",
      "args": ["-m", "keepass_mcp_server"],
      "env": {
        "KEEPASS_DB_PATH": "$(pwd)/tests/data/test_database.kdbx",
        "KEEPASS_ACCESS_MODE": "readwrite",
        "KEEPASS_AUTO_SAVE": "true",
        "LOG_LEVEL": "INFO",
        "USE_KEYCHAIN": "false"
      }
    }
  }
}
EOF

echo "✅ Test environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Run tests: ./run_tests.sh"
echo "2. Test manually: python -m keepass_mcp_server"
echo "3. Test database password: TestPassword123!"
echo "4. Test database location: tests/data/test_database.kdbx"
