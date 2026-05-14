import { ProjectConfig } from '../types';

export class GeneratorService {
  /**
   * Generates a complete Expo project from configuration
   */
  static async generateProject(config: ProjectConfig, outputDir: string): Promise<string> {
    // Ensure output directory exists
    await this.ensureDir(outputDir);

    // Copy template files and replace placeholders
    await this.copyTemplateFiles(config, outputDir);

    // Write generated project metadata
    await this.writeProjectMetadata(config, outputDir);

    // Copy or generate assets (icon, splash)
    await this.processAssets(config, outputDir);

    return outputDir;
  }

  private static async ensureDir(dir: string): Promise<void> {
    const fs = require('expo-file-system/build/index');
    const info = await fs.getInfoAsync(dir);
    if (!info.exists) {
      await fs.makeDirectoryAsync(dir, { intermediates: true });
    }
  }

  private static async copyTemplateFiles(config: ProjectConfig, outputDir: string): Promise<void> {
    const fs = require('expo-file-system/build/index');
    const templateDir = `${__dirname}/../templates/base`;

    // Load available extensions from builder's extensions/ directory
    const extensionsDir = `${__dirname}/../extensions`;
    const availableExtensions = await this.loadAvailableExtensions(extensionsDir);

    // Recursively copy all template files
    const copyRecursive = async (src: string, dest: string): Promise<void> => {
      const info = await fs.getInfoAsync(src);
      if (info.isFile) {
        let content = await fs.readAsStringAsync(src);
        // Inject extensions code if this file is webview.tsx
        if (src.endsWith('webview.tsx')) {
          content = this.injectExtensions(content, config, availableExtensions);
        } else {
          content = this.replacePlaceholders(content, config);
        }
        await fs.writeAsStringAsync(dest, content);
      } else if (info.isDirectory) {
        await fs.makeDirectoryAsync(dest, { intermediates: true });
        const items = await fs.readDirectoryAsync(src);
        for (const item of items) {
          await copyRecursive(`${src}/${item}`, `${dest}/${item}`);
        }
      }
    };

    await copyRecursive(templateDir, outputDir);
  }

  private static async loadAvailableExtensions(extensionsDir: string): Promise<Array<{id: string, name: string, code: string}>> {
    const fs = require('expo-file-system/build/index');
    try {
      const info = await fs.getInfoAsync(extensionsDir);
      if (!info.exists) return [];
      const files = await fs.readDirectoryAsync(extensionsDir);
      const extensions = [];
      for (const file of files) {
        if (file.endsWith('.js')) {
          const id = file.replace('.js', '');
          const code = await fs.readAsStringAsync(`${extensionsDir}/${file}`);
          // Parse name from first comment or use id
          const nameMatch = code.match(/\*\s*([^\n]+)/);
          const name = nameMatch ? nameMatch[1].trim() : id;
          extensions.push({ id, name, code });
        }
      }
      return extensions;
    } catch (error) {
      console.error('Failed to load extensions:', error);
      return [];
    }
  }

  private static injectExtensions(content: string, config: ProjectConfig, availableExtensions: Array<{id: string, name: string, code: string}>): string {
    // Build EXTENSIONS array objects with enabled flag
    const selectedIds = config.features.extensions || [];
    const enabledExtensions = availableExtensions
      .filter(ext => selectedIds.includes(ext.id))
      .map(ext => ({
        id: ext.id,
        name: ext.name,
        enabled: true,
        code: ext.code,
      }));

    // Replace {{EXTENSIONS}} with JSON string (no quotes around whole thing so it's valid JS)
    const extensionsJson = JSON.stringify(enabledExtensions, null, 2);
    return content.replace('{{EXTENSIONS}}', extensionsJson)
                  .replace('{{URL}}', config.url)
                  .replace('{{SPLASH_ENABLED}}', String(config.features.splashEnabled));
  }

  private static replacePlaceholders(content: string, config: ProjectConfig): string {
    const replacements: Record<string, string> = {
      '{{APP_NAME}}': config.name,
      '{{APP_NAME_SLUG}}': config.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, ''),
      '{{URL}}': config.url,
      '{{PACKAGE_NAME}}': config.packageName,
      '{{VERSION}}': config.version,
      '{{BUNDLE_IDENTIFIER}}': config.packageName,
      '{{ICON_BASE64}}': config.icon || '',
      '{{SPLASH_BASE64}}': config.splash || '',
      '{{SPLASH_ENABLED}}': String(config.features.splashEnabled),
      '{{BGM_ENABLED}}': String(config.features.bgmEnabled),
      '{{BGM_URL}}': config.features.bgmUrl || '',
      '{{TRANSLATION_ENABLED}}': String(config.features.translationEnabled),
      '{{EXTENSIONS}}': JSON.stringify(config.features.extensions, null, 2),
    };

    Object.entries(replacements).forEach(([key, value]) => {
      content = content.split(key).join(value);
    });

    return content;
  }

  private static async writeProjectMetadata(config: ProjectConfig, outputDir: string): Promise<void> {
    const fs = require('expo-file-system/build/index');
    const metaPath = `${outputDir}/web-to-app.config.json`;
    const meta = {
      ...config,
      generatedAt: new Date().toISOString(),
      generatorVersion: '1.0.0',
    };
    await fs.writeAsStringAsync(metaPath, JSON.stringify(meta, null, 2));
  }

  private static async processAssets(config: ProjectConfig, outputDir: string): Promise<void> {
    const fs = require('expo-file-system/build/index');
    const assetsDir = `${outputDir}/assets`;

    // Ensure assets directory exists
    await this.ensureDir(assetsDir);

    // Write icon if provided
    if (config.icon) {
      const iconPath = `${assetsDir}/icon.png`;
      await this.writeBase64ToFile(config.icon, iconPath);
    }

    // Write splash if provided
    if (config.splash) {
      const splashPath = `${assetsDir}/splash.png`;
      await this.writeBase64ToFile(config.splash, splashPath);
    }
  }

  private static async writeBase64ToFile(base64: string, filePath: string): Promise<void> {
    const fs = require('expo-file-system/build/index');
    // base64 may include data URI prefix; remove it
    const data = base64.replace(/^data:image\/\w+;base64,/, '');
    await fs.writeAsStringAsync(filePath, data, { encoding: fs.EncodingType.Base64 });
  }
}
