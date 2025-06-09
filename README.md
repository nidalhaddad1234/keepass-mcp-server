# KeePass MCP Server

A comprehensive Model Context Protocol (MCP) server that provides secure credential management through KeePass database integration. This server enables AI agents and browser automation tools to securely access, manage, and manipulate password databases while maintaining the highest security standards.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![KeePass 2.x](https://img.shields.io/badge/KeePass-2.x-green.svg)](https://keepass.info/)

## Features

### 🔐 **Complete KeePass Integration**
- Full read/write access to KeePass 2.x (.kdbx) database files
- Support for master password and key file authentication
- Automatic database saving with backup creation
- Transaction support with rollback capability

### 🔍 **Advanced Search & Retrieval**
- Search credentials by website URL, title, tags, or any metadata
- Fuzzy URL matching for automatic credential selection
- Advanced filtering by date, group, content, and custom criteria
- Similarity search and duplicate detection

### 📝 **Comprehensive Entry Management**
- Full CRUD operations for entries and groups
- Password generation with customizable rules
- Entry validation and security analysis
- Bulk import/export operations

### 🛡️ **Enterprise-Grade Security**
- Session-based authentication with configurable timeouts
- System keychain integration for secure credential storage
- Automatic database locking and memory cleanup
- Comprehensive audit logging
- Rate limiting and concurrent access protection

### 🔧 **Browser Automation Ready**
- Credentials formatted for automation tools
- Auto-type sequence generation
- URL matching for automatic credential selection
- Support for custom fields and TOTP codes

### 🐳 **Flexible Deployment**
- Local MCP server for Claude Desktop
- Docker containerization with docker-compose
- Environment-based configuration
- Health check endpoints

## Quick Start

### 🚀 **One-Click Setup**

```bash
# Clone the repository
git clone https://github.com/keepass-mcp/keepass-mcp-server.git
cd keepass-mcp-server

# Make scripts executable
chmod +x make-executable.sh && ./make-executable.sh

# Choose your hosting option
./setup-hosting.sh
```

### 📍 **Hosting Options**

| Option | Best For | Setup Time | Cost | Security |
|--------|----------|------------|------|---------|
| 🏠 **Local Machine** | Beginners | 5 min | Free | Highest |
| 🐳 **Docker Local** | Developers | 10 min | Free | High |
| 🖥️ **VPS/Server** | Teams | 15 min | $5-20/mo | High |
| ☁️ **Cloud Platform** | Remote Access | 10 min | $0-10/mo | Medium |
| 🔒 **Advanced Security** | Enterprise | 60 min | Varies | Maximum |

### **Quick Hosting Commands**

```bash
# Interactive setup (recommended)
./setup-hosting.sh

# Local Claude Desktop integration
./setup_claude_desktop.sh

# Docker deployment
./deploy-docker.sh production

# VPS deployment
./deploy-vps.sh <server-ip> <username>

# Cloud deployment (Railway)
./deploy-railway.sh
```

### Prerequisites

- Python 3.8 or higher
- KeePass 2.x database file (.kdbx)
- Claude Desktop (for local MCP integration)

## Manual Installation (if not using setup scripts)

1. **Install dependencies:**
```bash
pip install -r requirements.txt
pip install -e .
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your database path and preferences
```

3. **Configure Claude Desktop:**
Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "keepass": {
      "command": "python",
      "args": ["-m", "keepass_mcp_server"],
      "env": {
        "KEEPASS_DB_PATH": "/path/to/your/database.kdbx",
        "KEEPASS_ACCESS_MODE": "readwrite",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

4. **Start using with Claude:**
```
Tell Claude: "Please unlock my KeePass database and help me manage my credentials."
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `KEEPASS_DB_PATH` | Path to KeePass database file | - | ✅ |
| `KEEPASS_KEY_FILE` | Path to key file (optional) | - | ❌ |
| `KEEPASS_BACKUP_DIR` | Backup directory path | `./backups` | ❌ |
| `KEEPASS_ACCESS_MODE` | Access mode (`readonly`/`readwrite`) | `readonly` | ❌ |
| `KEEPASS_AUTO_SAVE` | Enable automatic saving | `true` | ❌ |
| `KEEPASS_BACKUP_COUNT` | Number of backups to keep | `10` | ❌ |
| `KEEPASS_SESSION_TIMEOUT` | Session timeout in seconds | `3600` | ❌ |
| `KEEPASS_AUTO_LOCK` | Auto-lock timeout in seconds | `1800` | ❌ |
| `LOG_LEVEL` | Logging level | `INFO` | ❌ |

### Complete Configuration Example

```bash
# Database Configuration
KEEPASS_DB_PATH=/secure/path/to/database.kdbx
KEEPASS_KEY_FILE=/secure/path/to/keyfile.key
KEEPASS_BACKUP_DIR=/secure/backups

# Access Control
KEEPASS_ACCESS_MODE=readwrite
KEEPASS_AUTO_SAVE=true
KEEPASS_BACKUP_COUNT=15
KEEPASS_SESSION_TIMEOUT=7200
KEEPASS_AUTO_LOCK=3600

# Security Settings
USE_KEYCHAIN=true
MASTER_PASSWORD_PROMPT=true
MAX_RETRIES=3

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/keepass-mcp.log
AUDIT_LOG=true

# Performance
CACHE_TIMEOUT=300
MAX_CONCURRENT_OPERATIONS=10
```

## Usage Examples

### Basic Authentication
```
User: "Please unlock my KeePass database"
Claude: "I'll unlock your KeePass database. Please provide your master password."
User: "MySecurePassword123!"
Claude: "Database unlocked successfully. I can now help you manage your credentials."
```

### Searching Credentials
```
User: "Find my GitHub credentials"
Claude: "I found your GitHub account credentials. The username is 'developer' and I can provide the password when needed."

User: "I need credentials for github.com"
Claude: "I found a matching entry for github.com with username 'developer'. Would you like me to provide the password?"
```

### Creating New Entries
```
User: "Create a new entry for Netflix with username john@email.com and generate a strong password"
Claude: "I've created a new Netflix entry with username 'john@email.com' and generated a secure 16-character password. The entry has been saved to your database."
```

### Managing Groups
```
User: "Create a new group called 'Streaming Services' and move all my entertainment accounts there"
Claude: "I've created the 'Streaming Services' group and moved 4 entertainment accounts (Netflix, Hulu, Disney+, and Spotify) to this group."
```

### Security Analysis
```
User: "Check my database for weak passwords"
Claude: "I found 3 entries with weak passwords:
1. Old Email Account - password too short
2. Test Account - low complexity
3. Social Media - common password pattern

Would you like me to generate new secure passwords for these accounts?"
```

## Docker Deployment

### Using Docker Compose

1. **Create docker-compose.yml:**
```yaml
version: '3.8'
services:
  keepass-mcp-server:
    build: .
    volumes:
      - /path/to/your/database.kdbx:/data/database.kdbx:ro
      - keepass_backups:/data/backups
    environment:
      KEEPASS_DB_PATH: /data/database.kdbx
      KEEPASS_ACCESS_MODE: readwrite
      LOG_LEVEL: INFO
```

2. **Deploy:**
```bash
docker-compose up -d
```

### Manual Docker Run
```bash
docker build -t keepass-mcp-server .
docker run -d \
  -v /path/to/database.kdbx:/data/database.kdbx:ro \
  -v /path/to/backups:/data/backups \
  -e KEEPASS_DB_PATH=/data/database.kdbx \
  -e KEEPASS_ACCESS_MODE=readwrite \
  keepass-mcp-server
```

## API Reference

### Authentication Tools

#### `authenticate`
Unlock the KeePass database and create session.
```json
{
  "password": "master_password",
  "key_file": "/path/to/keyfile.key"  // optional
}
```

#### `logout`
Lock database and destroy session.
```json
{}
```

### Search & Retrieval Tools

#### `search_credentials`
Search for credentials using various criteria.
```json
{
  "query": "github",
  "search_fields": ["title", "username", "url", "notes", "tags"],
  "case_sensitive": false,
  "exact_match": false,
  "tags": ["important"],
  "group_filter": "Development",
  "limit": 50,
  "sort_by": "relevance"
}
```

#### `search_by_url`
Search for credentials by URL with fuzzy matching.
```json
{
  "url": "https://github.com",
  "fuzzy_match": true
}
```

#### `get_credential`
Retrieve specific credential by entry ID.
```json
{
  "entry_id": "uuid-string",
  "include_password": true,
  "include_history": false
}
```

### Entry Management Tools

#### `create_entry`
Create a new password entry.
```json
{
  "title": "GitHub Account",
  "username": "developer",
  "password": "optional-password",
  "url": "https://github.com",
  "notes": "Development account",
  "group_name": "Development",
  "tags": ["development", "git"],
  "custom_fields": {"API_Token": "ghp_xxxxx"},
  "generate_password": true,
  "password_options": {
    "length": 16,
    "include_symbols": true,
    "exclude_ambiguous": true
  }
}
```

#### `update_entry`
Update an existing entry.
```json
{
  "entry_id": "uuid-string",
  "title": "Updated Title",
  "username": "new_username",
  "generate_password": true,
  "password_options": {"length": 20}
}
```

#### `delete_entry`
Delete an entry from the database.
```json
{
  "entry_id": "uuid-string",
  "permanent": false  // true for permanent deletion
}
```

### Group Management Tools

#### `create_group`
Create a new group.
```json
{
  "name": "Development",
  "parent_group_name": "Work",
  "notes": "Development tools and accounts",
  "icon": 1
}
```

#### `list_groups`
List groups in the database.
```json
{
  "include_root": true,
  "include_statistics": false,
  "recursive": false,
  "sort_by": "name"
}
```

### Advanced Tools

#### `generate_password`
Generate a secure password.
```json
{
  "length": 16,
  "include_uppercase": true,
  "include_lowercase": true,
  "include_numbers": true,
  "include_symbols": true,
  "exclude_ambiguous": true
}
```

#### `search_weak_passwords`
Find entries with weak passwords.
```json
{
  "min_length": 8,
  "require_complexity": true
}
```

#### `validate_entries`
Validate all entries and find issues.
```json
{}
```

### Database Operations

#### `save_database`
Manually save the database.
```json
{
  "reason": "manual"
}
```

#### `create_backup`
Create a database backup.
```json
{
  "reason": "manual",
  "compress": true,
  "verify": true
}
```

#### `get_database_info`
Get database information and statistics.
```json
{}
```

#### `health_check`
Perform system health check.
```json
{}
```

## Security Features

### 🔐 **Authentication & Sessions**
- Master password and key file support
- Session-based authentication with configurable timeouts
- Automatic session cleanup and expiration
- Rate limiting for authentication attempts

### 🛡️ **Data Protection**
- No plaintext credential storage in memory
- System keychain integration (macOS/Windows/Linux)
- Automatic memory cleanup of sensitive data
- Secure backup creation with verification

### 📊 **Audit & Monitoring**
- Comprehensive audit logging (operations only, never credentials)
- Security event tracking
- Session activity monitoring
- Database access logging

### 🔒 **Access Control**
- Read-only and read-write access modes
- Permission-based operation filtering
- Concurrent access protection
- Database locking after inactivity

### 🏥 **Recovery & Backup**
- Automatic backups before write operations
- Transaction support with rollback capability
- Backup verification and restoration
- Database corruption detection

## Browser Automation Integration

The server provides credentials in formats optimized for browser automation:

### Selenium Example
```python
from selenium import webdriver
from selenium.webdriver.common.by import By

# Get credentials through Claude/MCP
credentials = get_credentials_from_claude("github.com")

driver = webdriver.Chrome()
driver.get("https://github.com/login")
driver.find_element(By.NAME, "login").send_keys(credentials["username"])
driver.find_element(By.NAME, "password").send_keys(credentials["password"])
driver.find_element(By.NAME, "commit").click()
```

### Playwright Example
```python
from playwright.sync_api import sync_playwright

credentials = get_credentials_from_claude("github.com")

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://github.com/login")
    page.fill('input[name="login"]', credentials["username"])
    page.fill('input[name="password"]', credentials["password"])
    page.click('input[name="commit"]')
```

## Development

### Setup Development Environment

1. **Clone and install in development mode:**
```bash
git clone https://github.com/keepass-mcp/keepass-mcp-server.git
cd keepass-mcp-server
pip install -r requirements-dev.txt
pip install -e .
```

2. **Run tests:**
```bash
pytest tests/ -v --cov=keepass_mcp_server
```

3. **Run linting:**
```bash
black src/
isort src/
flake8 src/
mypy src/
```

### Project Structure

```
keepass-mcp-server/
├── src/keepass_mcp_server/     # Main package
│   ├── server.py               # MCP server implementation
│   ├── keepass_handler.py      # KeePass database interface
│   ├── entry_manager.py        # Entry CRUD operations
│   ├── group_manager.py        # Group CRUD operations
│   ├── search_engine.py        # Advanced search functionality
│   ├── password_generator.py   # Password generation
│   ├── backup_manager.py       # Backup and restore
│   ├── security.py             # Security and authentication
│   ├── validators.py           # Input validation
│   ├── exceptions.py           # Custom exceptions
│   └── config.py               # Configuration management
├── tests/                      # Test suite
├── docker/                     # Docker deployment files
├── examples/                   # Usage examples and samples
├── docs/                       # Documentation
└── README.md                   # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Ensure all tests pass (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Troubleshooting

### Common Issues

**Database not found:**
```
Error: Database file not found: /path/to/database.kdbx
```
- Verify the `KEEPASS_DB_PATH` environment variable
- Ensure the file exists and is readable
- Check file permissions

**Authentication failed:**
```
Error: Invalid password or key file
```
- Verify master password is correct
- Check key file path if using one
- Ensure key file is readable

**Permission denied:**
```
Error: Operation not allowed in read-only mode
```
- Change `KEEPASS_ACCESS_MODE` to `readwrite`
- Restart the server after configuration change

**Session expired:**
```
Error: Session has expired. Please authenticate again.
```
- Re-authenticate with Claude
- Increase `KEEPASS_SESSION_TIMEOUT` if needed

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
keepass-mcp-server
```

### Health Check

Check server status:
```bash
# Using the health_check tool through Claude
"Please run a health check on the KeePass server"
```

## Security Considerations

### 🔒 **Database Security**
- Store your KeePass database in a secure location
- Use strong master passwords (recommended: 20+ characters)
- Consider using key files for additional security
- Regular backups to secure, separate locations

### 🛡️ **Server Security**
- Run the server with minimal required privileges
- Use read-only mode when write access isn't needed
- Configure appropriate session timeouts
- Monitor audit logs for suspicious activity

### 🔐 **Network Security**
- Use local deployment when possible
- Secure network connections for remote deployments
- Consider VPN for remote access
- Regular security updates

### 📊 **Monitoring**
- Enable audit logging
- Monitor for failed authentication attempts
- Set up alerts for security events
- Regular security assessments

## Performance Optimization

### 🚀 **Configuration Tuning**
- Adjust `CACHE_TIMEOUT` for your usage patterns
- Configure `MAX_CONCURRENT_OPERATIONS` based on load
- Optimize `BACKUP_COUNT` for storage constraints
- Set appropriate session timeouts

### 💾 **Database Optimization**
- Keep database size reasonable (< 100MB recommended)
- Regular cleanup of unused entries
- Optimize group structure for search performance
- Use tags effectively for filtering

### 🔍 **Search Optimization**
- Use specific search terms when possible
- Leverage group filters to narrow results
- Utilize tags for categorical searches
- Consider entry limits for large datasets

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [KeePass](https://keepass.info/) for the excellent password manager
- [PyKeePass](https://github.com/libkeepass/pykeepass) for Python KeePass integration
- [Anthropic](https://www.anthropic.com/) for the Model Context Protocol
- [Claude](https://claude.ai/) for AI-powered credential management

## Support

- 📖 **Documentation:** [docs/](docs/)
- 🐛 **Bug Reports:** [GitHub Issues](https://github.com/keepass-mcp/keepass-mcp-server/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/keepass-mcp/keepass-mcp-server/discussions)
- 📧 **Email:** support@keepass-mcp.com

## Roadmap

### 🎯 **Current Version (1.0.0)**
- ✅ Complete KeePass integration
- ✅ MCP protocol implementation
- ✅ Advanced search functionality
- ✅ Security and audit features
- ✅ Docker deployment

### 🚀 **Upcoming Features (1.1.0)**
- 🔄 Real-time database synchronization
- 🌐 Web interface for management
- 📱 Mobile app integration
- 🔌 Plugin system for extensions
- 📊 Advanced analytics and reporting

### 🎨 **Future Enhancements (2.0.0)**
- 🤖 AI-powered password policies
- 🔗 Integration with more password managers
- ☁️ Cloud deployment options
- 🔒 Hardware security key support
- 📈 Enterprise features and SSO

---

**Made with ❤️ for secure credential management**
