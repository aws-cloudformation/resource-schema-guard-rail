/**
 * Diagnostic Provider
 * Manages validation lifecycle and diagnostic display for Guard Rail
 */

import * as vscode from 'vscode';
import { GuardRailExecutor } from './guardRailExecutor';
import { DiagnosticMapper } from './diagnosticMapper';

/**
 * Provides diagnostic integration for Guard Rail validation
 */
export class GuardRailDiagnosticProvider {
  private diagnosticCollection: vscode.DiagnosticCollection;
  private executor: GuardRailExecutor;
  private mapper: DiagnosticMapper;
  private pendingValidations: Map<string, NodeJS.Timeout>;
  private statusBarItem: vscode.StatusBarItem;
  private outputChannel: vscode.OutputChannel;
  private errorDecorationType: vscode.TextEditorDecorationType;
  private warningDecorationType: vscode.TextEditorDecorationType;

  constructor(workspaceRoot: string, outputChannel: vscode.OutputChannel) {
    // vscode is a global singleton interface. We need to create a collection
    // once validation results are set it gets propagated to VSCode UI through this global collection
    this.diagnosticCollection = vscode.languages.createDiagnosticCollection('guard-rail');
    this.executor = new GuardRailExecutor(workspaceRoot, outputChannel);
    this.mapper = new DiagnosticMapper(outputChannel);
    this.pendingValidations = new Map();

    // Create decoration types for line highlighting
    // Lines are highlighted by VSCode itself (built in coloring red/orange/yellow)
    // This decorations highlight background color of the line
    this.errorDecorationType = vscode.window.createTextEditorDecorationType({
      backgroundColor: 'rgba(255, 0, 0, 0.1)',
      isWholeLine: true,
      overviewRulerColor: 'red',
      overviewRulerLane: vscode.OverviewRulerLane.Left
    });

    this.warningDecorationType = vscode.window.createTextEditorDecorationType({
      backgroundColor: 'rgba(173, 216, 230, 0.3)',
      isWholeLine: true,
      overviewRulerColor: 'lightblue',
      overviewRulerLane: vscode.OverviewRulerLane.Left,
      border: '1px solid rgba(173, 216, 230, 0.6)'
    });

    // Create status bar item
    this.statusBarItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Left,
      100
    );
    this.statusBarItem.text = '$(check) Guard Rail';
    this.statusBarItem.tooltip = 'Guard Rail validation status';
    this.statusBarItem.show();

