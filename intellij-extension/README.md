# Resource Schema Guard Rail - IntelliJ Plugin

IntelliJ IDEA plugin for real-time validation of CloudFormation resource schema files using the Guard Rail CLI tool.

## Features

- Automatic validation on file open, edit, and save
- Inline error and warning diagnostics
- Status bar widget showing validation summary
- Manual validation command
- Integration with IntelliJ's Problems tool window

## Requirements

- IntelliJ IDEA 2023.1 or later
- Guard Rail CLI tool installed (`pip install resource-schema-guard-rail`)

## Building

```bash
./gradlew build
```

## Running

```bash
./gradlew runIde
```

## Testing

```bash
./gradlew test
```

## Installation

1. Build the plugin: `./gradlew buildPlugin`
2. Install from disk in IntelliJ: Settings → Plugins → Install Plugin from Disk
3. Select the generated `.zip` file from `build/distributions/`
