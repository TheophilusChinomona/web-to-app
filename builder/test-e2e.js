
const { GeneratorService } = require('./dist/services/services/GeneratorService.js');
const fs = require('fs');
const path = require('path');

async function run() {
  const config = {
    id: 'test-888',
    name: 'E2ETestApp',
    url: 'https://example.com',
    packageName: 'com.example.e2etest',
    version: '1.0.0',
    icon: null,
    splash: null,
    features: { splashEnabled: true, bgmEnabled: false, translationEnabled: false, extensions: ['ad-blocker'] },
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };

  const outputDir = path.join(__dirname, 'test-output', 'e2e-final');
  if (fs.existsSync(outputDir)) fs.rmSync(outputDir, { recursive: true, force: true };

  await GeneratorService.generateProject(config, outputDir);
  console.log('✅ Generated');

  // Verify
  const required = ['App.tsx', 'app.json', 'package.json', 'app/webview.tsx', 'assets'];
  let ok = true;
  for (const f of required) {
    if (!fs.existsSync(path.join(outputDir, f))) {
      console.error('❌ Missing:', f);
      ok = false;
    }
  }
  if (!ok) process.exit(1);

  const appJson = JSON.parse(fs.readFileSync(path.join(outputDir, 'app.json'), 'utf-8'));
  if (appJson.expo.name !== 'E2ETestApp') throw new Error('name mismatch');
  
  const web = fs.readFileSync(path.join(outputDir, 'app/webview.tsx'), 'utf-8');
  if (!web.includes('https://example.com') || !web.includes('"ad-blocker"')) throw new Error('injection failed');

  console.log('✅ All checks passed');
  console.log('\n🎉 GENERATOR E2E TEST PASSED');
}

run().catch(err => {
  console.error('❌', err);
  process.exit(1);
});
