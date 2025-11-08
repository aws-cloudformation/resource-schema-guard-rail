/**
 * Diagnostic Mapper
 * Converts Guard Rail validation results to VS Code diagnostics
 */

import * as vscode from 'vscode';
import { GuardRailResult, GuardRuleResult } from './types';

/**
 * Maps Guard Rail validation results to VS Code diagnostics
 */
export class DiagnosticMapper {
  private outputChannel: any; // vscode.OutputChannel

  constructor(outputChannel?: any) {
    this.outputChannel = outputChannel;
  }

  /**
   * Logs a message to the output channel if available
   */
  private log(message: string): void {
    if (this.outputChannel) {
      this.outputChannel.appendLine(`[DiagnosticMapper] ${message}`);
    }
  }

  /**
   * Converts an array of GuardRailResult to VS Code Diagnostic objects
   * @param results Array of validation results from Guard Rail CLI
   * @param document The text document being validated
   * @returns Array of VS Code diagnostics
   */
  mapResults(results: GuardRailResult[], document: vscode.TextDocument): vscode.Diagnostic[] {
    this.log(`Mapping ${results.length} result(s) to diagnostics`);
    const diagnostics: vscode.Diagnostic[] = [];

    for (const result of results) {
      // Process non-compliant rules (errors)
      const nonCompliantCount = Object.keys(result.non_compliant).length;
      if (nonCompliantCount > 0) {
        this.log(`Processing ${nonCompliantCount} non-compliant rule(s)`);
      }
      
      for (const [ruleName, ruleResults] of Object.entries(result.non_compliant)) {
        for (const ruleResult of ruleResults) {
          const lineNumber = this.extractLineNumber(ruleResult.path, document);
          this.log(`  Error: ${ruleName} at line ${lineNumber + 1} (path: ${ruleResult.path})`);
          const diagnostic = this.createDiagnostic(
            ruleName,
            ruleResult,
            lineNumber,
            vscode.DiagnosticSeverity.Error
          );
          diagnostics.push(diagnostic);
        }
      }

      // Process warning rules (warnings)
      const warningCount = Object.keys(result.warning).length;
      if (warningCount > 0) {
        this.log(`Processing ${warningCount} warning rule(s)`);
      }
      
      for (const [ruleName, ruleResults] of Object.entries(result.warning)) {
        for (const ruleResult of ruleResults) {
          const lineNumber = this.extractLineNumber(ruleResult.path, document);
          this.log(`  Warning: ${ruleName} at line ${lineNumber + 1} (path: ${ruleResult.path})`);
          const diagnostic = this.createDiagnostic(
            ruleName,
            ruleResult,
            lineNumber,
            vscode.DiagnosticSeverity.Warning
          );
          diagnostics.push(diagnostic);
        }
      }
    }

    this.log(`Created ${diagnostics.length} diagnostic(s)`);
    return diagnostics;
  }

  /**
   * Extracts line number from a JSON path by searching the document
   * @param path JSON path string (e.g., "/properties/Tags" or "/handlers/create/permissions[0]")
   * @param document The text document to search
   * @returns Line number (0-indexed) where the property is found, or 0 if not found
   */
  extractLineNumber(path: string, document: vscode.TextDocument): number {
    // Handle empty paths - default to line 0 (schema-level issues)
    if (!path || path.trim() === '') {
      return 0;
    }

    // Remove leading slash and split into path segments
    const normalizedPath = path.startsWith('/') ? path.substring(1) : path;
    
    if (!normalizedPath) {
      return 0;
    }

    // Split path into segments, handling array indices
    // Example: "properties/Tags" or "handlers/create/permissions[0]"
    const segments = normalizedPath.split('/');
    
    if (segments.length === 0) {
      return 0;
    }

    // Get the last segment as the property to search for
    // Remove array indices like [0] from the segment
    let lastSegment = segments[segments.length - 1];
    lastSegment = lastSegment.replace(/\[\d+\]$/, '');

    if (!lastSegment) {
      return 0;
    }

    // Search for the property in the document
    // Look for patterns like: "propertyName": or "propertyName" :
    const documentText = document.getText();
    const lines = documentText.split('\n');

    // Try to find the property with quotes
    const quotedPattern = new RegExp(`"${this.escapeRegex(lastSegment)}"\\s*:`);
    
    for (let i = 0; i < lines.length; i++) {
      if (quotedPattern.test(lines[i])) {
        return i;
      }
    }

    // If not found with the last segment, try searching for intermediate segments
    // This helps with nested paths
    for (let segmentIndex = segments.length - 1; segmentIndex >= 0; segmentIndex--) {
      let segment = segments[segmentIndex];
      segment = segment.replace(/\[\d+\]$/, '');
      
      if (!segment) {
        continue;
      }

      const pattern = new RegExp(`"${this.escapeRegex(segment)}"\\s*:`);
      
      for (let i = 0; i < lines.length; i++) {
        if (pattern.test(lines[i])) {
          return i;
        }
      }
    }

    // Fallback to line 0 if property not found
    return 0;
  }

  /**
   * Creates a VS Code Diagnostic object from a guard rule result
   * @param ruleName Name of the rule that triggered
   * @param result The guard rule result details
   * @param lineNumber Line number where the issue occurs (0-indexed)
   * @param severity Diagnostic severity level
   * @returns VS Code Diagnostic object
   */
  createDiagnostic(
    ruleName: string,
    result: GuardRuleResult,
    lineNumber: number,
    severity: vscode.DiagnosticSeverity
  ): vscode.Diagnostic {
    // Create range for the diagnostic
    // Start at the beginning of the line, extend to end of line
    const line = Math.max(0, lineNumber);
    const range = new vscode.Range(
      new vscode.Position(line, 0),
      new vscode.Position(line, Number.MAX_SAFE_INTEGER)
    );

    // Format the diagnostic message
    // Include rule name and the detailed message
    const message = `(${result.check_id}) ${result.message}`;

    // Create the diagnostic
    const diagnostic = new vscode.Diagnostic(
      range,
      message,
      severity
    );

    // Set the source to identify this as a Guard Rail diagnostic
    diagnostic.source = 'guard-rail';

    // Include the check_id as the diagnostic code for reference
    diagnostic.code = ruleName;

    return diagnostic;
  }

  /**
   * Escapes special regex characters in a string
   * @param str String to escape
   * @returns Escaped string safe for use in RegExp
   */
  private escapeRegex(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }
}
