import { GeneratorService } from '../services/GeneratorService';
import * as fs from 'fs';
import * as path from 'path';

describe('GeneratorService Integration', () => {
  it('generates a valid Expo project structure', async () => {
    const config = {
      id: 'test-123',
      name: 'MyGeneratedApp',
      url: 'https://example.com',
      packageName: 'com.example.mygeneratedapp',
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

    const outputDir = path.join(__dirname, '../test-output/my-generated-app');
    if (fs.existsSync(outputDir)) {
      fs.rmSync(outputDir, { recursive: true, force: true });
    }

    const result = await GeneratorService.generateProject(config, outputDir);
    expect(fs.existsSync(result)).toBe(true);

    const requiredFiles = ['App.tsx', 'app.json', 'package.json', 'eas.json', 'app/webview.tsx', 'app/_layout.tsx'];
    for (const file of requiredFiles) {
      expect(fs.existsSync(path.join(result, file))).toBe(true);
    }

    console.log('✅ Integration test passed');
  });
});
