# KeePass MCP Server Usage Examples

This document provides comprehensive examples of how to use the KeePass MCP Server with Claude Desktop and other MCP clients.

## Table of Contents

1. [Basic Setup](#basic-setup)
2. [Authentication](#authentication)
3. [Searching Credentials](#searching-credentials)
4. [Managing Entries](#managing-entries)
5. [Managing Groups](#managing-groups)
6. [Password Generation](#password-generation)
7. [Database Operations](#database-operations)
8. [Advanced Features](#advanced-features)
9. [Browser Automation Examples](#browser-automation-examples)
10. [Troubleshooting](#troubleshooting)

## Basic Setup

### Claude Desktop Configuration

Add the following to your `claude_desktop_config.json`:

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

### Environment Variables

Create a `.env` file in your project directory:

```bash
KEEPASS_DB_PATH=/path/to/your/database.kdbx
KEEPASS_KEY_FILE=/path/to/your/keyfile.key
KEEPASS_BACKUP_DIR=./backups
KEEPASS_ACCESS_MODE=readwrite
KEEPASS_AUTO_SAVE=true
KEEPASS_SESSION_TIMEOUT=3600
LOG_LEVEL=INFO
```

## Authentication

### Basic Authentication

```markdown
**User**: Please unlock my KeePass database

**Claude**: I'll help you unlock your KeePass database. I'll need your master password.

**User**: The password is MySecurePassword123!

**Claude**: I'll authenticate with your KeePass database now.
```

*Claude will use the `authenticate` tool with the provided password.*

### Authentication with Key File

```markdown
**User**: Please unlock my database using both password and key file

**Claude**: I'll unlock your database using both the master password and key file. Please provide your master password.

**User**: MySecurePassword123!

**Claude**: I'll authenticate using both your password and the configured key file.
```

## Searching Credentials

### Basic Search

```markdown
**User**: Find my GitHub credentials

**Claude**: I'll search for your GitHub credentials in the database.
```

*Claude will use the `search_credentials` tool with query "GitHub".*

### URL-Based Search

```markdown
**User**: I need credentials for github.com

**Claude**: I'll search for credentials specifically for github.com.
```

*Claude will use the `search_by_url` tool with URL "github.com".*

### Advanced Search

```markdown
**User**: Find all work-related accounts with the tag "important"

**Claude**: I'll search for entries tagged as "important" in work-related groups.
```

*Claude will use advanced search parameters with tags filter.*

### Search with Filters

```markdown
**User**: Show me all entries in the "Work" group that were created in the last 30 days

**Claude**: I'll find all recent entries in your Work group.
```

## Managing Entries

### Creating New Entries

```markdown
**User**: Create a new entry for my Netflix account. Username is john@email.com, and please generate a strong password.

**Claude**: I'll create a new Netflix entry with your username and generate a secure password.
```

*Claude will use the `create_entry` tool with password generation enabled.*

### Updating Entries

```markdown
**User**: Update my GitHub entry to change the password to NewSecurePass2024!

**Claude**: I'll update your GitHub entry with the new password.
```

*Claude will search for the GitHub entry and use the `update_entry` tool.*

### Moving Entries

```markdown
**User**: Move my banking entries to a new "Finance" group

**Claude**: I'll help you move your banking entries to a Finance group. First, let me find your banking entries and create the Finance group if it doesn't exist.
```

### Deleting Entries

```markdown
**User**: Delete the old Twitter account entry

**Claude**: I'll find and delete the old Twitter account entry. Should I move it to the recycle bin or permanently delete it?

**User**: Move it to recycle bin for now

**Claude**: I'll move the Twitter entry to the recycle bin.
```

## Managing Groups

### Creating Groups

```markdown
**User**: Create a new group called "Development Tools" under the "Work" group

**Claude**: I'll create a new "Development Tools" group under your existing "Work" group.
```

### Organizing Groups

```markdown
**User**: Reorganize my groups - create "Personal" and "Professional" as main categories

**Claude**: I'll help you reorganize your groups with Personal and Professional as main categories. This will involve creating the new groups and moving existing entries.
```

## Password Generation

### Basic Password Generation

```markdown
**User**: Generate a 16-character password with symbols

**Claude**: I'll generate a secure 16-character password with symbols for you.
```

### Custom Password Requirements

```markdown
**User**: Generate a password that's 20 characters long, must include at least 3 numbers and 2 symbols, but exclude ambiguous characters

**Claude**: I'll generate a custom password meeting your specific requirements.
```

### Password Strength Analysis

```markdown
**User**: Check the strength of this password: MyPassword123

**Claude**: I'll analyze the strength of that password and provide recommendations for improvement.
```

## Database Operations

### Manual Save

```markdown
**User**: Save my database changes

**Claude**: I'll save your KeePass database and create a backup.
```

### Creating Backups

```markdown
**User**: Create a backup of my database before I make changes

**Claude**: I'll create a backup of your database for safety.
```

### Database Information

```markdown
**User**: Show me information about my database

**Claude**: I'll provide detailed information about your KeePass database including statistics and health status.
```

## Advanced Features

### Finding Weak Passwords

```markdown
**User**: Check my database for weak passwords

**Claude**: I'll scan your database for entries with weak passwords and provide recommendations.
```

### Finding Duplicates

```markdown
**User**: Find any duplicate entries in my database

**Claude**: I'll search for duplicate entries based on title, username, and URL.
```

### Entry Validation

```markdown
**User**: Validate all my entries and find any issues

**Claude**: I'll perform a comprehensive validation of all entries in your database.
```

### Bulk Operations

```markdown
**User**: Import these credentials from my CSV file

**Claude**: I'll help you import credentials from your CSV file. Please share the file or the data you'd like to import.
```

## Browser Automation Examples

### Getting Credentials for Current Website

```markdown
**User**: I'm on github.com and need my login credentials

**Claude**: I'll find your GitHub credentials for you.
```

*Returns credentials in format suitable for browser automation tools.*

### Auto-Type Sequence Generation

```markdown
**User**: Give me the auto-type sequence for my bank login

**Claude**: I'll provide the login sequence for your banking credentials.
```

*Response includes username, tab, password, enter sequence.*

## Integration Examples

### With Browser Automation

```python
# Example Python script using the credentials
import requests

# Get credentials from KeePass MCP Server
credentials = claude_get_credentials("github.com")

# Use in automation
session = requests.Session()
login_data = {
    "username": credentials["username"],
    "password": credentials["password"]
}
response = session.post("https://github.com/login", data=login_data)
```

### With Selenium

```python
from selenium import webdriver
from selenium.webdriver.common.by import By

# Get credentials
creds = claude_get_credentials("github.com")

# Use with Selenium
driver = webdriver.Chrome()
driver.get("https://github.com/login")
driver.find_element(By.NAME, "login").send_keys(creds["username"])
driver.find_element(By.NAME, "password").send_keys(creds["password"])
driver.find_element(By.NAME, "commit").click()
```

## Common Workflows

### New Account Setup Workflow

```markdown
**User**: I'm creating a new account on example.com. Help me set up secure credentials.

**Claude**: I'll help you create secure credentials for example.com:

1. First, I'll generate a strong password
2. Then I'll create a new entry in your KeePass database
3. I'll organize it in the appropriate group

What username would you like to use?

**User**: john.doe@email.com

**Claude**: Perfect! I'll create the entry with that username and a generated password.
```

### Password Update Workflow

```markdown
**User**: I need to update my password for banking.com due to a security notice

**Claude**: I'll help you update your banking password securely:

1. First, let me find your current banking entry
2. I'll generate a new secure password
3. I'll update the entry with the new password
4. I'll create a backup before making changes

Let me start by finding your banking entry.
```

## Error Handling Examples

### Database Locked

```markdown
**User**: Get my email password

**Claude**: I need to unlock your KeePass database first. The database is currently locked for security. Please provide your master password.
```

### Entry Not Found

```markdown
**User**: Get my MySpace credentials

**Claude**: I couldn't find any entries for MySpace in your database. Would you like me to:
1. Search with different terms
2. Create a new MySpace entry
3. Show you all available entries to browse
```

### Read-Only Mode

```markdown
**User**: Create a new entry for Discord

**Claude**: I'm currently in read-only mode and cannot create new entries. The server configuration prevents write operations. You can:
1. Ask an administrator to enable write mode
2. View existing entries instead
```

## Security Best Practices

### Session Management

```markdown
**User**: I'm done working, please lock my database

**Claude**: I'll lock your KeePass database and clear all session data for security.
```

### Backup Verification

```markdown
**User**: Verify my latest backup

**Claude**: I'll verify the integrity of your most recent backup and confirm it's valid.
```

## Troubleshooting

### Connection Issues

```markdown
**User**: The server seems unresponsive

**Claude**: Let me check the server health and diagnose any issues.
```

### Performance Issues

```markdown
**User**: Searches are taking too long

**Claude**: I'll check the database performance and provide optimization suggestions.
```

### Configuration Issues

```markdown
**User**: I'm getting authentication errors

**Claude**: Let me help troubleshoot your authentication setup. This could be related to:
1. Incorrect master password
2. Missing or invalid key file
3. Database file permissions
4. Configuration issues
```

## Tips and Tricks

1. **Use Tags Effectively**: Tag your entries with categories like "work", "personal", "critical" for easier searching.

2. **Regular Backups**: Set up automatic backups to protect your data.

3. **Password Auditing**: Regularly check for weak or duplicate passwords.

4. **Group Organization**: Use a hierarchical group structure to keep entries organized.

5. **Custom Fields**: Use custom fields for storing additional information like security questions, account numbers, or notes.

6. **Browser Integration**: Use URL matching for automatic credential suggestions when browsing.

7. **Secure Sharing**: Use read-only mode when sharing access with others.

8. **Session Timeouts**: Configure appropriate session timeouts for your security needs.

9. **Audit Logging**: Enable audit logging to track database access and modifications.

10. **Multi-Factor Authentication**: Store 2FA backup codes and recovery information in notes or custom fields.
