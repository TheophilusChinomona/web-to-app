const { GeneratorService } = require('./dist/services/GeneratorService');
const fs = require('fs');
const path = require('path');

async function run() {
  console.log("🧪 Starting generator integration test...");
  
  const config = {
    id: 'test-456',
    name: 'QuickTestApp',
    url: 'https://example.com',
    packageName: 'com.example.quicktest',
    version: '1.0.0',
    icon: null,
    splash: null,
    features: {
      splashEnabled: true,
      bgmEnabled: false,
      translationEnabled: false,
      extensions: ['ad-blocker'],
    },
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };

  const outputDir = path.join(__dirname, 'test-output', 'quicktest');
  if (fs.existsSync(outputDir)) {
    fs.rmSync(outputDir, { recursive: true, force: true });
  }

  try {
    const result = await GeneratorService.generateProject(config, outputDir);
    console.log("✅ Project generated at:", result);

    // Verify structure
    const checks = [
      'App.tsx',
      'app.json',
      'package.json',
      'eas.json',
      'app/webview.tsx',
      'app/_layout.tsx',
      'assets',
    ];
    
    let allOk = true;
    for (const file of checks) {
      const full = path.join(result, file);
      if (!fs.existsSync(full)) {
        console.error("❌ Missing:", file);
        allOk = false;
      }
    }
    
    if (allOk) {
      console.log("✅ All required files present");
      
      // Check content
      const appJson = JSON.parse(fs.readFileSync(path.join(result, 'app.json'), 'utf-8'));
      if (appJson.expo.name === 'QuickTestApp') {
        console.log("✅ Placeholder replacement works");
      } else {
        console.error("❌ Placeholder not replaced correctly");
        allOk = false;
      }
      
      const webview = fs.readFileSync(path.join(result, 'app/webview.tsx'), 'utf-8');
      if (webview.includes('https://example.com') && webview.includes('ad-blocker')) {
        console.log("✅ WebView config and extensions injected");
      } else {
        console.error("❌ Injection failed");
        allOk = false;
      }
    }

    if (allOk) {
      console.log("
🎉 INTEGRATION TEST PASSED");
      process.exit(0);
    } else {
      console.error("
❌ TEST FAILED");
      process.exit(1);
    }
  } catch (err) {
    console.error("❌ Error:", err);
    process.exit(1);
  }
}

run();
