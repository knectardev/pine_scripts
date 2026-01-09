# Pine Script Library - API Documentation

**Version:** 1.0  
**Base URL:** `http://localhost:5000/api`  
**Date:** January 9, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Data Models](#data-models)
4. [API Endpoints](#api-endpoints)
   - [Scripts](#scripts)
   - [Version Control](#version-control)
   - [Code Operations](#code-operations)
   - [Backups](#backups)
   - [Debug](#debug)
5. [Error Handling](#error-handling)
6. [Examples](#examples)

---

## Overview

The Pine Script Library API provides a RESTful interface for managing TradingView Pine Script files with metadata tracking, version control, and automated code quality validation.

### Features

- ✅ Full CRUD operations for scripts
- ✅ Version control with history tracking
- ✅ Automated code review based on official standards
- ✅ Auto-fix capabilities for common issues
- ✅ LLM-powered smart fixes
- ✅ Backup and restore functionality

### API Characteristics

- **Protocol:** HTTP/REST
- **Data Format:** JSON
- **CORS:** Enabled for all origins
- **Authentication:** None (local development)
- **Rate Limiting:** None (consider adding for production)

---

## Authentication

**Current:** No authentication required (local development only)

**Production Recommendations:**
- Implement API key authentication
- Add JWT tokens for session management
- Consider OAuth2 for third-party integrations

---

## Data Models

### Script Object

```json
{
  "id": "string",                    // Unique identifier
  "name": "string",                  // Display name (required)
  "type": "string",                  // "indicator", "strategy", or "study" (required)
  "version": "string",               // Semantic version (e.g., "1.0.0")
  "currentVersion": "string",        // Active version number
  "pineVersion": number,             // Pine Script version (5 or 6)
  "description": "string",           // Script description
  "author": "string",                // Author name
  "tags": ["string"],                // Searchable tags
  "timeframes": ["string"],          // Recommended timeframes
  "status": "string",                // "active", "testing", "deprecated", or "archived"
  "filePath": "string",              // Path to script file (required)
  "dateCreated": "string",           // ISO 8601 timestamp
  "dateModified": "string",          // ISO 8601 timestamp
  "parameters": [                    // Input parameters
    {
      "name": "string",
      "type": "string",
      "default": any,
      "description": "string"
    }
  ],
  "backtest": {                      // Backtest metrics (for strategies)
    "symbol": "string",
    "timeframe": "string",
    "startDate": "string",
    "endDate": "string",
    "initialCapital": number,
    "netProfit": number,
    "netProfitPercent": number,
    "totalTrades": number,
    "winningTrades": number,
    "losingTrades": number,
    "winRate": number,
    "profitFactor": number,
    "maxDrawdown": number,
    "avgTrade": number,
    "avgWinningTrade": number,
    "avgLosingTrade": number,
    "sharpeRatio": number,
    "notes": "string"
  },
  "versions": [                      // Version history
    {
      "version": "string",
      "filePath": "string",
      "dateCreated": "string",
      "changelog": "string",
      "author": "string",
      "isActive": boolean
    }
  ]
}
```

### Code Review Result Object

```json
{
  "scriptName": "string",
  "reviewedVersion": "string",
  "summary": {
    "totalIssues": number,
    "critical": number,
    "high": number,
    "medium": number,
    "warning": number,
    "passed": number
  },
  "issues": [
    {
      "category": "string",
      "check": "string",
      "severity": "string",          // "CRITICAL", "HIGH", "MEDIUM", "WARNING", "PASS"
      "message": "string",
      "line": number,
      "code": "string",
      "quickfix": {                  // Optional
        "type": "string",
        "old_name": "string",
        "new_name": "string"
      }
    }
  ],
  "recommendations": [
    {
      "category": "string",
      "message": "string"
    }
  ]
}
```

### Version Object

```json
{
  "version": "string",               // Semantic version
  "filePath": "string",              // Path to versioned file
  "dateCreated": "string",           // ISO 8601 timestamp
  "changelog": "string",             // Change description
  "author": "string",                // Author of this version
  "isActive": boolean                // Is this the current version?
}
```

---

## API Endpoints

### Scripts

#### Get All Scripts

```http
GET /api/scripts
```

**Description:** Retrieve all scripts with metadata

**Response:** `200 OK`
```json
{
  "scripts": [Script]
}
```

**Example:**
```bash
curl http://localhost:5000/api/scripts
```

---

#### Get Single Script

```http
GET /api/scripts/:id
```

**Description:** Retrieve a specific script by ID

**Parameters:**
- `id` (path, required) - Script unique identifier

**Response:** `200 OK`
```json
{Script}
```

**Errors:**
- `404 Not Found` - Script not found

**Example:**
```bash
curl http://localhost:5000/api/scripts/abc123
```

---

#### Create Script

```http
POST /api/scripts
```

**Description:** Create a new script with initial version

**Request Body:** (application/json)
```json
{
  "name": "My Strategy",              // Required
  "type": "strategy",                 // Required: "indicator", "strategy", or "study"
  "version": "1.0.0",                 // Optional: defaults to "1.0.0"
  "filePath": "scripts/strategies/my-strategy/my-strategy.pine",  // Required
  "description": "Strategy description",
  "author": "Your Name",
  "tags": ["trend", "momentum"],
  "timeframes": ["1h", "4h"],
  "status": "active",
  "parameters": [...]
}
```

**Response:** `201 Created`
```json
{Script}
```

**Features:**
- ✅ Automatically generates ID if not provided
- ✅ Creates version directory structure
- ✅ Generates initial Pine Script template
- ✅ Initializes version control

**Errors:**
- `400 Bad Request` - Missing required fields
- `409 Conflict` - Script ID already exists
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl -X POST http://localhost:5000/api/scripts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Indicator",
    "type": "indicator",
    "filePath": "scripts/indicators/my-indicator/my-indicator.pine"
  }'
```

---

#### Update Script

```http
PUT /api/scripts/:id
```

**Description:** Update script metadata (not code)

**Parameters:**
- `id` (path, required) - Script unique identifier

**Request Body:** (application/json)
```json
{
  "name": "Updated Name",
  "description": "New description",
  "status": "testing",
  ... any other fields to update
}
```

**Response:** `200 OK`
```json
{Script}
```

**Features:**
- ✅ Automatically updates `dateModified`
- ✅ Preserves `dateCreated`
- ✅ Merges with existing data

**Errors:**
- `404 Not Found` - Script not found
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl -X PUT http://localhost:5000/api/scripts/abc123 \
  -H "Content-Type: application/json" \
  -d '{"status": "testing"}'
```

---

#### Delete Script

```http
DELETE /api/scripts/:id
```

**Description:** Delete a script (soft delete - preserves files)

**Parameters:**
- `id` (path, required) - Script unique identifier

**Response:** `200 OK`
```json
{
  "message": "Script deleted successfully"
}
```

**Note:** Files are NOT deleted from disk, only metadata is removed

**Errors:**
- `404 Not Found` - Script not found
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl -X DELETE http://localhost:5000/api/scripts/abc123
```

---

### Code Operations

#### Get Script Code

```http
GET /api/scripts/:id/code
```

**Description:** Retrieve Pine Script code for current or specific version

**Parameters:**
- `id` (path, required) - Script unique identifier
- `version` (query, optional) - Specific version to retrieve

**Response:** `200 OK`
```json
{
  "code": "string",                  // Pine Script code
  "version": "string",               // Version number
  "filePath": "string"               // File path
}
```

**Errors:**
- `404 Not Found` - Script or version not found
- `500 Internal Server Error` - Server error

**Examples:**
```bash
# Get current version
curl http://localhost:5000/api/scripts/abc123/code

# Get specific version
curl http://localhost:5000/api/scripts/abc123/code?version=1.0.0
```

---

#### Review Script Code

```http
GET /api/scripts/:id/review
```

**Description:** Perform comprehensive code quality review

**Parameters:**
- `id` (path, required) - Script unique identifier
- `version` (query, optional) - Version to review (defaults to current)

**Response:** `200 OK`
```json
{CodeReviewResult}
```

**Validation Categories:**
- Script structure (version declaration, organization)
- Naming conventions (camelCase, SNAKE_CASE)
- Formatting (spacing, indentation)
- Pine Script syntax (ternary, line continuation)
- Performance (plot limits, loop efficiency)
- Logic errors (OHLC, division by zero, strategy API)
- Platform limitations

**Errors:**
- `404 Not Found` - Script or file not found
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl http://localhost:5000/api/scripts/abc123/review
```

---

#### Save Edited Code

```http
POST /api/scripts/:id/save-code
```

**Description:** Save edited code and create new version

**Parameters:**
- `id` (path, required) - Script unique identifier

**Request Body:** (application/json)
```json
{
  "code": "string",                  // Updated Pine Script code
  "newVersion": "string",            // New version number (e.g., "1.0.1")
  "changelog": "string",             // Description of changes
  "author": "string"                 // Author of this version (optional)
}
```

**Response:** `200 OK`
```json
{
  "message": "Code saved successfully",
  "script": {Script},
  "newVersion": {Version}
}
```

**Features:**
- ✅ Creates new version file
- ✅ Injects version metadata into code header
- ✅ Deactivates previous version
- ✅ Updates script metadata

**Errors:**
- `400 Bad Request` - Missing required fields
- `404 Not Found` - Script not found
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl -X POST http://localhost:5000/api/scripts/abc123/save-code \
  -H "Content-Type: application/json" \
  -d '{
    "code": "//@version=5\nindicator(\"My Indicator\")\nplot(close)",
    "newVersion": "1.0.1",
    "changelog": "Fixed bug in calculation"
  }'
```

---

#### Auto-Fix Single Issue

```http
POST /api/scripts/:id/autofix
```

**Description:** Automatically fix a single code issue

**Parameters:**
- `id` (path, required) - Script unique identifier

**Request Body:** (application/json)
```json
{
  "issue": {                         // Issue object from code review
    "quickfix": {
      "type": "string",
      "old_name": "string",
      "new_name": "string"
    }
  },
  "version": "string"                // Version to fix (optional)
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Issue fixed successfully",
  "fixedCode": "string",
  "newVersion": "string"
}
```

**Supported Fix Types:**
- `rename_input_variable` - Rename input to add "Input" suffix
- `add_version` - Add missing version declaration
- `fix_operator_spacing` - Add spaces around operators

**Errors:**
- `400 Bad Request` - Missing required fields or unsupported fix type
- `404 Not Found` - Script not found
- `500 Internal Server Error` - Server error

---

#### Auto-Fix All Issues

```http
POST /api/scripts/:id/auto-fix-all
```

**Description:** Automatically fix all fixable issues

**Parameters:**
- `id` (path, required) - Script unique identifier

**Request Body:** (application/json)
```json
{
  "issues": [{Issue}],               // Array of issues with quickfix
  "version": "string"                // Version to fix (optional)
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "fixedCode": "string",
  "fixesApplied": number,
  "newVersion": "string"
}
```

**Features:**
- ✅ Applies all quick-fixes in sequence
- ✅ Creates new version after fixes
- ✅ Validates code after fixes

**Errors:**
- `400 Bad Request` - Missing required fields
- `404 Not Found` - Script not found
- `500 Internal Server Error` - Server error

---

#### Smart Auto-Fix (LLM)

```http
POST /api/scripts/:id/smart-autofix
```

**Description:** Use LLM to intelligently fix code issues

**Parameters:**
- `id` (path, required) - Script unique identifier

**Request Body:** (application/json)
```json
{
  "issue": {Issue},                  // Issue to fix
  "code": "string",                  // Current code
  "scriptName": "string"
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "fixedCode": "string",
  "explanation": "string",
  "newVersion": "string"
}
```

**Requirements:**
- OpenAI or Anthropic API key configured
- `DEFAULT_LLM_PROVIDER` environment variable set

**Features:**
- ✅ Context-aware fixes
- ✅ Preserves code functionality
- ✅ Follows Pine Script standards
- ✅ Provides explanation of changes

**Errors:**
- `400 Bad Request` - Missing API key
- `404 Not Found` - Script not found
- `500 Internal Server Error` - LLM error

---

### Version Control

#### Get Version History

```http
GET /api/scripts/:id/versions
```

**Description:** Get all versions of a script

**Parameters:**
- `id` (path, required) - Script unique identifier

**Response:** `200 OK`
```json
{
  "currentVersion": "string",
  "versions": [{Version}]
}
```

**Features:**
- ✅ Sorted by date (newest first)
- ✅ Indicates active version
- ✅ Includes changelogs

**Errors:**
- `404 Not Found` - Script not found
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl http://localhost:5000/api/scripts/abc123/versions
```

---

#### Restore Version

```http
POST /api/scripts/:id/versions/:version/restore
```

**Description:** Restore a previous version as the current version

**Parameters:**
- `id` (path, required) - Script unique identifier
- `version` (path, required) - Version to restore (e.g., "1.0.0")

**Response:** `200 OK`
```json
{
  "message": "Version restored successfully",
  "restoredVersion": "string",
  "newActiveVersion": "string",
  "script": {Script}
}
```

**Features:**
- ✅ Creates new version from restored code
- ✅ Preserves version history
- ✅ Updates active version pointer

**Errors:**
- `404 Not Found` - Script or version not found
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl -X POST http://localhost:5000/api/scripts/abc123/versions/1.0.0/restore
```

---

### Backups

#### List Backups

```http
GET /api/backups
```

**Description:** Get list of all backup files

**Response:** `200 OK`
```json
{
  "backups": [
    {
      "filename": "scripts_20260108_120000.json",
      "date": "2026-01-08T12:00:00Z",
      "size": 245678
    }
  ]
}
```

**Features:**
- ✅ Sorted by date (newest first)
- ✅ Includes file size
- ✅ Auto-created on every save operation

**Example:**
```bash
curl http://localhost:5000/api/backups
```

---

#### Restore Backup

```http
POST /api/backups/:filename
```

**Description:** Restore scripts from a backup file

**Parameters:**
- `filename` (path, required) - Backup filename

**Response:** `200 OK`
```json
{
  "message": "Backup restored successfully",
  "scriptsCount": number
}
```

**Warning:** This operation replaces current `scripts.json`

**Errors:**
- `404 Not Found` - Backup file not found
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl -X POST http://localhost:5000/api/backups/scripts_20260108_120000.json
```

---

### Debug

#### Check API Key Status

```http
GET /api/debug/api-key-status
```

**Description:** Check if LLM API keys are configured

**Response:** `200 OK`
```json
{
  "openai": {
    "configured": boolean,
    "model": "string"
  },
  "anthropic": {
    "configured": boolean,
    "model": "string"
  },
  "defaultProvider": "string"
}
```

**Example:**
```bash
curl http://localhost:5000/api/debug/api-key-status
```

---

## Error Handling

### Error Response Format

```json
{
  "error": "string"                  // Error message
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 500 | Internal Server Error | Server error |

---

## Examples

### Complete Workflow Example

#### 1. Create a New Script

```bash
curl -X POST http://localhost:5000/api/scripts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "RSI Divergence Indicator",
    "type": "indicator",
    "filePath": "scripts/indicators/rsi-divergence/rsi-divergence.pine",
    "description": "Detects RSI divergences",
    "author": "John Doe",
    "tags": ["RSI", "divergence", "momentum"]
  }'
```

#### 2. Get the Code

```bash
curl http://localhost:5000/api/scripts/{id}/code
```

#### 3. Review the Code

```bash
curl http://localhost:5000/api/scripts/{id}/review
```

#### 4. Fix Issues

```bash
curl -X POST http://localhost:5000/api/scripts/{id}/autofix \
  -H "Content-Type: application/json" \
  -d '{
    "issue": {
      "quickfix": {
        "type": "rename_input_variable",
        "old_name": "length",
        "new_name": "lengthInput"
      }
    }
  }'
```

#### 5. Save Changes

```bash
curl -X POST http://localhost:5000/api/scripts/{id}/save-code \
  -H "Content-Type: application/json" \
  -d '{
    "code": "...",
    "newVersion": "1.0.1",
    "changelog": "Fixed naming conventions"
  }'
```

#### 6. View Version History

```bash
curl http://localhost:5000/api/scripts/{id}/versions
```

---

## Rate Limiting

**Current:** No rate limiting implemented

**Production Recommendation:**
```python
# Example using Flask-Limiter
@app.route('/api/scripts', methods=['POST'])
@limiter.limit("10 per minute")
def create_script():
    ...
```

---

## CORS Configuration

**Current:** Enabled for all origins (`*`)

**Production Recommendation:**
```python
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})
```

---

## Best Practices

### Making Requests

1. **Always include Content-Type header for POST/PUT**
   ```bash
   -H "Content-Type: application/json"
   ```

2. **Handle errors gracefully**
   ```javascript
   try {
     const response = await fetch('/api/scripts');
     if (!response.ok) throw new Error(await response.json());
   } catch (error) {
     console.error('API error:', error);
   }
   ```

3. **Use proper HTTP methods**
   - GET: Read operations
   - POST: Create operations
   - PUT: Update operations
   - DELETE: Delete operations

4. **Validate data before sending**
   - Check required fields
   - Validate data types
   - Sanitize inputs

---

## WebSocket Support

**Current:** Not implemented

**Future Consideration:** Real-time updates for collaborative editing

---

## Versioning

**API Version:** 1.0  
**Compatibility:** Stable (no breaking changes planned)

**Future Versions:**
- v1.1: Add pagination
- v2.0: Add authentication (breaking change)

---

## Support

For issues and questions:
- Check the [README.md](../README.md)
- Review [CODE_REVIEW_REPORT.md](CODE_REVIEW_REPORT.md)
- Consult [PINE_SCRIPT_STANDARDS.md](PINE_SCRIPT_STANDARDS.md)

---

**Last Updated:** January 9, 2026  
**Maintained By:** Pine Script Library Team
