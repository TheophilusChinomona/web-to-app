package com.webtoapp.core.expo

import com.webtoapp.data.model.MultiWebConfig

object ExpoAppTemplate {

    fun webView(url: String): String = """
import React, { useEffect } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, StyleSheet } from 'react-native';
import * as WebBrowser from 'expo-web-browser';

const TARGET_URL = '${url.replace("'", "\\'")}';

export default function App() {
  useEffect(() => {
    WebBrowser.openBrowserAsync(TARGET_URL);
  }, []);

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#6200ee" />
      <Text style={styles.label}>Opening...</Text>
      <TouchableOpacity style={styles.button} onPress={() => WebBrowser.openBrowserAsync(TARGET_URL)}>
        <Text style={styles.buttonText}>Open again</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 16, padding: 24 },
  label: { fontSize: 16, color: '#555' },
  button: { marginTop: 8, paddingHorizontal: 24, paddingVertical: 10, backgroundColor: '#6200ee', borderRadius: 8 },
  buttonText: { color: '#fff', fontWeight: '600' },
});
""".trimIndent()

    fun inlineHtml(htmlContent: String): String {
        val escapedForJs = htmlContent
            .replace("\\", "\\\\")
            .replace("`", "\\`")
            .replace("\${", "\\\${")
        return """
import React, { useEffect } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, StyleSheet } from 'react-native';
import * as WebBrowser from 'expo-web-browser';

const HTML_CONTENT = `$escapedForJs`;

function openHtml() {
  const encoded = encodeURIComponent(HTML_CONTENT);
  WebBrowser.openBrowserAsync('data:text/html,' + encoded);
}

export default function App() {
  useEffect(() => {
    openHtml();
  }, []);

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#6200ee" />
      <Text style={styles.label}>Opening page...</Text>
      <TouchableOpacity style={styles.button} onPress={openHtml}>
        <Text style={styles.buttonText}>Open again</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 16, padding: 24 },
  label: { fontSize: 16, color: '#555' },
  button: { marginTop: 8, paddingHorizontal: 24, paddingVertical: 10, backgroundColor: '#6200ee', borderRadius: 8 },
  buttonText: { color: '#fff', fontWeight: '600' },
});
""".trimIndent()
    }

    fun multiWeb(config: MultiWebConfig): String {
        val sites = config.sites
        val sitesJson = sites.mapIndexed { i, site ->
            val name = site.name.replace("'", "\\'")
            val url = site.url.replace("'", "\\'")
            "  { key: 'site$i', label: '$name', url: '$url' }"
        }.joinToString(",\n")

        return """
import React from 'react';
import { View, Text, TouchableOpacity, ScrollView, StyleSheet, StatusBar } from 'react-native';
import * as WebBrowser from 'expo-web-browser';

const SITES = [
$sitesJson
];

export default function App() {
  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <Text style={styles.heading}>Sites</Text>
      <ScrollView contentContainerStyle={styles.list}>
        {SITES.map((site) => (
          <TouchableOpacity
            key={site.key}
            style={styles.row}
            onPress={() => WebBrowser.openBrowserAsync(site.url)}
          >
            <Text style={styles.label}>{site.label}</Text>
            <Text style={styles.url} numberOfLines={1}>{site.url}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  heading: { fontSize: 20, fontWeight: '700', padding: 20, paddingTop: 56, backgroundColor: '#fff', borderBottomWidth: 1, borderColor: '#e0e0e0' },
  list: { padding: 12, gap: 8 },
  row: { backgroundColor: '#fff', borderRadius: 12, padding: 16, elevation: 1, shadowColor: '#000', shadowOpacity: 0.05, shadowRadius: 4, shadowOffset: { width: 0, height: 2 } },
  label: { fontSize: 16, fontWeight: '600', color: '#111', marginBottom: 4 },
  url: { fontSize: 13, color: '#6200ee' },
});
""".trimIndent()
    }

    fun serverApp(url: String, serverNote: String): String = """
import React, { useEffect } from 'react';
import { View, Text, TouchableOpacity, ActivityIndicator, StyleSheet } from 'react-native';
import * as WebBrowser from 'expo-web-browser';

// ${serverNote.replace("\n", "\n// ")}

const SERVER_URL = '${url.replace("'", "\\'")}';

export default function App() {
  useEffect(() => {
    WebBrowser.openBrowserAsync(SERVER_URL);
  }, []);

  return (
    <View style={styles.container}>
      <ActivityIndicator size="large" color="#6200ee" />
      <Text style={styles.label}>Connecting to server...</Text>
      <Text style={styles.note}>Make sure your server is running and externally accessible.</Text>
      <TouchableOpacity style={styles.button} onPress={() => WebBrowser.openBrowserAsync(SERVER_URL)}>
        <Text style={styles.buttonText}>Retry</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 12, padding: 24 },
  label: { fontSize: 16, color: '#555' },
  note: { fontSize: 13, color: '#999', textAlign: 'center' },
  button: { marginTop: 8, paddingHorizontal: 24, paddingVertical: 10, backgroundColor: '#6200ee', borderRadius: 8 },
  buttonText: { color: '#fff', fontWeight: '600' },
});
""".trimIndent()

