
import { GeneratorService } from './services/GeneratorService';
import * as fs from 'fs';
import * as path from 'path';

const config = {
  id: 'test-999',
  name: 'FinalTestApp',
  url: 'https://example.com',
  packageName: 'com.example.finaltest',
  version: '1.0.0',
  icon: null,
  splash: null,
  features: { splashEnabled: true, bgmEnabled: false, translationEnabled: false, extensions: ['ad-blocker'] },
  createdAt: Date.now(),
  updatedAt: Date.now(),
};

const outputDir = path.join(__dirname, 'test-output', 'final');
if (fs.existsSync(outputDir)) fs.rmSync(outputDir, { recursive: true, force: true });

await GeneratorService.generateProject(config, outputDir);
console.log('✅ Generated:', outputDir);

const required = ['App.tsx', 'app.json', 'package.json', 'app/webview.tsx', 'assets'];
let allOk = true;
for (const f of required) {
  if (!fs.existsSync(path.join(outputDir, f))) {
    console.error('❌ Missing:', f);
    allOk = false;
  }
}
if (allOk) console.log('✅ All files present');
else process.exit(1);

const appJson = JSON.parse(fs.readFileSync(path.join(outputDir, 'app.json'), 'utf-8'));
if (appJson.expo.name === 'FinalTestApp') console.log('✅ app.json name correct');
else { console.error('❌ name mismatch'); allOk = false; }

const webview = fs.readFileSync(path.join(outputDir, 'app/webview.tsx'), 'utf-8');
if (webview.includes('https://example.com') && webview.includes('"ad-blocker"')) console.log('✅ WebView & extensions OK');
else { console.error('❌ injection failed'); allOk = false; }

if (allOk) {
  console.log('\n🎉 GENERATOR TEST PASSED');
  process.exit(0);
} else {
  process.exit(1);
}
