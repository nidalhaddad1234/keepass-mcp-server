# KeePass MCP Server API Reference

This document provides comprehensive API reference for all tools and resources available in the KeePass MCP Server.

## Table of Contents

1. [Authentication Tools](#authentication-tools)
2. [Search & Retrieval Tools](#search--retrieval-tools)
3. [Entry Management Tools](#entry-management-tools)
4. [Group Management Tools](#group-management-tools)
5. [Password Generation Tools](#password-generation-tools)
6. [Database Operations](#database-operations)
7. [Advanced Analysis Tools](#advanced-analysis-tools)
8. [Resources](#resources)
9. [Error Codes](#error-codes)
10. [Data Models](#data-models)

## Authentication Tools

### `authenticate`

Unlock the KeePass database and create an authenticated session.

**Parameters:**
```typescript
{
  password: string;           // Master password for the database
  key_file?: string;         // Optional path to key file
}
```

**Response:**
```typescript
{
  success: boolean;
  session_token: string;     // Session token for subsequent requests
  unlock_info: {
    unlocked_at: string;     // ISO timestamp
    database_path: string;   // Path to database file
    has_key_file: boolean;   // Whether key file was used
    entry_count: number;     // Total number of entries
    group_count: number;     // Total number of groups
    database_version: string; // KeePass database version
  };
  message: string;
}
```

**Errors:**
- `AUTH_ERROR`: Invalid password or key file
- `DATABASE_ERROR`: Database file not found or corrupted
- `VALIDATION_ERROR`: Missing required parameters

**Example:**
```json
{
  "password": "MySecurePassword123!",
  "key_file": "/path/to/keyfile.key"
}
```

### `logout`

Lock the database and destroy the current session.

**Parameters:**
```typescript
{}
```

**Response:**
```typescript
{
  success: boolean;
  lock_info: {
    locked_at: string;       // ISO timestamp
    success: boolean;
  };
  message: string;
}
```

**Example:**
```json
{}
```

## Search & Retrieval Tools

### `search_credentials`

Search for credentials using advanced filtering and search criteria.

**Parameters:**
```typescript
{
  query?: string;                    // Search query string
  search_fields?: string[];          // Fields to search in
  case_sensitive?: boolean;          // Case-sensitive search
  exact_match?: boolean;            // Require exact string match
  regex_search?: boolean;           // Use regex pattern matching
  tags?: string[];                  // Filter by tags
  group_filter?: string;            // Filter by group name
  date_created_after?: string;      // ISO date string
  date_created_before?: string;     // ISO date string
  date_modified_after?: string;     // ISO date string
  date_modified_before?: string;    // ISO date string
  has_url?: boolean;                // Filter by URL presence
  has_notes?: boolean;              // Filter by notes presence
  has_attachments?: boolean;        // Filter by attachment presence
  password_age_days?: number;       // Find passwords older than N days
  sort_by?: string;                 // Sort method
  limit?: number;                   // Maximum results to return
}
```

**Available `search_fields`:**
- `title` - Entry title
- `username` - Username field
- `url` - URL field
- `notes` - Notes field
- `tags` - Entry tags

**Available `sort_by` options:**
- `relevance` - Sort by search relevance (default)
- `title` - Sort by entry title
- `date_created` - Sort by creation date
- `date_modified` - Sort by modification date

**Response:**
```typescript
{
  success: boolean;
  query: string;
  results_count: number;
  results: Entry[];                 // Array of matching entries
}
```

**Example:**
```json
{
  "query": "github",
  "search_fields": ["title", "url", "tags"],
  "tags": ["development"],
  "limit": 10,
  "sort_by": "relevance"
}
```

### `search_by_url`

Search for credentials specifically by URL with fuzzy matching capabilities.

**Parameters:**
```typescript
{
  url: string;                      // URL to search for
  fuzzy_match?: boolean;            // Enable fuzzy URL matching
}
```

**Response:**
```typescript
{
  success: boolean;
  url: string;
  fuzzy_match: boolean;
  results_count: number;
  results: Entry[];                 // Entries sorted by URL relevance
}
```

**URL Matching Logic:**
1. Exact URL match (score: 10.0)
2. Exact domain match (score: 8.0)
3. Subdomain match (score: 6.0)
4. Domain parts match (score: 4.0)
5. Partial domain match (score: 2.0)

**Example:**
```json
{
  "url": "https://github.com",
  "fuzzy_match": true
}
```

### `get_credential`

Retrieve a specific credential entry by its unique ID.

**Parameters:**
```typescript
{
  entry_id: string;                 // UUID of the entry
  include_password?: boolean;       // Include password in response
  include_history?: boolean;        // Include entry history
}
```

**Response:**
```typescript
{
  success: boolean;
  entry: Entry;                     // Complete entry details
}
```

**Example:**
```json
{
  "entry_id": "550e8400-e29b-41d4-a716-446655440000",
  "include_password": true,
  "include_history": false
}
```

### `list_entries`

List entries in the database or within a specific group.

**Parameters:**
```typescript
{
  group_id?: string;                // ID of specific group
  group_name?: string;              // Name of specific group
  include_passwords?: boolean;      // Include passwords in response
  include_subgroups?: boolean;      // Include entries from subgroups
  sort_by?: string;                 // Sort method
  limit?: number;                   // Maximum entries to return
}
```

**Available `sort_by` options:**
- `title` - Sort by entry title (default)
- `username` - Sort by username
- `date_created` - Sort by creation date
- `date_modified` - Sort by modification date
- `url` - Sort by URL

**Response:**
```typescript
{
  success: boolean;
  group_id?: string;
  group_name?: string;
  entries_count: number;
  entries: Entry[];
}
```

**Example:**
```json
{
  "group_name": "Development",
  "include_passwords": false,
  "include_subgroups": true,
  "sort_by": "title",
  "limit": 50
}
```

### `list_groups`

List groups in the database with optional statistics.

**Parameters:**
```typescript
{
  parent_group_id?: string;         // ID of parent group
  parent_group_name?: string;       // Name of parent group
  include_root?: boolean;           // Include root group
  include_statistics?: boolean;     // Include group statistics
  recursive?: boolean;              // Include all descendant groups
  sort_by?: string;                 // Sort method
}
```

**Available `sort_by` options:**
- `name` - Sort by group name (default)
- `created` - Sort by creation date
- `modified` - Sort by modification date
- `entries_count` - Sort by number of entries

**Response:**
```typescript
{
  success: boolean;
  parent_group_id?: string;
  parent_group_name?: string;
  groups_count: number;
  groups: Group[];
}
```

**Example:**
```json
{
  "include_root": false,
  "include_statistics": true,
  "recursive": false,
  "sort_by": "name"
}
```

### `get_group_info`

Get detailed information about a specific group.

**Parameters:**
```typescript
{
  group_id?: string;                // ID of the group
  group_name?: string;              // Name of the group
  include_entries?: boolean;        // Include group entries
  include_subgroups?: boolean;      // Include subgroups
  include_statistics?: boolean;     // Include group statistics
}
```

**Response:**
```typescript
{
  success: boolean;
  group: Group;                     // Complete group details
}
```

**Example:**
```json
{
  "group_name": "Development",
  "include_entries": true,
  "include_subgroups": true,
  "include_statistics": true
}
```

## Entry Management Tools

### `create_entry`

Create a new password entry in the database.

**Parameters:**
```typescript
{
  title: string;                    // Entry title (required)
  username?: string;                // Username for the entry
  password?: string;                // Password for the entry
  url?: string;                     // URL associated with the entry
  notes?: string;                   // Notes for the entry
  group_id?: string;                // ID of the group to create entry in
  group_name?: string;              // Name of the group (alternative to group_id)
  tags?: string[];                  // List of tags for the entry
  custom_fields?: Record<string, string>; // Custom fields
  generate_password?: boolean;      // Generate password automatically
  password_options?: PasswordOptions; // Options for password generation
  expires?: string;                 // Expiration date (ISO string)
  icon?: number;                    // Icon number for the entry
}
```

**Password Options:**
```typescript
interface PasswordOptions {
  length?: number;                  // Password length (4-128)
  include_uppercase?: boolean;      // Include uppercase letters
  include_lowercase?: boolean;      // Include lowercase letters
  include_numbers?: boolean;        // Include numbers
  include_symbols?: boolean;        // Include symbols
  exclude_ambiguous?: boolean;      // Exclude ambiguous characters
  min_uppercase?: number;           // Minimum uppercase letters
  min_lowercase?: number;           // Minimum lowercase letters
  min_numbers?: number;             // Minimum numbers
  min_symbols?: number;             // Minimum symbols
  custom_symbols?: string;          // Custom symbol set
  forbidden_chars?: string;         // Characters to exclude
}
```

**Response:**
```typescript
{
  success: boolean;
  entry: Entry;                     // Created entry details
  message: string;
}
```

**Example:**
```json
{
  "title": "GitHub Account",
  "username": "developer",
  "url": "https://github.com",
  "notes": "Development account with 2FA",
  "group_name": "Development",
  "tags": ["development", "git", "important"],
  "custom_fields": {
    "API_Token": "ghp_xxxxxxxxxxxxxxxxxxxx",
    "Two_Factor_Auth": "Enabled"
  },
  "generate_password": true,
  "password_options": {
    "length": 20,
    "include_symbols": true,
    "exclude_ambiguous": true,
    "min_symbols": 2
  }
}
```

### `update_entry`

Update an existing entry in the database.

**Parameters:**
```typescript
{
  entry_id: string;                 // UUID of the entry to update
  title?: string;                   // New title
  username?: string;                // New username
  password?: string;                // New password
  url?: string;                     // New URL
  notes?: string;                   // New notes
  tags?: string[];                  // New tags
  custom_fields?: Record<string, string>; // New custom fields
  expires?: string;                 // New expiration date
  icon?: number;                    // New icon number
  generate_password?: boolean;      // Generate new password
  password_options?: PasswordOptions; // Password generation options
}
```

**Response:**
```typescript
{
  success: boolean;
  entry: Entry;                     // Updated entry details
  message: string;
}
```

**Example:**
```json
{
  "entry_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "GitHub Account (Updated)",
  "generate_password": true,
  "password_options": {
    "length": 24,
    "include_symbols": true
  }
}
```

### `delete_entry`

Delete an entry from the database.

**Parameters:**
```typescript
{
  entry_id: string;                 // UUID of the entry to delete
  permanent?: boolean;              // Permanently delete vs move to recycle bin
}
```

**Response:**
```typescript
{
  success: boolean;
  result: {
    entry_id: string;
    title: string;
    deleted_at: string;             // ISO timestamp
    permanent: boolean;
    success: boolean;
  };
  message: string;
}
```

**Example:**
```json
{
  "entry_id": "550e8400-e29b-41d4-a716-446655440000",
  "permanent": false
}
```

### `move_entry`

Move an entry to a different group.

**Parameters:**
```typescript
{
  entry_id: string;                 // UUID of the entry to move
  target_group_id?: string;         // ID of the target group
  target_group_name?: string;       // Name of the target group
}
```

**Response:**
```typescript
{
  success: boolean;
  result: {
    entry_id: string;
    title: string;
    old_group: string;
    new_group: string;
    moved_at: string;               // ISO timestamp
    success: boolean;
  };
  message: string;
}
```

**Example:**
```json
{
  "entry_id": "550e8400-e29b-41d4-a716-446655440000",
  "target_group_name": "Work Accounts"
}
```

### `duplicate_entry`

Create a duplicate of an existing entry.

**Parameters:**
```typescript
{
  entry_id: string;                 // UUID of the entry to duplicate
  new_title?: string;               // Title for the duplicate
  target_group_id?: string;         // Target group for duplicate
  target_group_name?: string;       // Target group name
}
```

**Response:**
```typescript
{
  success: boolean;
  entry: Entry;                     // Duplicated entry details
  message: string;
}
```

**Example:**
```json
{
  "entry_id": "550e8400-e29b-41d4-a716-446655440000",
  "new_title": "GitHub Account (Backup)",
  "target_group_name": "Backup Accounts"
}
```

## Group Management Tools

### `create_group`

Create a new group in the database.

**Parameters:**
```typescript
{
  name: string;                     // Group name (required)
  parent_group_id?: string;         // ID of the parent group
  parent_group_name?: string;       // Name of the parent group
  notes?: string;                   // Notes for the group
  icon?: number;                    // Icon number for the group
  expires?: string;                 // Expiration date (ISO string)
}
```

**Response:**
```typescript
{
  success: boolean;
  group: Group;                     // Created group details
  message: string;
}
```

**Example:**
```json
{
  "name": "Development Tools",
  "parent_group_name": "Work",
  "notes": "Development tools and services",
  "icon": 1
}
```

### `update_group`

Update an existing group.

**Parameters:**
```typescript
{
  group_id?: string;                // ID of the group to update
  group_name?: string;              // Name of the group to update
  new_name?: string;                // New name for the group
  notes?: string;                   // New notes
  icon?: number;                    // New icon number
  expires?: string;                 // New expiration date
}
```

**Response:**
```typescript
{
  success: boolean;
  group: Group;                     // Updated group details
  message: string;
}
```

**Example:**
```json
{
  "group_name": "Development",
  "new_name": "Development & Testing",
  "notes": "Development and testing tools",
  "icon": 15
}
```

### `delete_group`

Delete a group from the database.

**Parameters:**
```typescript
{
  group_id?: string;                // ID of the group to delete
  group_name?: string;              // Name of the group to delete
  force?: boolean;                  // Force deletion even if group has content
  move_entries_to?: string;         // Group ID to move entries to before deletion
}
```

**Response:**
```typescript
{
  success: boolean;
  result: {
    group_id: string;
    name: string;
    deleted_at: string;             // ISO timestamp
    entries_moved: number;
    target_group?: string;
    forced: boolean;
    success: boolean;
  };
  message: string;
}
```

**Example:**
```json
{
  "group_name": "Old Projects",
  "force": false,
  "move_entries_to": "550e8400-e29b-41d4-a716-446655440001"
}
```

### `move_group`

Move a group to a different parent group.

**Parameters:**
```typescript
{
  group_id?: string;                // ID of the group to move
  group_name?: string;              // Name of the group to move
  target_parent_id?: string;        // ID of the target parent group
  target_parent_name?: string;      // Name of the target parent group
}
```

**Response:**
```typescript
{
  success: boolean;
  result: {
    group_id: string;
    name: string;
    old_parent: string;
    new_parent: string;
    moved_at: string;               // ISO timestamp
    success: boolean;
  };
  message: string;
}
```

**Example:**
```json
{
  "group_name": "Personal Projects",
  "target_parent_name": "Personal"
}
```

## Password Generation Tools

### `generate_password`

Generate a secure password with customizable options.

**Parameters:**
```typescript
{
  length?: number;                  // Password length (default: 16)
  include_uppercase?: boolean;      // Include uppercase letters (default: true)
  include_lowercase?: boolean;      // Include lowercase letters (default: true)
  include_numbers?: boolean;        // Include numbers (default: true)
  include_symbols?: boolean;        // Include symbols (default: true)
  exclude_ambiguous?: boolean;      // Exclude ambiguous characters (default: false)
  exclude_similar?: boolean;        // Exclude similar characters (default: false)
  min_uppercase?: number;           // Minimum uppercase letters (default: 1)
  min_lowercase?: number;           // Minimum lowercase letters (default: 1)
  min_numbers?: number;             // Minimum numbers (default: 1)
  min_symbols?: number;             // Minimum symbols (default: 1)
  custom_symbols?: string;          // Custom symbol set
  forbidden_chars?: string;         // Characters to exclude
}
```

**Response:**
```typescript
{
  success: boolean;
  password: string;                 // Generated password
  strength_analysis: {
    score: number;                  // Strength score (0-100)
    strength: string;               // Strength description
    feedback: string[];             // Improvement suggestions
    length: number;
    has_uppercase: boolean;
    has_lowercase: boolean;
    has_numbers: boolean;
    has_symbols: boolean;
    has_ambiguous: boolean;
    character_sets: number;
    entropy: number;
  };
  options_used: PasswordOptions;
}
```

**Example:**
```json
{
  "length": 20,
  "include_uppercase": true,
  "include_lowercase": true,
  "include_numbers": true,
  "include_symbols": true,
  "exclude_ambiguous": true,
  "min_symbols": 3
}
```

## Database Operations

### `save_database`

Manually save the database to disk.

**Parameters:**
```typescript
{
  reason?: string;                  // Reason for saving (default: "manual")
}
```

**Response:**
```typescript
{
  success: boolean;
  save_info: {
    saved_at: string;               // ISO timestamp
    reason: string;
    backup_created: boolean;
    backup_info?: BackupInfo;
    success: boolean;
  };
  message: string;
}
```

**Example:**
```json
{
  "reason": "manual_checkpoint"
}
```

### `create_backup`

Create a backup of the database.

**Parameters:**
```typescript
{
  reason?: string;                  // Reason for backup (default: "manual")
  compress?: boolean;               // Compress the backup (default: true)
  verify?: boolean;                 // Verify backup integrity (default: true)
}
```

**Response:**
```typescript
{
  success: boolean;
  backup_info: BackupInfo;
  message: string;
}
```

**Example:**
```json
{
  "reason": "before_major_changes",
  "compress": true,
  "verify": true
}
```

### `get_database_info`

Get information and statistics about the database.

**Parameters:**
```typescript
{}
```

**Response:**
```typescript
{
  success: boolean;
  database_info: {
    database_path: string;
    is_locked: boolean;
    last_saved?: string;            // ISO timestamp
    version: string;
    encryption: string;
    total_entries: number;
    total_groups: number;
    entries_with_passwords: number;
    entries_with_urls: number;
    root_group_name: string;
    database_size_bytes: number;
    has_recycle_bin: boolean;
    auto_save_enabled: boolean;
  };
}
```

**Example:**
```json
{}
```

### `health_check`

Perform a comprehensive health check on the system.

**Parameters:**
```typescript
{}
```

**Response:**
```typescript
{
  success: boolean;
  health_check: {
    timestamp: string;              // ISO timestamp
    database_exists: boolean;
    database_accessible: boolean;
    database_locked: boolean;
    backup_directory_exists: boolean;
    recent_backup_available: boolean;
    latest_backup_age_days?: number;
    issues: string[];               // List of detected issues
    status: string;                 // "healthy" | "issues_detected" | "error"
  };
}
```

**Example:**
```json
{}
```

## Advanced Analysis Tools

### `search_weak_passwords`

Find entries with weak passwords based on configurable criteria.

**Parameters:**
```typescript
{
  min_length?: number;              // Minimum password length (default: 8)
  require_complexity?: boolean;     // Require character complexity (default: true)
}
```

**Response:**
```typescript
{
  success: boolean;
  criteria: {
    min_length: number;
    require_complexity: boolean;
  };
  weak_entries_count: number;
  weak_entries: Array<Entry & {
    weakness_reasons: string[];     // Reasons why password is weak
    password_strength: string;      // Strength rating
  }>;
}
```

**Example:**
```json
{
  "min_length": 12,
  "require_complexity": true
}
```

### `search_duplicates`

Find duplicate entries based on specified fields.

**Parameters:**
```typescript
{
  check_fields?: string[];          // Fields to check for duplicates
}
```

**Available `check_fields`:**
- `title` - Entry title
- `username` - Username field
- `url` - URL field

**Response:**
```typescript
{
  success: boolean;
  check_fields: string[];
  duplicate_groups_count: number;
  duplicate_groups: Entry[][];      // Groups of duplicate entries
}
```

**Example:**
```json
{
  "check_fields": ["title", "username", "url"]
}
```

### `validate_entries`

Validate all entries in the database and identify issues.

**Parameters:**
```typescript
{}
```

**Response:**
```typescript
{
  success: boolean;
  validation_results: {
    weak_passwords: Entry[];
    duplicate_titles: Entry[];
    missing_urls: Entry[];
    expired_entries: Entry[];
    empty_passwords: Entry[];
    total_entries: number;
    summary: {
      total_issues: number;
      validation_date: string;     // ISO timestamp
    };
  };
}
```

**Example:**
```json
{}
```

## Resources

The server provides these MCP resources for additional data access:

### `keepass://database/info`

Provides current database information and statistics.

**Content-Type:** `application/json`

**Content:** Same as `get_database_info` response data.

### `keepass://groups/hierarchy`

Provides complete group hierarchy structure.

**Content-Type:** `application/json`

**Content:** Hierarchical group structure with nested children.

### `keepass://backup/list`

Provides list of available database backups.

**Content-Type:** `application/json`

**Content:** Array of backup information objects.

## Error Codes

### Authentication Errors
- `AUTH_ERROR` - Authentication failed
- `SESSION_EXPIRED` - Session has expired
- `RATE_LIMITED` - Too many authentication attempts

### Database Errors
- `DATABASE_ERROR` - General database error
- `DATABASE_LOCKED` - Database is locked
- `DATABASE_CORRUPTED` - Database file is corrupted

### Validation Errors
- `VALIDATION_ERROR` - Input validation failed
- `ENTRY_NOT_FOUND` - Entry does not exist
- `GROUP_NOT_FOUND` - Group does not exist
- `DUPLICATE_ENTRY` - Entry already exists

### Security Errors
- `SECURITY_ERROR` - Security violation
- `READ_ONLY_MODE` - Operation not allowed in read-only mode
- `CONCURRENT_ACCESS` - Concurrent access conflict

### Operation Errors
- `BACKUP_ERROR` - Backup operation failed
- `IMPORT_ERROR` - Import operation failed
- `EXPORT_ERROR` - Export operation failed
- `OPERATION_TIMEOUT` - Operation timed out

## Data Models

### Entry

```typescript
interface Entry {
  id: string;                       // UUID
  title: string;                    // Entry title
  username: string;                 // Username
  password?: string;                // Password (only if requested)
  url: string;                      // URL
  notes: string;                    // Notes
  group: string;                    // Group name
  group_id: string;                 // Group UUID
  created: string;                  // ISO timestamp
  modified: string;                 // ISO timestamp
  accessed: string;                 // ISO timestamp
  expires?: string;                 // ISO timestamp
  icon: number;                     // Icon number
  tags: string[];                   // Tags array
  custom_fields: Record<string, string>; // Custom fields
  relevance_score?: number;         // Search relevance score
  history?: HistoryEntry[];         // Entry history
}
```

### Group

```typescript
interface Group {
  id: string;                       // UUID
  name: string;                     // Group name
  notes: string;                    // Group notes
  icon: number;                     // Icon number
  parent_id?: string;               // Parent group UUID
  parent_name?: string;             // Parent group name
  created: string;                  // ISO timestamp
  modified: string;                 // ISO timestamp
  expires?: string;                 // ISO timestamp
  path: string;                     // Full group path
  entries?: Entry[];                // Group entries (if requested)
  entries_count?: number;           // Number of entries
  subgroups?: Group[];              // Subgroups (if requested)
  subgroups_count?: number;         // Number of subgroups
  statistics?: GroupStatistics;     // Group statistics (if requested)
  children?: Group[];               // Hierarchical children
}
```

### BackupInfo

```typescript
interface BackupInfo {
  filename: string;                 // Backup filename
  path: string;                     // Full backup path
  created_at: string;               // ISO timestamp
  reason: string;                   // Backup reason
  original_size: number;            // Original file size in bytes
  backup_size: number;              // Backup file size in bytes
  compressed: boolean;              // Whether backup is compressed
  checksum: string;                 // SHA256 checksum
  verified: boolean;                // Whether backup was verified
}
```

### GroupStatistics

```typescript
interface GroupStatistics {
  group_id: string;
  group_name: string;
  total_entries: number;
  total_subgroups: number;
  entries_with_passwords: number;
  entries_without_passwords: number;
  entries_with_urls: number;
  entries_with_notes: number;
  password_strength: {
    weak_passwords: number;
    strong_passwords: number;
  };
  recent_activity: {
    created_last_30_days: number;
    modified_last_30_days: number;
  };
  include_subgroups: boolean;
  calculated_at: string;            // ISO timestamp
}
```

### HistoryEntry

```typescript
interface HistoryEntry {
  version: number;                  // History version number
  title: string;                    // Title at this version
  username: string;                 // Username at this version
  url: string;                      // URL at this version
  modified_at: string;              // ISO timestamp
  notes_length: number;             // Length of notes field
}
```

## Rate Limiting

The server implements rate limiting to prevent abuse:

- **Authentication attempts:** Maximum 3 attempts per 5-minute window per user
- **Concurrent operations:** Configurable maximum concurrent operations (default: 5)
- **Session timeout:** Configurable session timeout (default: 3600 seconds)

## Pagination

For tools that return large result sets, use the `limit` parameter to control the number of results returned. The server will return results in order of relevance or the specified sort criteria.

## Security Considerations

1. **Passwords in responses:** Passwords are only included when explicitly requested with `include_password: true`
2. **Audit logging:** All operations are logged for audit purposes (without sensitive data)
3. **Session management:** Sessions automatically expire after the configured timeout
4. **Read-only mode:** When in read-only mode, all write operations will return `READ_ONLY_MODE` error
5. **Input validation:** All inputs are validated and sanitized before processing

## Performance Tips

1. **Use specific searches:** More specific search queries return faster results
2. **Limit results:** Use the `limit` parameter to avoid large result sets
3. **Group filtering:** Filter by group to narrow search scope
4. **Tag usage:** Use tags for efficient categorical filtering
5. **Caching:** The server implements intelligent caching for frequently accessed data
