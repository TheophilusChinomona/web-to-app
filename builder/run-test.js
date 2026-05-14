#!/usr/bin/env node
import { spawn } from 'child_process';
import { resolve } from 'path';

// Build first
console.log("🔨 Building TypeScript...");
const build = spawn('npx', ['tsc', '--noEmit'], { cwd: resolve(__dirname, '.'), stdio: 'inherit' });
build.on('close', (code) => {
  if (code !== 0) {
    console.error("❌ Build failed");
    process.exit(code);
  }
  console.log("✅ Build passed");
  
  // Now run the integration test via ts-node
  console.log("🧪 Running integration test...");
  const test = spawn('npx', ['ts-node', '--esm', 'test/integration.test.ts'], { 
    cwd: resolve(__dirname, '.'),
    stdio: 'inherit',
    env: { ...process.env, TS_NODE_TRANSPILE_ONLY: '1' }
  });
  
  test.on('close', (code) => {
    process.exit(code);
  });
});
