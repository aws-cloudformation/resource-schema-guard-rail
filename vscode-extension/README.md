# Resource Schema Guard Rail VS Code Extension

Real-time validation for CloudFormation resource schema files with inline diagnostics.

## Features

- **Real-time validation** - Automatic validation on open, save, and edit with 500ms debouncing
- **Inline diagnostics** - Errors and warnings displayed directly in the editor
- **Status bar integration** - Live error/warning counts at a glance
- **Manual validation** - Command Palette: "Guard Rail: Validate Schema"
- **Delayed Validation** - Validation runs in separate process with smart debouncing

## Requirements

### Python
The extension requires Python to be installed and available in your system PATH:

- **Python 3.7 or higher** (recommended)
- The extension will automatically detect `python3` or `python` commands

**Installation:**
- **macOS/Linux**: Python is often pre-installed. Verify with `python3 --version`
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **Verify installation**: Run `python3 --version` or `python --version` in your terminal

### Guard Rail Tool
The Resource Schema Guard Rail tool must be installed in your workspace:

1. Clone or have the guard-rail repository in your workspace
2. Install Python dependencies:
   i. From pypi.org `pip install resource-schema-guard-rail`
   ii. From the source `pip install . -r requirements.txt`

**Note**: The extension assumes the guard-rail tool is located in the workspace root directory.

## Installation

### For Development

1. **Clone the repository** (if not already done)
   ```bash
   cd vscode-extension
   ```

2. **Install Node.js dependencies**
   ```bash
   npm install
   ```

3. **Compile the TypeScript code**
   ```bash
   npm run compile
   ```

4. **Launch the Extension Development Host**
   - Open the `vscode-extension` folder in VS Code
   - Press `F5` to launch a new VS Code window with the extension loaded
   - Or use the "Run and Debug" panel and select "Run Extension"



## Usage

### Automatic Validation

The extension automatically validates CloudFormation resource schema files:

1. **Open a JSON schema file** in VS Code
2. **Validation runs automatically** when you:
   - Open the file
   - Save the file
   - Make changes (after 500ms of inactivity)
3. **View diagnostics** inline in the editor:
   - Red squiggly lines indicate errors
   - Yellow squiggly lines indicate warnings
4. **Hover over diagnostics** to see detailed information

**Example:**
```
When you open a schema file with a tagging violation, you'll see:
  Line 45: Tags property must be defined in properties section
  Source: guard-rail (TAG016)
```

### Manual Validation

Trigger validation on-demand without saving:

1. **Open the Command Palette** (`Cmd+Shift+P` on macOS, `Ctrl+Shift+P` on Windows/Linux)
2. **Type**: "Guard Rail: Validate Schema"
3. **Press Enter** to run validation on the active file

### Status Bar

The status bar shows a summary of validation results:

- **Format**: `$(error) X $(warning) Y` (where X = errors, Y = warnings)
- **Location**: Bottom-right corner of VS Code
- **Updates**: Automatically after each validation

### Viewing Validation Output

For debugging or detailed logs:

1. **Open the Output panel** (`Cmd+Shift+U` on macOS, `Ctrl+Shift+U` on Windows/Linux)
2. **Select "Guard Rail"** from the dropdown
3. **View**: CLI execution details, errors, and warnings

## Examples

### Example 1: Valid Schema
When you open a valid schema file, no diagnostics appear, and the status bar shows:
```
$(check) Guard Rail: No issues
```

### Example 2: Schema with Errors
Opening a schema with missing required properties:

**File**: `aws-myservice-resource.json`
```json
{
  "typeName": "AWS::MyService::Resource",
  "properties": {
    "Name": {
      "type": "string"
    }
  }
}
```

**Diagnostics shown**:
- Line 1: `Primary identifier must be defined` (Error)
- Line 3: `Tags property is required for taggable resources` (Error)

**Status bar**: `$(error) 2 $(warning) 0`

### Example 3: Schema with Warnings
Opening a schema with non-critical issues:

**Diagnostics shown**:
- Line 15: `Consider adding description for property` (Warning)

**Status bar**: `$(error) 0 $(warning) 1`

## Development

### Building and Testing

1. **Watch mode for continuous compilation**
   ```bash
   npm run watch
   ```

2. **Run unit tests**
   ```bash
   npm test
   ```

3. **Launch Extension Development Host**
   - Press `F5` in VS Code
   - Or use Debug panel → "Run Extension"

4. **Reload extension after changes**
   - In the Extension Development Host window
   - Press `Cmd+R` (macOS) or `Ctrl+R` (Windows/Linux)
   - Or use Command Palette → "Developer: Reload Window"

### Project Structure

```
vscode-extension/
├── src/
│   ├── extension.ts           # Extension entry point
│   ├── diagnosticProvider.ts  # Manages validation lifecycle
│   ├── guardRailExecutor.ts   # Executes CLI tool
│   ├── diagnosticMapper.ts    # Maps results to VS Code diagnostics
│   ├── commands.ts            # Command handlers
│   └── types.ts               # TypeScript type definitions
├── test/
│   ├── diagnosticMapper.test.ts
│   ├── guardRailExecutor.test.ts
│   ├── diagnosticProvider.test.ts
│   └── fixtures/              # Test schema files
├── package.json               # Extension manifest
└── tsconfig.json             # TypeScript configuration
```

## Known Limitations

### Validation Scope
- **Stateless rules only**: The extension runs stateless validation rules that check individual schema files without comparing against previous versions
- **No stateful validation**: Rules that require comparing current schema with previous versions are not supported in this extension

### File Requirements
- **Saved files only**: Unsaved files are not validated automatically. Save the file to trigger validation
- **File size limit**: Files less than 1GB
- **JSON files only**

### Tool Dependencies
- Python 3.7+
- `pip install resource-schema-guard-rail`

### UI Limitations
- **No quick fixes**: The extension does not provide automated fixes for violations (future enhancement)
- **No rule documentation**: Hovering over diagnostics shows the message but not full rule documentation
- **No configuration UI**: All settings use defaults; no configuration options are exposed yet

### Diagnostics at Wrong Line Numbers
**Problem**: Diagnostics appear at incorrect locations

**Solutions**:
1. Ensure the schema file is properly formatted JSON
2. Save the file to refresh validation
3. Check the Output panel for parsing errors
