/**
 * Diagnostic Mapper
 * Converts Guard Rail validation results to VS Code diagnostics
 * Imports: need to import json-parser to provide better highlihgting accuracy
 */

import * as vscode from 'vscode';
import * as jsonc from 'jsonc-parser';
import { GuardRailResult, GuardRuleResult } from './types';

/**
 * Maps Guard Rail validation results to VS Code diagnostics
 */
export class DiagnosticMapper {
  private outputChannel: any; // vscode.OutputChannel

  constructor(outputChannel?: any) {
    this.outputChannel = outputChannel;
  }


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
      this.processRuleResults(
        result.non_compliant,
        document,
        diagnostics,
        vscode.DiagnosticSeverity.Error,
        'non-compliant',
        'Error'
      );

      // Process warning rules (warnings)
      this.processRuleResults(
        result.warning,
        document,
        diagnostics,
        vscode.DiagnosticSeverity.Warning,
        'warning',
        'Warning'
      );
    }

    this.log(`Created ${diagnostics.length} diagnostic(s)`);
    return diagnostics;
  }

  /**
   * Processes rule results and adds diagnostics to the array
   * @param rules Object containing rule results
   * @param document The text document being validated
   * @param diagnostics Array to add diagnostics to
   * @param severity Diagnostic severity level
   * @param resultType Type of result (e.g., 'non-compliant', 'warning')
   * @param logLabel Label for logging (e.g., 'Error', 'Warning')
   */
  private processRuleResults(
    rules: Record<string, GuardRuleResult[]>,
    document: vscode.TextDocument,
    diagnostics: vscode.Diagnostic[],
    severity: vscode.DiagnosticSeverity,
    resultType: string,
    logLabel: string
  ): void {
    const ruleCount = Object.keys(rules).length;
    if (ruleCount > 0) {
      this.log(`Processing ${ruleCount} ${resultType} rule(s)`);
    }

    for (const [ruleName, ruleResults] of Object.entries(rules)) {
      for (const ruleResult of ruleResults) {
        const lineNumber = this.extractLineNumber(ruleResult.path, document);
        this.log(`  ${logLabel}: ${ruleName} at line ${lineNumber + 1} (path: ${ruleResult.path})`);
        const diagnostic = this.createDiagnostic(
          ruleName,
          ruleResult,
          lineNumber,
          severity
        );
        diagnostics.push(diagnostic);
      }
    }
  }

  /**
   * Extracts line number from a JSON path using proper JSON parsing with $ref resolution
   * @param path JSON path string (e.g., "/properties/Tags" or "/properties/StageDescription/Tags")
   * @param document The text document to search
   * @returns Line number (0-indexed) where the property is found, or 0 if not found
   */
  extractLineNumber(path: string, document: vscode.TextDocument): number {
    if (!path?.trim()) {
      return 0;
    }

    const text = document.getText();
    // Remove leading slash and split into segments, converting numeric strings to numbers
    const pathSegments: (string | number)[] = path
      .replace(/^\//, '')
      .split('/')
      .filter((segment) => segment !== '')
      .map((segment) => {
        const numericValue = parseInt(segment, 10);
        return !isNaN(numericValue) && segment === numericValue.toString()
          ? numericValue
          : segment;
      });

    if (pathSegments.length === 0) {
      return 0;
    }

    try {
      // need to parse document as json as we can do more precise traversal
      // path gives us segments to retrieve
      // jsonc lets us get line numbers from a document
      const rootDocument = jsonc.parseTree(text);

      if (!rootDocument) {
        this.log('Failed to parse JSON document');
        return 0;
      }

      // Navigate through path, resolving $refs as we encounter them
      const node = this.findSubschema(rootDocument, pathSegments);

      if (node) {
        const position = document.positionAt(node.offset);
        this.log(`Found path "${path}" at line ${position.line + 1}`);
        return position.line;
      }

      this.log(`Path "${path}" not found in document`);
    } catch (error) {
      this.log(`Error parsing JSON: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }

    return 0;
  }

  /**
   * Navigates through path segments, resolving $ref references as encountered
   * @param root The parsed JSON tree root
   * @param pathSegments Array of path segments to navigate
   * @returns The final node if found, null otherwise
   */
  private findSubschema(
    root: jsonc.Node,
    pathSegments: (string | number)[]
  ): jsonc.Node | null {
    let currentNode: jsonc.Node | undefined = root;
    const currentPath: (string | number)[] = [];

    for (const segment of pathSegments) {
      currentPath.push(segment);

      // Try to find the next node directly
      currentNode = jsonc.findNodeAtLocation(currentNode, [segment]);
      if (!currentNode) return null;

      // Check if this node has a $ref and if so grab subschema and return its definition
      const refNode = jsonc.findNodeAtLocation(currentNode, ['$ref']);
      if (refNode?.value) {
        const refValue = refNode.value as string;

        // Handle internal references like "#/definitions/Description"
        if (refValue.startsWith('#/')) {
          const refPath = refValue.substring(2);
          const refSegments = refPath.split('/');

          this.log(`Resolving $ref at ${currentPath.join('/')}: ${refValue}`);

          // Resolve the reference - this gives us the schema definition
          const refTarget = jsonc.findNodeAtLocation(root, refSegments);
          if (!refTarget) return null;

          // If the ref target is a schema object with properties, navigate into properties
          // This handles cases like {"type": "object", "properties": {...}}
          const propertiesNode = jsonc.findNodeAtLocation(refTarget, ['properties']);
          currentNode = propertiesNode || refTarget;
        }
      }
    }

    return currentNode || null;
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
    const diagnostic = new vscode.Diagnostic(range, message, severity);

    // Set the source to identify this as a Guard Rail diagnostic
    diagnostic.source = 'guard-rail';

    // Include the check_id as the diagnostic code for reference
    diagnostic.code = ruleName;

    return diagnostic;
  }
}
