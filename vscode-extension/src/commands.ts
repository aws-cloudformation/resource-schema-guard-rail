/**
 * Command Handlers
 * Registers and implements VS Code commands for Guard Rail
 */

import * as vscode from 'vscode';
import { GuardRailDiagnosticProvider } from './diagnosticProvider';

/**
 * Registers all Guard Rail commands
 * @param context The extension context
 * @param provider The diagnostic provider instance
 * @param outputChannel The output channel for logging
 */
export function registerCommands(
  context: vscode.ExtensionContext,
  provider: GuardRailDiagnosticProvider,
  outputChannel: vscode.OutputChannel
): void {
  outputChannel.appendLine('[Commands] Registering commands');
  
  // Register "guard-rail.validateSchema" command
  const validateCommand = vscode.commands.registerCommand(
    'guard-rail.validateSchema',
    async () => {
      outputChannel.appendLine('[Commands] Validate Schema command triggered');
      
      // Get the active text editor window
      const editor = vscode.window.activeTextEditor;

      // Check if there's an active editor window
      if (!editor) {
        outputChannel.appendLine('[Commands] No active editor found');
        vscode.window.showInformationMessage(
          'No active editor found. Please open a JSON schema file.'
        );
        return;
      }

      const document = editor.document;
      outputChannel.appendLine(`[Commands] Active document: ${document.uri.toString()}, language: ${document.languageId}`);

      // Check if the active file is a JSON file
      if (document.languageId !== 'json') {
        outputChannel.appendLine('[Commands] Active file is not JSON');
        vscode.window.showInformationMessage(
          'The active file is not a JSON file. Guard Rail validates JSON schema files.'
        );
        return;
      }

      // Trigger manual validation via diagnostic provider
      outputChannel.appendLine('[Commands] Triggering manual validation');
      await provider.provideDiagnostics(document);
    }
  );

  // Add command to subscriptions for cleanup
  context.subscriptions.push(validateCommand);
  outputChannel.appendLine('[Commands] Commands registered successfully');
}
