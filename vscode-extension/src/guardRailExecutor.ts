/**
 * Guard Rail CLI Executor
 * Handles execution of the guard-rail CLI tool
 */

import { spawn } from 'child_process';
import { GuardRailResult } from './types';

/**
 * Executes the Guard Rail CLI tool and parses results
 */
export class GuardRailExecutor {
  private workspaceRoot: string;
  private outputChannel: any; // vscode.OutputChannel

  constructor(workspaceRoot: string, outputChannel?: any) {
    this.workspaceRoot = workspaceRoot;
    this.outputChannel = outputChannel;
  }

  /**
   * Logs a message to the output channel if available
   */
  private log(message: string): void {
    if (this.outputChannel) {
      this.outputChannel.appendLine(`[GuardRailExecutor] ${message}`);
    }
  }

  /**
   * Logs an error to the output channel if available
   */
  private logError(message: string, error?: Error): void {
    if (this.outputChannel) {
      const errorDetails = error ? ` - ${error.message}` : '';
      this.outputChannel.appendLine(`[GuardRailExecutor] ERROR: ${message}${errorDetails}`);
    }
  }

  /**
   * Executes the Guard Rail CLI tool on a schema file
   * @param schemaPath Absolute path to the schema file to validate
   * @returns Parsed validation results
   * @throws Error if execution fails
   */
  async execute(schemaPath: string): Promise<GuardRailResult[]> {
    this.log(`Starting validation for schema: ${schemaPath}`);

    // Build command arguments
    // Command: guard-rail --schema file://<path> --json
    // The --json flag outputs JSON format for programmatic consumption
    const args = [
      '--schema',
      `file://${schemaPath}`,
      '--json'
    ];

    const command = 'guard-rail';
    this.log(`Executing command: ${command} ${args.join(' ')}`);
    this.log(`Working directory: ${this.workspaceRoot}`);

    return new Promise((resolve, reject) => {
      let childProcess;

      try {
        childProcess = spawn(command, args, {
          cwd: this.workspaceRoot,
          stdio: ['ignore', 'pipe', 'pipe']
        });
        this.log(`Process spawned with PID: ${childProcess.pid}`);
      } catch (error) {
        this.logError('Failed to spawn Guard Rail CLI process', error as Error);
        reject(new Error(
          `Failed to spawn Guard Rail CLI process: ${error instanceof Error ? error.message : 'Unknown error'}`
        ));
        return;
      }

      let stdout = '';
      let stderr = '';
      let isTimedOut = false;
      let isErrored = false;

      // Set up 30-second timeout
      const timeout = setTimeout(() => {
        isTimedOut = true;
        this.logError(`Process timed out after 30 seconds (PID: ${childProcess.pid})`);

        // Try graceful termination first
        childProcess.kill('SIGTERM');

        // Force kill if process doesn't terminate within 2 seconds
        setTimeout(() => {
          if (!childProcess.killed) {
            this.log(`Force killing process (PID: ${childProcess.pid})`);
            childProcess.kill('SIGKILL');
          }
        }, 2000);

        reject(new Error(
          'Guard Rail CLI execution timed out after 30 seconds. ' +
          'The schema file may be too large or complex to validate.'
        ));
      }, 30000);

      // Collect stdout with streaming
      childProcess.stdout.on('data', (data: Buffer) => {
        stdout += data.toString();
      });

      // Collect stderr with streaming
      childProcess.stderr.on('data', (data: Buffer) => {
        stderr += data.toString();
      });

      // Handle process completion
      childProcess.on('close', (code: number | null) => {
        clearTimeout(timeout);
        this.log(`Process exited with code: ${code}`);

        // Don't process if already timed out or errored
        if (isTimedOut || isErrored) {
          return;
        }

        // Handle non-zero exit codes
        // Note: Exit code 1 means validation errors were found, which is expected
        // Only reject if exit code is not 0 or 1
        if (code !== 0 && code !== 1 && code !== null) {
          const errorMessage = stderr.trim() || 'Unknown error occurred';
          this.logError(`Process exited with non-zero code ${code}`, new Error(errorMessage));
          this.log(`stderr output: ${stderr}`);
          reject(new Error(
            `Guard Rail CLI exited with code ${code}. ` +
            `This may indicate a validation error or CLI issue.\n` +
            `Error output: ${errorMessage}`
          ));
          return;
        }

        // Handle null exit code (process was killed)
        if (code === null) {
          this.logError('Process was terminated unexpectedly');
          reject(new Error(
            'Guard Rail CLI process was terminated unexpectedly. ' +
            'This may be due to system resource constraints.'
          ));
          return;
        }

        // Parse JSON output
        // Note: The CLI outputs JSON to stderr when using --json flag
        try {
          let trimmedOutput = stdout.trim();
          
          // If stdout is empty, try stderr (CLI outputs JSON to stderr)
          if (!trimmedOutput) {
            this.log('stdout is empty, checking stderr for JSON output');
            trimmedOutput = stderr.trim();
          }
          
          this.log(`Received output (${trimmedOutput.length} characters)`);

          if (!trimmedOutput) {
            this.logError('CLI produced no output');
            reject(new Error(
              'Guard Rail CLI produced no output. ' +
              'Please ensure the guard-rail package is installed (pip install resource-schema-guard-rail).'
            ));
            return;
          }

          // Attempt to parse JSON
          let results: GuardRailResult[];
          try {
            // Try parsing as-is first
            results = JSON.parse(trimmedOutput) as GuardRailResult[];
            this.log('Successfully parsed JSON output');
          } catch (firstError) {
            // If that fails, try converting Python dict syntax to JSON
            // Replace single quotes with double quotes (but not inside strings)
            this.log('First parse failed, attempting Python dict conversion');
            try {
              const jsonified = trimmedOutput
                .replace(/'/g, '"')
                .replace(/True/g, 'true')
                .replace(/False/g, 'false')
                .replace(/None/g, 'null');
              
              results = JSON.parse(jsonified) as GuardRailResult[];
              this.log('Successfully parsed after Python dict conversion');
            } catch (secondError) {
              // Both parsing attempts failed
              const preview = trimmedOutput.substring(0, 200);
              const hasMore = trimmedOutput.length > 200 ? '...' : '';
              this.logError('Failed to parse JSON output after conversion', secondError as Error);
              this.log(`Output preview: ${preview}${hasMore}`);

              reject(new Error(
                `Failed to parse Guard Rail output as JSON. ` +
                `The CLI may have produced invalid output.\n` +
                `Parse error: ${secondError instanceof Error ? secondError.message : 'Unknown error'}\n` +
                `Output preview: ${preview}${hasMore}`
              ));
              return;
            }
          }

          // Validate the parsed structure
          if (!Array.isArray(results)) {
            this.logError('Output is not an array');
            reject(new Error(
              'Guard Rail output is not an array. ' +
              'The CLI may have produced unexpected output format.'
            ));
            return;
          }

          this.log(`Validation completed successfully with ${results.length} result(s)`);
          resolve(results);
        } catch (error) {
          this.logError('Unexpected error processing output', error as Error);
          reject(new Error(
            `Unexpected error processing Guard Rail output: ` +
            `${error instanceof Error ? error.message : 'Unknown error'}`
          ));
        }
      });

      // Handle process spawn errors (e.g., executable not found)
      childProcess.on('error', (error: Error) => {
        isErrored = true;
        clearTimeout(timeout);
        this.logError('Process error occurred', error);

        // Check for common error types
        if (error.message.includes('ENOENT')) {
          this.logError(`guard-rail command not found`);
          reject(new Error(
            `guard-rail command not found. ` +
            'Please install the resource-schema-guard-rail package: pip install resource-schema-guard-rail'
          ));
        } else if (error.message.includes('EACCES')) {
          this.logError(`Permission denied for guard-rail command`);
          reject(new Error(
            `Permission denied executing guard-rail. ` +
            'Please check file permissions.'
          ));
        } else {
          this.logError(`Failed to execute CLI: ${error.message}`);
          reject(new Error(
            `Failed to execute Guard Rail CLI: ${error.message}. ` +
            'This may be a system or permission issue.'
          ));
        }
      });
    });
  }
}
