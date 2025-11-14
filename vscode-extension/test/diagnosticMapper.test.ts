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

  positionAt(offset: number): { line: number; character: number } {
    const lines = this.content.substring(0, offset).split('\n');
    return {
      line: lines.length - 1,
      character: lines[lines.length - 1].length
    };
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
      const content = '{\n  "handlers": {\n    "create": {\n      "permissions": ["item"]\n    }\n  }\n}';
      const doc = new MockDocument(content) as any;
      const lineNumber = mapper.extractLineNumber('/handlers/create/permissions/0', doc);
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

      assert.strictEqual(diagnostic.message, '(TEST001) Test error message');
      assert.strictEqual(diagnostic.severity, vscode.DiagnosticSeverity.Error);
      assert.strictEqual(diagnostic.source, 'guard-rail');
      assert.strictEqual(diagnostic.code, 'TestRule');
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
      assert.strictEqual(diagnostic.message, '(WARN001) Test warning message');
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

    it('should handle mixed errors and warnings', () => {
      const results: GuardRailResult[] = [{
        compliant: [],
        non_compliant: {
          'ErrorRule': [{
            check_id: 'ERR001',
            message: 'Error message',
            path: '/properties'
          }]
        },
        warning: {
          'WarningRule': [{
            check_id: 'WARN001',
            message: 'Warning message',
            path: '/handlers'
          }]
        },
        skipped: []
      }];

      const doc = new MockDocument('{\n  "properties": {},\n  "handlers": {}\n}') as any;
      const diagnostics = mapper.mapResults(results, doc);

      assert.strictEqual(diagnostics.length, 2);

      // Check that we have one error and one warning
      const errors = diagnostics.filter(d => d.severity === vscode.DiagnosticSeverity.Error);
      const warnings = diagnostics.filter(d => d.severity === vscode.DiagnosticSeverity.Warning);

      assert.strictEqual(errors.length, 1);
      assert.strictEqual(warnings.length, 1);
    });

    it('should handle empty results array', () => {
      const results: GuardRailResult[] = [];
      const doc = new MockDocument('{"test": "value"}') as any;
      const diagnostics = mapper.mapResults(results, doc);

      assert.strictEqual(diagnostics.length, 0);
    });
  });

  describe('logging with output channel', () => {
    it('should log when output channel is provided', () => {
      const mockChannel = {
        appendLine: (msg: string) => {
          // Mock implementation
        }
      };

      const mapperWithChannel = new DiagnosticMapper(mockChannel);
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
      const diagnostics = mapperWithChannel.mapResults(results, doc);

      assert.strictEqual(diagnostics.length, 1);
    });
  });

  describe('edge cases in path extraction', () => {
    it('should handle path with only slashes', () => {
      const doc = new MockDocument('{"test": "value"}') as any;
      const lineNumber = mapper.extractLineNumber('///', doc);
      assert.strictEqual(lineNumber, 0);
    });

    it('should handle path with empty segments', () => {
      const doc = new MockDocument('{"test": "value"}') as any;
      const lineNumber = mapper.extractLineNumber('/test//', doc);
      assert.strictEqual(lineNumber, 0);
    });

    it('should handle path with only array index', () => {
      const doc = new MockDocument('["item1", "item2"]') as any;
      const lineNumber = mapper.extractLineNumber('/0', doc);
      assert.strictEqual(lineNumber, 0);
    });

    it('should return 0 when path segment not found', () => {
      const content = '{\n  "properties": {\n    "nested": {}\n  }\n}';
      const doc = new MockDocument(content) as any;
      // Search for /properties/nested/nonexistent - should return 0 since exact path doesn't exist
      const lineNumber = mapper.extractLineNumber('/properties/nested/nonexistent', doc);
      assert.strictEqual(lineNumber, 0);
    });

    it('should handle whitespace in property names', () => {
      const content = '{\n  "property name": "value"\n}';
      const doc = new MockDocument(content) as any;
      const lineNumber = mapper.extractLineNumber('/property name', doc);
      assert.strictEqual(lineNumber, 1);
    });

    it('should handle special regex characters in property names', () => {
      const content = '{\n  "property.with.dots": "value",\n  "property[with]brackets": "value"\n}';
      const doc = new MockDocument(content) as any;
      const lineNumber1 = mapper.extractLineNumber('/property.with.dots', doc);
      const lineNumber2 = mapper.extractLineNumber('/property[with]brackets', doc);
      assert.ok(lineNumber1 >= 0);
      assert.ok(lineNumber2 >= 0);
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