    fun embeddedHtml(): String = """
import React, { useEffect, useState } from 'react';
import { View, Text, ActivityIndicator, StyleSheet } from 'react-native';
import { Asset } from 'expo-asset';
import * as FileSystem from 'expo-file-system';
import * as WebBrowser from 'expo-web-browser';

const webAsset = require('./assets/web.html');

export default function App() {
  const [status, setStatus] = useState('Loading...');

  useEffect(() => {
    (async () => {
      try {
        const asset = Asset.fromModule(webAsset);
        await asset.downloadAsync();
        const base64 = await FileSystem.readAsStringAsync(asset.localUri!, {
          encoding: FileSystem.EncodingType.Base64,
        });
        await WebBrowser.openBrowserAsync('data:text/html;base64,' + base64);
        setStatus('');
      } catch (e: any) {
        setStatus('Failed to load: ' + (e?.message ?? e));
      }
    })();
  }, []);

  return (
    <View style={styles.container}>
      {status ? (
        <>
          <ActivityIndicator size="large" color="#6200ee" />
          <Text style={styles.label}>{status}</Text>
        </>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center', gap: 16 },
  label: { fontSize: 14, color: '#555' },
});
""".trimIndent()

    fun appJson(
        appName: String,
        slug: String,
        packageName: String,
        bundleIdentifier: String,
        sdkVersion: String
    ): String = """
{
  "expo": {
    "name": "${appName.replace("\"", "\\\"")}",
    "slug": "$slug",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/icon.png",
    "userInterfaceStyle": "automatic",
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#ffffff"
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/adaptive-icon.png",
        "backgroundColor": "#ffffff"
      },
      "package": "${packageName.ifBlank { "com.example.app" }}"
    },
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "$bundleIdentifier"
    },
    "sdkVersion": "$sdkVersion.0.0",
    "assetBundlePatterns": ["assets/**/*"]
  }
}
""".trimIndent()

    fun packageJson(appName: String, sdkVersion: String): String = """
{
  "name": "${appName.lowercase().replace(Regex("[^a-z0-9-]"), "-")}",
  "version": "1.0.0",
  "main": "node_modules/expo/AppEntry.js",
  "scripts": {
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios"
  },
  "dependencies": {
    "expo": "~$sdkVersion.0.0",
    "expo-asset": "~10.0.10",
    "expo-file-system": "~17.0.1",
    "expo-status-bar": "~1.12.1",
    "expo-web-browser": "~13.0.1",
    "react": "18.2.0",
    "react-native": "0.73.6"
  },
  "devDependencies": {
    "@babel/core": "^7.20.0"
  },
  "private": true
}
""".trimIndent()

    val babelConfig: String = """
module.exports = function(api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
  };
};
""".trimIndent()

    val tsConfig: String = """
{
  "extends": "expo/tsconfig.base",
  "compilerOptions": {
    "strict": true
  }
}
""".trimIndent()

    fun readme(appName: String): String = """
# $appName — Expo Project

Generated by WebToApp. Run this project on **iOS and Android** using Expo Go — no Android SDK or Xcode required.

## Quick Start

1. Install [Node.js 18+](https://nodejs.org) on your computer.

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npx expo start
   ```

4. Scan the QR code with the **Expo Go** app on your phone.
   - **iOS**: [Download Expo Go from the App Store](https://apps.apple.com/app/expo-go/id982107779)
   - **Android**: [Download Expo Go from Google Play](https://play.google.com/store/apps/details?id=host.exp.exponent)

The app will open in a browser overlay powered by `expo-web-browser`, which is bundled inside Expo Go — no native build step needed.

## Build for Production (optional)

To compile a standalone .apk or .ipa without needing Android Studio or Xcode, use EAS Build:

```
npm install -g eas-cli
eas login
eas build --platform all
```

EAS builds in the cloud and delivers ready-to-install binaries.

## Notes

- **HTML apps**: content is loaded via a `data:text/html` URI. Very large HTML pages (> ~2 MB) may be truncated by the OS browser — for those, consider hosting the HTML online and using a URL-based app instead.
- **Next.js / React / Vue static apps**: run `next build` (with `output: 'export'` in `next.config.js`), `vite build`, or your framework's static export command, then import the output folder (`out/`, `dist/`) into WebToApp as a Frontend app. The Expo export will inline all CSS, JS, and images into a single self-contained `assets/web.html` file and load it via a base64 data URI — no server required.
- Expo SDK 51 targets React Native 0.73.6.
""".trimIndent()
}