    this.outputChannel = outputChannel;
    this.outputChannel.appendLine('[DiagnosticProvider] Initialized');
  }

  /**
   * Validates a document and updates diagnostics
   * @param document The document to validate
   */
  async provideDiagnostics(document: vscode.TextDocument): Promise<void> {
    const uri = document.uri.toString();
    this.outputChannel.appendLine(`[DiagnosticProvider] Validation requested for: ${uri}`);

    // Skip validation for unsaved files
    if (document.isUntitled || document.uri.scheme !== 'file') {
      this.outputChannel.appendLine(`[DiagnosticProvider] Skipping validation for unsaved file: ${uri}`);
      vscode.window.showInformationMessage(
        'Save the file to run Guard Rail validation.'
      );
      return;
    }

    // Skip validation for files larger than 1GB
    const fileSizeLimit = 1024 * 1024 * 1024; // 1GB in bytes
    const fileSize = Buffer.byteLength(document.getText(), 'utf8');
    if (fileSize > fileSizeLimit) {
      this.outputChannel.appendLine(
        `[DiagnosticProvider] Skipping validation for large file (${(fileSize / 1024 / 1024 / 1024).toFixed(2)}GB): ${uri}`
      );
      vscode.window.showWarningMessage(
        'File too large for Guard Rail validation (>1GB).'
      );
      return;
    }

    // Clear existing timeout for this file
    const existingTimeout = this.pendingValidations.get(uri);
    if (existingTimeout) {
      this.outputChannel.appendLine(`[DiagnosticProvider] Clearing existing timeout for: ${uri}`);
      clearTimeout(existingTimeout);
    }

    // Set up debounced validation (500ms)
    this.outputChannel.appendLine(`[DiagnosticProvider] Scheduling validation with 500ms debounce for: ${uri}`);
    const timeout = setTimeout(async () => {
      this.pendingValidations.delete(uri);
      await this.executeValidation(document);
    }, 500);

    this.pendingValidations.set(uri, timeout);
  }

  /**
   * Executes validation on a document
   * @param document The document to validate
   */
  private async executeValidation(document: vscode.TextDocument): Promise<void> {
    const filePath = document.uri.fsPath;

    try {
      this.outputChannel.appendLine(`[DiagnosticProvider] Starting validation for: ${filePath}`);

      // Clear existing diagnostics before validation
      this.clearDiagnostics(document);

      // Execute Guard Rail CLI
      const results = await this.executor.execute(filePath);

      this.outputChannel.appendLine(`[DiagnosticProvider] Validation completed for: ${filePath}`);

      // Map results to diagnostics
      const diagnostics = this.mapper.mapResults(results, document);

      // Update diagnostic collection
      this.diagnosticCollection.set(document.uri, diagnostics);

      // Apply line highlighting decorations
      this.applyDecorations(document, diagnostics);

      // Count errors and warnings
      let errorCount = 0;
      let warningCount = 0;

      for (const diagnostic of diagnostics) {
        if (diagnostic.severity === vscode.DiagnosticSeverity.Error) {
          errorCount++;
        } else if (diagnostic.severity === vscode.DiagnosticSeverity.Warning) {
          warningCount++;
        }
      }

      // Update status bar
      this.updateStatusBar(errorCount, warningCount);

      this.outputChannel.appendLine(
        `[DiagnosticProvider] Found ${errorCount} error(s) and ${warningCount} warning(s)`
      );
    } catch (error) {
      this.outputChannel.appendLine(
        `[DiagnosticProvider] ERROR: Validation failed for ${filePath}: ${error instanceof Error ? error.message : 'Unknown error'}`
      );

      // Show error notification to user
      vscode.window.showErrorMessage(
        `Guard Rail validation failed: ${error instanceof Error ? error.message : 'Unknown error'}`
      );
    }
  }

  /**
   * Clears diagnostics for a document
   * @param document The document to clear diagnostics for
   */
  clearDiagnostics(document: vscode.TextDocument): void {
    this.outputChannel.appendLine(`[DiagnosticProvider] Clearing diagnostics for: ${document.uri.toString()}`);
    this.diagnosticCollection.delete(document.uri);

    // Clear decorations
    const editor = vscode.window.visibleTextEditors.find(
      e => e.document.uri.toString() === document.uri.toString()
    );
    if (editor) {
      editor.setDecorations(this.errorDecorationType, []);
      editor.setDecorations(this.warningDecorationType, []);
    }
  }

  /**
   * Applies line highlighting decorations based on diagnostics
   * @param document The document to apply decorations to
   * @param diagnostics The diagnostics to visualize
   */
  private applyDecorations(document: vscode.TextDocument, diagnostics: vscode.Diagnostic[]): void {
    // this will find the editor window that displays the document we want to decorate
    const editor = vscode.window.visibleTextEditors.find(
      e => e.document.uri.toString() === document.uri.toString()
    );

    if (!editor) {
      this.outputChannel.appendLine('[DiagnosticProvider] No visible editor found for decorations');
      return;
    }

    const errorRanges: vscode.Range[] = [];
    const warningRanges: vscode.Range[] = [];

    diagnostics.forEach(diagnostic => {
      if (diagnostic.severity === vscode.DiagnosticSeverity.Error) {
        errorRanges.push(diagnostic.range);
      } else if (diagnostic.severity === vscode.DiagnosticSeverity.Warning) {
        warningRanges.push(diagnostic.range);
      }
    });

    editor.setDecorations(this.errorDecorationType, errorRanges);
    editor.setDecorations(this.warningDecorationType, warningRanges);

    this.outputChannel.appendLine(
      `[DiagnosticProvider] Applied decorations: ${errorRanges.length} errors, ${warningRanges.length} warnings`
    );
  }

  /**
   * Updates the status bar with error and warning counts
   * @param errorCount Number of errors
   * @param warningCount Number of warnings
   */
  updateStatusBar(errorCount: number, warningCount: number): void {
    this.outputChannel.appendLine(`[DiagnosticProvider] Updating status bar: ${errorCount} error(s), ${warningCount} warning(s)`);

    // Adds necessary status bar indicators
    if (errorCount === 0 && warningCount === 0) {
      this.statusBarItem.text = '$(check) Guard Rail';
      this.statusBarItem.tooltip = 'No validation issues found';
      this.statusBarItem.color = '#00ff00'; // Green text
      this.statusBarItem.backgroundColor = undefined;
    } else if (errorCount > 0) {
      this.statusBarItem.text = `$(error) Guard Rail: ${errorCount} error(s), ${warningCount} warning(s)`;
      this.statusBarItem.tooltip = `Guard Rail found ${errorCount} error(s) and ${warningCount} warning(s)`;
      this.statusBarItem.color = undefined; // Reset to default
      this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
    } else {
      this.statusBarItem.text = `$(warning) Guard Rail: ${warningCount} warning(s)`;
      this.statusBarItem.tooltip = `Guard Rail found ${warningCount} warning(s)`;
      this.statusBarItem.color = undefined; // Reset to default
      this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
    }
  }

  /**
   * Disposes of resources
   */
  dispose(): void {
    this.outputChannel.appendLine('[DiagnosticProvider] Disposing resources');

    // Clear all pending validations
    const pendingCount = this.pendingValidations.size;
    if (pendingCount > 0) {
      this.outputChannel.appendLine(`[DiagnosticProvider] Clearing ${pendingCount} pending validation(s)`);
    }

    for (const timeout of this.pendingValidations.values()) {
      clearTimeout(timeout);
    }
    this.pendingValidations.clear();

    // Dispose of diagnostic collection
    this.diagnosticCollection.dispose();

    // Dispose of status bar item
    this.statusBarItem.dispose();

    this.outputChannel.appendLine('[DiagnosticProvider] Disposed');
  }
}
