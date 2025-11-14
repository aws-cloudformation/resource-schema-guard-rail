/**
 * Simple test runner for VS Code extension unit tests
 * Runs all test files in the test directory
 */

import * as path from 'path';
import * as fs from 'fs';

async function runTests() {
  console.log('Running VS Code Extension Tests\n');
  console.log('================================\n');

  const testDir = __dirname;
  const testFiles = fs.readdirSync(testDir)
    .filter(file => file.endsWith('.test.js'))
    .map(file => path.join(testDir, file));

  if (testFiles.length === 0) {
    console.log('No test files found');
    process.exit(1);
  }

  let hasFailures = false;

  for (const testFile of testFiles) {
    const testName = path.basename(testFile, '.test.js');
    console.log(`\nRunning ${testName} tests...`);
    console.log('-'.repeat(50));

    try {
      // Clear the module cache to ensure fresh test execution
      delete require.cache[testFile];
      
      // Require the test file which will execute the tests
      require(testFile);
      
      // Check if any test failed
      if (process.exitCode === 1) {
        hasFailures = true;
      }
    } catch (error) {
      console.error(`\nError running ${testName}:`, error);
      hasFailures = true;
    }
  }

  console.log('\n================================');
  if (hasFailures) {
    console.log('\n❌ Some tests failed');
    process.exit(1);
  } else {
    console.log('\n✅ All tests passed');
    process.exit(0);
  }
}

// Run tests
runTests().catch(error => {
  console.error('Fatal error running tests:', error);
  process.exit(1);
});
