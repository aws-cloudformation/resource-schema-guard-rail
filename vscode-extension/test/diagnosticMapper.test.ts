/**
 * Unit tests for DiagnosticMapper
 */

import * as assert from 'assert';
import { GuardRailResult } from '../src/types';

// Mock VS Code module before importing DiagnosticMapper
const vscode = {
  DiagnosticSeverity: {
    Error: 0,
    Warning: 1,
    Information: 2,
    Hint: 3
  },
  Range: class {
    constructor(public start: any, public end: any) {}
  },
  Position: class {
    constructor(public line: number, public character: number) {}
  },
  Diagnostic: class {
    constructor(public range: any, public message: string, public severity: number) {}
    source?: string;
    code?: string;
  }
};

// Mock the vscode module
(require as any).cache = (require as any).cache || {};
(require as any).extensions['.js'] = (require as any).extensions['.js'] || function() {};

// Create a mock module for vscode
const Module = require('module');
const originalRequire = Module.prototype.require;
Module.prototype.require = function(id: string) {
  if (id === 'vscode') {
    return vscode;
  }
  return originalRequire.apply(this, arguments);
};

import { DiagnosticMapper } from '../src/diagnosticMapper';

// Mock document
class MockDocument {
  constructor(private content: string) {}
  
  getText(): string {
    return this.content;
  }
}

describe('DiagnosticMapper', () => {
  let mapper: DiagnosticMapper;

  beforeEach(() => {
    mapper = new DiagnosticMapper();
  });

  describe('extractLineNumber', () => {
    it('should return 0 for empty path', () => {
      const doc = new MockDocument('{"test": "value"}') as any;
      const lineNumber = mapper.extractLineNumber('', doc);
      assert.strictEqual(lineNumber, 0);
    });

    it('should find property at root level', () => {
      const content = '{\n  "properties": {\n    "Name": "test"\n  }\n}';
      const doc = new MockDocument(content) as any;
      const lineNumber = mapper.extractLineNumber('/properties', doc);
      assert.strictEqual(lineNumber, 1);
    });

    it('should find nested property', () => {
      const content = '{\n  "properties": {\n    "Tags": {\n      "type": "array"\n    }\n  }\n}';
      const doc = new MockDocument(content) as any;
      const lineNumber = mapper.extractLineNumber('/properties/Tags', doc);
      assert.strictEqual(lineNumber, 2);
    });

    it('should handle array indices in path', () => {
      const content = '{\n  "handlers": {\n    "create": {\n      "permissions": []\n    }\n  }\n}';
      const doc = new MockDocument(content) as any;
      const lineNumber = mapper.extractLineNumber('/handlers/create/permissions[0]', doc);
      assert.strictEqual(lineNumber, 3);
    });

    it('should return 0 for non-existent property', () => {
      const doc = new MockDocument('{"test": "value"}') as any;
      const lineNumber = mapper.extractLineNumber('/nonexistent/property', doc);
      assert.strictEqual(lineNumber, 0);
    });
  });

  describe('createDiagnostic', () => {
    it('should create error diagnostic with correct properties', () => {
      const result = {
        check_id: 'TEST001',
        message: 'Test error message',
        path: '/properties/Test'
      };
      
      const diagnostic = mapper.createDiagnostic(
        'TestRule',
        result,
        5,
        vscode.DiagnosticSeverity.Error
      ) as any;

      assert.strictEqual(diagnostic.message, '[TestRule] Test error message');
      assert.strictEqual(diagnostic.severity, vscode.DiagnosticSeverity.Error);
      assert.strictEqual(diagnostic.source, 'guard-rail');
      assert.strictEqual(diagnostic.code, 'TEST001');
      assert.strictEqual(diagnostic.range.start.line, 5);
    });

    it('should create warning diagnostic with correct severity', () => {
      const result = {
        check_id: 'WARN001',
        message: 'Test warning message',
        path: '/properties/Test'
      };
      
      const diagnostic = mapper.createDiagnostic(
        'WarningRule',
        result,
        10,
        vscode.DiagnosticSeverity.Warning
      ) as any;

      assert.strictEqual(diagnostic.severity, vscode.DiagnosticSeverity.Warning);
      assert.strictEqual(diagnostic.message, '[WarningRule] Test warning message');
    });
  });

  describe('mapResults', () => {
    it('should map non-compliant results to error diagnostics', () => {
      const results: GuardRailResult[] = [{
        compliant: [],
        non_compliant: {
          'TestRule': [{
            check_id: 'TEST001',
            message: 'Test error',
            path: '/properties'
          }]
        },
        warning: {},
        skipped: []
      }];

      const doc = new MockDocument('{\n  "properties": {}\n}') as any;
      const diagnostics = mapper.mapResults(results, doc);

      assert.strictEqual(diagnostics.length, 1);
      assert.strictEqual(diagnostics[0].severity, vscode.DiagnosticSeverity.Error);
    });

    it('should map warning results to warning diagnostics', () => {
      const results: GuardRailResult[] = [{
        compliant: [],
        non_compliant: {},
        warning: {
          'WarningRule': [{
            check_id: 'WARN001',
            message: 'Test warning',
            path: '/properties'
          }]
        },
        skipped: []
      }];

      const doc = new MockDocument('{\n  "properties": {}\n}') as any;
      const diagnostics = mapper.mapResults(results, doc);

      assert.strictEqual(diagnostics.length, 1);
      assert.strictEqual(diagnostics[0].severity, vscode.DiagnosticSeverity.Warning);
    });

    it('should handle multiple results', () => {
      const results: GuardRailResult[] = [{
        compliant: [],
        non_compliant: {
          'Rule1': [{
            check_id: 'ERR001',
            message: 'Error 1',
            path: '/properties'
          }],
          'Rule2': [{
            check_id: 'ERR002',
            message: 'Error 2',
            path: '/handlers'
          }]
        },
        warning: {},
        skipped: []
      }];

      const doc = new MockDocument('{\n  "properties": {},\n  "handlers": {}\n}') as any;
      const diagnostics = mapper.mapResults(results, doc);

      assert.strictEqual(diagnostics.length, 2);
    });

    it('should return empty array for compliant results', () => {
      const results: GuardRailResult[] = [{
        compliant: ['Rule1', 'Rule2'],
        non_compliant: {},
        warning: {},
        skipped: []
      }];

      const doc = new MockDocument('{"test": "value"}') as any;
      const diagnostics = mapper.mapResults(results, doc);

      assert.strictEqual(diagnostics.length, 0);
    });
  });
});

// Simple test runner
function describe(name: string, fn: () => void) {
  console.log(`\n${name}`);
  fn();
}

function beforeEach(fn: () => void) {
  // Store for execution before each test
  (global as any).__beforeEach = fn;
}

function it(name: string, fn: () => void) {
  try {
    if ((global as any).__beforeEach) {
      (global as any).__beforeEach();
    }
    fn();
    console.log(`  ✓ ${name}`);
  } catch (error) {
    console.log(`  ✗ ${name}`);
    console.error(`    ${error instanceof Error ? error.message : error}`);
    process.exitCode = 1;
  }
}

// Run tests if this file is executed directly
if (require.main === module) {
  console.log('Running DiagnosticMapper tests...');
}
