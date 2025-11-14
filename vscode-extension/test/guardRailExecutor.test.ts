/**
 * Unit tests for GuardRailExecutor
 */

import * as assert from 'assert';
import * as path from 'path';
import { EventEmitter } from 'events';

// Mock child process BEFORE importing GuardRailExecutor
class MockChildProcess extends EventEmitter {
  public pid = 12345;
  public killed = false;
  public stdout = new EventEmitter();
  public stderr = new EventEmitter();

  kill(_signal?: string): boolean {
    this.killed = true;
    this.emit('close', null);
    return true;
  }
}

// Store the original child_process module
const childProcessModule = require('child_process');
const originalSpawn = childProcessModule.spawn;
let mockSpawnFn: any = null;

// Override spawn globally
childProcessModule.spawn = function(...args: any[]) {
  if (mockSpawnFn) {
    return mockSpawnFn(...args);
  }
  return originalSpawn.apply(this, args);
};

// NOW import GuardRailExecutor after mocking is set up
import { GuardRailExecutor } from '../src/guardRailExecutor';

// Mock output channel for testing
class MockOutputChannel {
  public messages: string[] = [];

  appendLine(message: string): void {
    this.messages.push(message);
  }

  clear(): void {
    this.messages = [];
  }

  getLastMessage(): string | undefined {
    return this.messages[this.messages.length - 1];
  }

  hasMessage(substring: string): boolean {
    return this.messages.some(msg => msg.includes(substring));
  }
}

