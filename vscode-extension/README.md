# Resource Schema Guard Rail VS Code Extension

A Visual Studio Code extension that provides real-time validation for CloudFormation resource schema files using the Resource Schema Guard Rail linting tool. Get instant feedback on schema violations with inline diagnostics, just like ESLint or other popular linters.

## Features

### 🔍 Real-Time Validation
- Automatic validation when opening, saving, or editing JSON schema files
- Inline error and warning diagnostics displayed directly in the editor
- Debounced validation (500ms) to avoid excessive executions during rapid typing

### 📊 Status Bar Integration
- Live error and warning counts displayed in the status bar
- Quick visibility into schema health at a glance

### ⚡ Manual Validation
- Command Palette command: "Guard Rail: Validate Schema"
- Validate on-demand without saving files

### 🎯 Detailed Diagnostics
- Hover over diagnostics to see full rule details
- Each diagnostic includes the rule name (check_id) and violation message
- Severity-based categorization (errors vs warnings)

### 🚀 Performance Optimized
- Validation runs in separate process to avoid blocking the editor
- Smart debouncing prevents excessive CLI executions
- Automatic diagnostic clearing when files are closed

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
2. Install Python dependencies: `pip install -r requirements.txt`
3. The extension will execute the tool as: `python -m src.cli`

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

### For Production Use

1. **Package the extension**
   ```bash
   npm install -g @vscode/vsce
   vsce package
   ```

2. **Install the .vsix file**
   ```bash
   code --install-extension guard-rail-vscode-0.1.0.vsix
   ```

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

## Configuration

Currently, the extension uses default settings. Future versions may include:
- Custom rule selection
- Validation timeout configuration
- File size limits
- Debounce delay customization

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

### Adding New Features

1. Update type definitions in `types.ts`
2. Implement core logic in appropriate module
3. Add unit tests in `test/` directory
4. Update this README with new features
5. Test in Extension Development Host

## Known Limitations

### Validation Scope
- **Stateless rules only**: The extension runs stateless validation rules that check individual schema files without comparing against previous versions
- **No stateful validation**: Rules that require comparing current schema with previous versions are not supported in this extension

### File Requirements
- **Saved files only**: Unsaved files are not validated automatically. Save the file to trigger validation
- **File size limit**: Files larger than 1MB are skipped to maintain performance
- **JSON files only**: The extension activates only for JSON language files

### Tool Dependencies
- **Workspace installation required**: The guard-rail tool must be installed in the workspace root directory
- **Python required**: Python 3.7+ must be available in the system PATH
- **No bundled CLI**: The extension does not bundle the guard-rail tool; it must be installed separately

### Performance
- **30-second timeout**: Validation processes that take longer than 30 seconds are terminated
- **Sequential validation**: Only one validation runs per file at a time
- **No caching**: Validation results are not cached between sessions (future enhancement)

### Error Handling
- **CLI errors**: If the guard-rail CLI fails, error details are logged to the Output panel
- **Python not found**: If Python is not available, an error notification is displayed
- **Parse errors**: If CLI output cannot be parsed, validation is skipped with an error message

### UI Limitations
- **No quick fixes**: The extension does not provide automated fixes for violations (future enhancement)
- **No rule documentation**: Hovering over diagnostics shows the message but not full rule documentation
- **No configuration UI**: All settings use defaults; no configuration options are exposed yet

## Troubleshooting

### "Python not found" Error
**Problem**: Extension cannot find Python executable

**Solutions**:
1. Verify Python is installed: `python3 --version` or `python --version`
2. Ensure Python is in your system PATH
3. Restart VS Code after installing Python

### "Guard Rail CLI not found" Error
**Problem**: Extension cannot locate the guard-rail tool

**Solutions**:
1. Verify the guard-rail tool is in your workspace root
2. Check that `src/cli.py` exists in the workspace
3. Install dependencies: `pip install -r requirements.txt`
4. Restart VS Code

### Validation Not Running
**Problem**: No diagnostics appear when opening schema files

**Solutions**:
1. Check the Output panel (select "Guard Rail") for error messages
2. Verify the file is saved (unsaved files are not validated)
3. Check file size (files >1MB are skipped)
4. Manually trigger validation: Command Palette → "Guard Rail: Validate Schema"

### Diagnostics at Wrong Line Numbers
**Problem**: Diagnostics appear at incorrect locations

**Solutions**:
1. Ensure the schema file is properly formatted JSON
2. Save the file to refresh validation
3. Check the Output panel for parsing errors

### Extension Not Activating
**Problem**: Extension does not load when opening JSON files

**Solutions**:
1. Verify the extension is installed and enabled
2. Check VS Code version compatibility (requires VS Code 1.80.0+)
3. Reload VS Code window: Command Palette → "Developer: Reload Window"

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass: `npm test`
5. Submit a pull request

## License

See the LICENSE file in the repository root.

## Support

For issues, questions, or feature requests:
- Check the [Known Limitations](#known-limitations) section
- Review the [Troubleshooting](#troubleshooting) guide
- Open an issue in the repository

## Changelog

### Version 0.1.0 (Initial Release)
- Real-time validation for CloudFormation resource schemas
- Inline error and warning diagnostics
- Status bar integration
- Manual validation command
- Debounced validation for performance
- Output channel for debugging
