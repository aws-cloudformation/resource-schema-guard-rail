/**
 * Extension Entry Point
 * Activates the Guard Rail VS Code extension and sets up diagnostic provider
 */

import * as vscode from 'vscode';
import { GuardRailDiagnosticProvider } from './diagnosticProvider';
import { registerCommands } from './commands';

let diagnosticProvider: GuardRailDiagnosticProvider | undefined;
let outputChannel: vscode.OutputChannel | undefined;

/**
 * Extension activation entry point
 * Called when the extension is activated (when a JSON file is opened)
 */
export function activate(context: vscode.ExtensionContext) {
  // Create output channel for logging
  outputChannel = vscode.window.createOutputChannel('Resource Schema Guard Rail');
  outputChannel.appendLine('Resource Schema Guard Rail extension is now active');

  // Get workspace root
  const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  
  if (!workspaceRoot) {
    vscode.window.showErrorMessage(
      'Guard Rail requires a workspace to be opened. Please open a folder.'
    );
    return;
  }

  // Initialize diagnostic provider
  diagnosticProvider = new GuardRailDiagnosticProvider(workspaceRoot, outputChannel);

  // Register command handlers
  registerCommands(context, diagnosticProvider, outputChannel);

  // Set up document event listeners
  
  // onDidOpen: Validate when a document is opened
  context.subscriptions.push(
    vscode.workspace.onDidOpenTextDocument((document) => {
      if (document.languageId === 'json') {
        diagnosticProvider?.provideDiagnostics(document);
      }
    })
  );

  // onDidSave: Validate when a document is saved
  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument((document) => {
      if (document.languageId === 'json') {
        diagnosticProvider?.provideDiagnostics(document);
      }
    })
  );

  // onDidChange: Validate when a document changes (with debouncing)
  context.subscriptions.push(
    vscode.workspace.onDidChangeTextDocument((event) => {
      const document = event.document;
      if (document.languageId === 'json') {
        diagnosticProvider?.provideDiagnostics(document);
      }
    })
  );

  // onDidClose: Clear diagnostics when a document is closed
  context.subscriptions.push(
    vscode.workspace.onDidCloseTextDocument((document) => {
      if (document.languageId === 'json') {
        diagnosticProvider?.clearDiagnostics(document);
      }
    })
  );

  // Validate all currently open JSON documents
  vscode.workspace.textDocuments.forEach((document) => {
    if (document.languageId === 'json') {
      diagnosticProvider?.provideDiagnostics(document);
    }
  });

  outputChannel.appendLine('Guard Rail extension initialization complete');
}

/**
 * Extension deactivation entry point
 * Called when the extension is deactivated
 */
export function deactivate() {
  // Clean up diagnostic collection, status bar item, and cancel pending validations
  if (diagnosticProvider) {
    diagnosticProvider.dispose();
    diagnosticProvider = undefined;
  }

  // Dispose output channel
  if (outputChannel) {
    outputChannel.dispose();
    outputChannel = undefined;
  }
}
