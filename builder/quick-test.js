
const { GeneratorService } = require('./dist/services/GeneratorService');
const fs = require('fs');
const path = require('path');

const config = {
  id: 'test-789',
  name: 'MyTestApp',
  url: 'https://example.com',
  packageName: 'com.example.mytestapp',
  version: '1.0.0',
  icon: null,
  splash: null,
  features: { splashEnabled: true, bgmEnabled: false, translationEnabled: false, extensions: ['ad-blocker'] },
  createdAt: Date.now(),
  updatedAt: Date.now(),
};

const outputDir = path.join(__dirname, 'test-output', 'final-test');
if (fs.existsSync(outputDir)) fs.rmSync(outputDir, { recursive: true, force: true });

GeneratorService.generateProject(config, outputDir)
  .then(() => {
    console.log('✅ Generated to', outputDir);
    const required = ['App.tsx', 'app.json', 'package.json', 'app/webview.tsx', 'assets'];
    let ok = true;
    for (const f of required) {
      if (!fs.existsSync(path.join(outputDir, f))) {
        console.error('❌ Missing:', f);
        ok = false;
      }
    }
    if (ok) {
      const appJson = JSON.parse(fs.readFileSync(path.join(outputDir, 'app.json'), 'utf-8'));
      if (appJson.expo.name === 'MyTestApp') {
        console.log('✅ Placeholder replaced correctly');
      } else {
        console.error('❌ Name not replaced');
        ok = false;
      }
      const webview = fs.readFileSync(path.join(outputDir, 'app/webview.tsx'), 'utf-8');
      if (webview.includes('https://example.com') && webview.includes('code:')) {
        console.log('✅ Extensions injected');
      } else {
        console.error('❌ Injection failed');
        ok = false;
      }
    }
    if (ok) {
      console.log('\n🎉 ALL CHECKS PASSED');
      process.exit(0);
    } else {
      process.exit(1);
    }
  })
  .catch(err => {
    console.error('❌ Error:', err);
    process.exit(1);
  });
