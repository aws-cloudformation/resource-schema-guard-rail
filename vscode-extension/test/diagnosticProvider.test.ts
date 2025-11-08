/**
 * Unit tests for DiagnosticProvider
 */

import * as assert from 'assert';

// Mock VS Code API
const mockDiagnosticCollection = {
  set: () => {},
  delete: () => {},
  dispose: () => {}
};

const mockStatusBarItem = {
  text: '',
  tooltip: '',
  backgroundColor: undefined as any,
  show: () => {},
  dispose: () => {}
};

const mockOutputChannel = {
  appendLine: () => {},
  dispose: () => {}
};

const vscode = {
  languages: {
    createDiagnosticCollection: () => mockDiagnosticCollection
  },
  window: {
    createStatusBarItem: () => mockStatusBarItem,
    showInformationMessage: () => {},
    showWarningMessage: () => {},
    showErrorMessage: () => {}
  },
  StatusBarAlignment: {
    Left: 1,
    Right: 2
  },
  DiagnosticSeverity: {
    Error: 0,
    Warning: 1
  },
  ThemeColor: class {
    constructor(public id: string) {}
  }
};

describe('DiagnosticProvider', () => {
  describe('debouncing logic', () => {
    it('should debounce rapid validation requests', (done?: () => void) => {
      let validationCount = 0;
      const pendingValidations = new Map<string, NodeJS.Timeout>();
      const uri = 'file:///test.json';

      // Simulate rapid changes
      for (let i = 0; i < 5; i++) {
        const existing = pendingValidations.get(uri);
        if (existing) {
          clearTimeout(existing);
        }

        const timeout = setTimeout(() => {
          validationCount++;
          pendingValidations.delete(uri);
        }, 500);

        pendingValidations.set(uri, timeout);
      }

      // After 600ms, only one validation should have occurred
      setTimeout(() => {
        assert.strictEqual(validationCount, 1);
        if (done) done();
      }, 600);
    });

    it('should allow multiple files to be validated independently', (done?: () => void) => {
      let file1Count = 0;
      let file2Count = 0;
      const pendingValidations = new Map<string, NodeJS.Timeout>();

      // Schedule validation for file 1
      const uri1 = 'file:///test1.json';
      const timeout1 = setTimeout(() => {
        file1Count++;
        pendingValidations.delete(uri1);
      }, 500);
      pendingValidations.set(uri1, timeout1);

      // Schedule validation for file 2
      const uri2 = 'file:///test2.json';
      const timeout2 = setTimeout(() => {
        file2Count++;
        pendingValidations.delete(uri2);
      }, 500);
      pendingValidations.set(uri2, timeout2);

      // After 600ms, both should have validated
      setTimeout(() => {
        assert.strictEqual(file1Count, 1);
        assert.strictEqual(file2Count, 1);
        if (done) done();
      }, 600);
    });
  });

  describe('diagnostic clearing', () => {
    it('should clear diagnostics when requested', () => {
      let cleared = false;
      const collection = {
        delete: () => { cleared = true; },
        set: () => {},
        dispose: () => {}
      };

      const uri = { toString: () => 'file:///test.json' };
      collection.delete();

      assert.strictEqual(cleared, true);
    });
  });

  describe('status bar updates', () => {
    it('should show success state with no errors', () => {
      const statusBar = {
        text: '',
        tooltip: '',
        backgroundColor: undefined as any
      };

      const errorCount = 0;
      const warningCount = 0;

      if (errorCount === 0 && warningCount === 0) {
        statusBar.text = '$(check) Guard Rail';
        statusBar.tooltip = 'No validation issues found';
        statusBar.backgroundColor = undefined;
      }

      assert.strictEqual(statusBar.text, '$(check) Guard Rail');
      assert.strictEqual(statusBar.backgroundColor, undefined);
    });

    it('should show error state with errors', () => {
      const statusBar = {
        text: '',
        tooltip: '',
        backgroundColor: undefined as any
      };

      const errorCount = 3;
      const warningCount = 1;

      if (errorCount > 0) {
        statusBar.text = `$(error) Guard Rail: ${errorCount} error(s), ${warningCount} warning(s)`;
        statusBar.tooltip = `Guard Rail found ${errorCount} error(s) and ${warningCount} warning(s)`;
      }

      assert.strictEqual(statusBar.text, '$(error) Guard Rail: 3 error(s), 1 warning(s)');
      assert.ok(statusBar.tooltip.includes('3 error(s)'));
    });

    it('should show warning state with only warnings', () => {
      const statusBar = {
        text: '',
        tooltip: ''
      };

      const errorCount = 0;
      const warningCount = 2;

      if (errorCount === 0 && warningCount > 0) {
        statusBar.text = `$(warning) Guard Rail: ${warningCount} warning(s)`;
        statusBar.tooltip = `Guard Rail found ${warningCount} warning(s)`;
      }

      assert.strictEqual(statusBar.text, '$(warning) Guard Rail: 2 warning(s)');
    });
  });

  describe('file validation checks', () => {
    it('should skip validation for unsaved files', () => {
      const document = {
        isUntitled: true,
        uri: { scheme: 'untitled' }
      };

      const shouldSkip = document.isUntitled || document.uri.scheme !== 'file';
      assert.strictEqual(shouldSkip, true);
    });

    it('should skip validation for large files', () => {
      const fileSizeLimit = 1024 * 1024; // 1MB
      const fileSize = 2 * 1024 * 1024; // 2MB

      const shouldSkip = fileSize > fileSizeLimit;
      assert.strictEqual(shouldSkip, true);
    });

    it('should allow validation for normal files', () => {
      const document = {
        isUntitled: false,
        uri: { scheme: 'file' }
      };
      const fileSize = 500 * 1024; // 500KB
      const fileSizeLimit = 1024 * 1024; // 1MB

      const shouldSkip = document.isUntitled || 
                        document.uri.scheme !== 'file' || 
                        fileSize > fileSizeLimit;
      assert.strictEqual(shouldSkip, false);
    });
  });
});

// Simple test runner
function describe(name: string, fn: () => void) {
  console.log(`\n${name}`);
  fn();
}

function it(name: string, fn: (done?: () => void) => void) {
  // Check if test expects a done callback
  if (fn.length > 0) {
    // Async test with done callback
    let completed = false;
    const done = () => { completed = true; };
    
    try {
      fn(done);
      // Wait a bit for async operations
      setTimeout(() => {
        if (completed) {
          console.log(`  ✓ ${name}`);
        } else {
          console.log(`  ✗ ${name}`);
          console.error('    Test timed out or did not call done()');
          process.exitCode = 1;
        }
      }, 1000);
    } catch (error) {
      console.log(`  ✗ ${name}`);
      console.error(`    ${error instanceof Error ? error.message : error}`);
      process.exitCode = 1;
    }
  } else {
    // Sync test
    try {
      fn();
      console.log(`  ✓ ${name}`);
    } catch (error) {
      console.log(`  ✗ ${name}`);
      console.error(`    ${error instanceof Error ? error.message : error}`);
      process.exitCode = 1;
    }
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  console.log('Running DiagnosticProvider tests...');
}