describe('GuardRailExecutor', () => {
  let executor: GuardRailExecutor;
  let mockOutputChannel: MockOutputChannel;
  const workspaceRoot = path.join(__dirname, '..', '..');

  beforeEach(() => {
    mockOutputChannel = new MockOutputChannel();
    executor = new GuardRailExecutor(workspaceRoot, mockOutputChannel);
  });

  afterEach(() => {
    // Reset mock after each test
    mockSpawnFn = null;
  });

  describe('constructor', () => {
    it('should create executor instance', () => {
      assert.ok(executor);
      assert.ok(executor instanceof GuardRailExecutor);
    });

    it('should create executor without output channel', () => {
      const executorWithoutChannel = new GuardRailExecutor(workspaceRoot);
      assert.ok(executorWithoutChannel);
      assert.ok(executorWithoutChannel instanceof GuardRailExecutor);
    });

    it('should store workspace root', () => {
      // Verify by checking that execute uses the workspace root
      assert.ok(executor);
    });
  });

  describe('logging', () => {
    it('should log messages when output channel is provided', async () => {
      const mockProcess = new MockChildProcess();
      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stdout.emit('data', Buffer.from(JSON.stringify([{
            compliant: [],
            non_compliant: {},
            warning: {},
            skipped: []
          }])));
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      await executor.execute('/test/schema.json');
      assert.ok(mockOutputChannel.messages.length > 0);
      assert.ok(mockOutputChannel.hasMessage('[GuardRailExecutor]'));
    });

    it('should log starting validation message', async () => {
      const schemaPath = '/test/schema.json';
      const mockProcess = new MockChildProcess();
      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stdout.emit('data', Buffer.from(JSON.stringify([{
            compliant: [],
            non_compliant: {},
            warning: {},
            skipped: []
          }])));
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      await executor.execute(schemaPath);
      assert.ok(mockOutputChannel.hasMessage('Starting validation for schema'));
      assert.ok(mockOutputChannel.hasMessage(schemaPath));
    });

    it('should log command execution details', async () => {
      const mockProcess = new MockChildProcess();
      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stdout.emit('data', Buffer.from(JSON.stringify([{
            compliant: [],
            non_compliant: {},
            warning: {},
            skipped: []
          }])));
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      await executor.execute('/test/schema.json');
      assert.ok(mockOutputChannel.hasMessage('Executing command'));
      assert.ok(mockOutputChannel.hasMessage('guard-rail'));
      assert.ok(mockOutputChannel.hasMessage('--json'));
    });

    it('should log working directory', async () => {
      const mockProcess = new MockChildProcess();
      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stdout.emit('data', Buffer.from(JSON.stringify([{
            compliant: [],
            non_compliant: {},
            warning: {},
            skipped: []
          }])));
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      await executor.execute('/test/schema.json');
      assert.ok(mockOutputChannel.hasMessage('Working directory'));
    });

    it('should log process PID when spawned', async () => {
      const mockProcess = new MockChildProcess();
      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stdout.emit('data', Buffer.from(JSON.stringify([{
            compliant: [],
            non_compliant: {},
            warning: {},
            skipped: []
          }])));
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      await executor.execute('/test/schema.json');
      assert.ok(mockOutputChannel.hasMessage('PID'));
      assert.ok(mockOutputChannel.hasMessage('12345'));
    });
  });

  describe('execute', () => {
    it('should successfully parse valid JSON output', async () => {
      const mockProcess = new MockChildProcess();

      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stdout.emit('data', Buffer.from(JSON.stringify([{
            compliant: ['Rule1'],
            non_compliant: {},
            warning: {},
            skipped: []
          }])));
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      const results = await executor.execute('/test/schema.json');
      assert.ok(Array.isArray(results));
      assert.strictEqual(results.length, 1);
      assert.ok(results[0].compliant.includes('Rule1'));
    });

    it('should handle JSON output in stderr', async () => {
      const mockProcess = new MockChildProcess();

      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stderr.emit('data', Buffer.from(JSON.stringify([{
            compliant: [],
            non_compliant: {},
            warning: {},
            skipped: []
          }])));
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      const results = await executor.execute('/test/schema.json');
      assert.ok(Array.isArray(results));
    });

    it('should handle exit code 1 (validation errors)', async () => {
      const mockProcess = new MockChildProcess();

      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stdout.emit('data', Buffer.from(JSON.stringify([{
            compliant: [],
            non_compliant: {
              'TestRule': [{
                check_id: 'TEST001',
                message: 'Error',
                path: '/properties'
              }]
            },
            warning: {},
            skipped: []
          }])));
          mockProcess.emit('close', 1);
        }, 10);
        return mockProcess;
      };

      const results = await executor.execute('/test/schema.json');
      assert.ok(Array.isArray(results));
      assert.strictEqual(Object.keys(results[0].non_compliant).length, 1);
    });

    it('should handle Python dict format and convert to JSON', async () => {
      const mockProcess = new MockChildProcess();

      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stdout.emit('data', Buffer.from(
            "[{'compliant': [], 'non_compliant': {}, 'warning': {}, 'skipped': []}]"
          ));
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      const results = await executor.execute('/test/schema.json');
      assert.ok(Array.isArray(results));
    });

    it('should handle Python boolean values (True/False/None)', async () => {
      const mockProcess = new MockChildProcess();

      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stdout.emit('data', Buffer.from(
            '[{"compliant": [], "non_compliant": {}, "warning": {}, "skipped": [], "test": True, "other": False, "value": None}]'
          ));
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      const results = await executor.execute('/test/schema.json');
      assert.ok(Array.isArray(results));
    });

    it('should reject on non-zero exit code (not 0 or 1)', async () => {
      const mockProcess = new MockChildProcess();

      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stderr.emit('data', Buffer.from('Fatal error occurred'));
          mockProcess.emit('close', 2);
        }, 10);
        return mockProcess;
      };

      try {
        await executor.execute('/test/schema.json');
        assert.fail('Should have thrown an error');
      } catch (error) {
        assert.ok(error instanceof Error);
        assert.ok(error.message.includes('exited with code 2'));
      }
    });

    it('should reject when process is killed (null exit code)', async () => {
      const mockProcess = new MockChildProcess();

      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.emit('close', null);
        }, 10);
        return mockProcess;
      };

      try {
        await executor.execute('/test/schema.json');
        assert.fail('Should have thrown an error');
      } catch (error) {
        assert.ok(error instanceof Error);
        assert.ok(error.message.includes('terminated unexpectedly'));
      }
    });

    it('should reject when output is empty', async () => {
      const mockProcess = new MockChildProcess();

      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      try {
        await executor.execute('/test/schema.json');
        assert.fail('Should have thrown an error');
      } catch (error) {
        assert.ok(error instanceof Error);
        assert.ok(error.message.includes('no output'));
      }
    });

    it('should reject when output is not valid JSON', async () => {
      const mockProcess = new MockChildProcess();

      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stdout.emit('data', Buffer.from('This is not JSON'));
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      try {
        await executor.execute('/test/schema.json');
        assert.fail('Should have thrown an error');
      } catch (error) {
        assert.ok(error instanceof Error);
        assert.ok(error.message.includes('parse') || error.message.includes('JSON'));
      }
    });

    it('should reject when output is not an array', async () => {
      const mockProcess = new MockChildProcess();

      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stdout.emit('data', Buffer.from('{"not": "an array"}'));
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      try {
        await executor.execute('/test/schema.json');
        assert.fail('Should have thrown an error');
      } catch (error) {
        assert.ok(error instanceof Error);
        assert.ok(error.message.includes('not an array'));
      }
    });

    it('should handle ENOENT error (command not found)', async () => {
      mockSpawnFn = () => {
        const mockProcess = new MockChildProcess();
        setTimeout(() => {
          const error: any = new Error('spawn guard-rail ENOENT');
          error.message = 'spawn guard-rail ENOENT';
          mockProcess.emit('error', error);
        }, 10);
        return mockProcess;
      };

      try {
        await executor.execute('/test/schema.json');
        assert.fail('Should have thrown an error');
      } catch (error) {
        assert.ok(error instanceof Error);
        assert.ok(error.message.includes('not found'));
        assert.ok(error.message.includes('install'));
      }
    });

    it('should handle EACCES error (permission denied)', async () => {
      mockSpawnFn = () => {
        const mockProcess = new MockChildProcess();
        setTimeout(() => {
          const error: any = new Error('spawn guard-rail EACCES');
          error.message = 'spawn guard-rail EACCES';
          mockProcess.emit('error', error);
        }, 10);
        return mockProcess;
      };

      try {
        await executor.execute('/test/schema.json');
        assert.fail('Should have thrown an error');
      } catch (error) {
        assert.ok(error instanceof Error);
        assert.ok(error.message.includes('Permission denied'));
      }
    });

    it('should handle generic spawn errors', async () => {
      mockSpawnFn = () => {
        const mockProcess = new MockChildProcess();
        setTimeout(() => {
          mockProcess.emit('error', new Error('Generic spawn error'));
        }, 10);
        return mockProcess;
      };

      try {
        await executor.execute('/test/schema.json');
        assert.fail('Should have thrown an error');
      } catch (error) {
        assert.ok(error instanceof Error);
        assert.ok(error.message.includes('Failed to execute'));
      }
    });

    it('should handle spawn throwing synchronously', async () => {
      mockSpawnFn = () => {
        throw new Error('Synchronous spawn error');
      };

      try {
        await executor.execute('/test/schema.json');
        assert.fail('Should have thrown an error');
      } catch (error) {
        assert.ok(error instanceof Error);
        assert.ok(error.message.includes('Failed to spawn'));
      }
    });

    it('should accumulate stdout data from multiple chunks', async () => {
      const mockProcess = new MockChildProcess();

      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stdout.emit('data', Buffer.from('[{"compliant": [],'));
          mockProcess.stdout.emit('data', Buffer.from(' "non_compliant": {},'));
          mockProcess.stdout.emit('data', Buffer.from(' "warning": {}, "skipped": []}]'));
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      const results = await executor.execute('/test/schema.json');
      assert.ok(Array.isArray(results));
    });

    it('should log exit code', async () => {
      const mockProcess = new MockChildProcess();

      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stdout.emit('data', Buffer.from(JSON.stringify([{
            compliant: [],
            non_compliant: {},
            warning: {},
            skipped: []
          }])));
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      await executor.execute('/test/schema.json');
      assert.ok(mockOutputChannel.hasMessage('exited with code'));
    });

    it('should log received output length', async () => {
      const mockProcess = new MockChildProcess();

      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stdout.emit('data', Buffer.from(JSON.stringify([{
            compliant: [],
            non_compliant: {},
            warning: {},
            skipped: []
          }])));
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      await executor.execute('/test/schema.json');
      assert.ok(mockOutputChannel.hasMessage('characters'));
    });

    it('should log when checking stderr for JSON', async () => {
      const mockProcess = new MockChildProcess();

      mockSpawnFn = () => {
        setTimeout(() => {
          // Empty stdout, JSON in stderr
          mockProcess.stderr.emit('data', Buffer.from(JSON.stringify([{
            compliant: [],
            non_compliant: {},
            warning: {},
            skipped: []
          }])));
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      await executor.execute('/test/schema.json');
      assert.ok(mockOutputChannel.hasMessage('checking stderr'));
    });

    it('should log successful JSON parse', async () => {
      const mockProcess = new MockChildProcess();

      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stdout.emit('data', Buffer.from(JSON.stringify([{
            compliant: [],
            non_compliant: {},
            warning: {},
            skipped: []
          }])));
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      await executor.execute('/test/schema.json');
      assert.ok(mockOutputChannel.hasMessage('Successfully parsed JSON'));
    });

    it('should log Python dict conversion attempt', async () => {
      const mockProcess = new MockChildProcess();

      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stdout.emit('data', Buffer.from(
            "[{'compliant': [], 'non_compliant': {}, 'warning': {}, 'skipped': []}]"
          ));
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      await executor.execute('/test/schema.json');
      assert.ok(mockOutputChannel.hasMessage('Python dict conversion'));
    });

    it('should log validation completion with result count', async () => {
      const mockProcess = new MockChildProcess();

      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stdout.emit('data', Buffer.from(JSON.stringify([
            { compliant: [], non_compliant: {}, warning: {}, skipped: [] },
            { compliant: [], non_compliant: {}, warning: {}, skipped: [] }
          ])));
          mockProcess.emit('close', 0);
        }, 10);
        return mockProcess;
      };

      await executor.execute('/test/schema.json');
      assert.ok(mockOutputChannel.hasMessage('Validation completed successfully'));
      assert.ok(mockOutputChannel.hasMessage('2 result'));
    });

    it('should handle stderr output with exit code 2', async () => {
      const mockProcess = new MockChildProcess();

      mockSpawnFn = () => {
        setTimeout(() => {
          mockProcess.stderr.emit('data', Buffer.from('Error: Something went wrong'));
          mockProcess.emit('close', 2);
        }, 10);
        return mockProcess;
      };

      try {
        await executor.execute('/test/schema.json');
        assert.fail('Should have thrown an error');
      } catch (error) {
        assert.ok(error instanceof Error);
        assert.ok(mockOutputChannel.hasMessage('stderr output'));
      }
    });
  });
});

// Simple test runner
function describe(name: string, fn: () => void) {
  console.log(`\n${name}`);
  fn();
}

function beforeEach(fn: () => void) {
  (global as any).__beforeEach = fn;
}

function afterEach(fn: () => void) {
  (global as any).__afterEach = fn;
}

function it(name: string, fn: () => void | Promise<void>) {
  const runTest = async () => {
    try {
      if ((global as any).__beforeEach) {
        (global as any).__beforeEach();
      }
      await fn();
      if ((global as any).__afterEach) {
        (global as any).__afterEach();
      }
      console.log(`  ✓ ${name}`);
    } catch (error) {
      if ((global as any).__afterEach) {
        try {
          (global as any).__afterEach();
        } catch (afterError) {
          // Ignore afterEach errors
        }
      }
      console.log(`  ✗ ${name}`);
      console.error(`    ${error instanceof Error ? error.message : error}`);
      process.exitCode = 1;
    }
  };

  runTest();
}

// Run tests if this file is executed directly
if (require.main === module) {
  console.log('Running GuardRailExecutor tests...');
}
