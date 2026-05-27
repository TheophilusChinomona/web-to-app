package com.webtoapp.core.expo

import com.webtoapp.data.model.MultiWebConfig

object ExpoAppTemplate {

    fun webView(url: String): String = """
import React from 'react';
import { View, StatusBar, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';

export default function App() {
  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <WebView
        source={{ uri: '${url.replace("'", "\\'")}' }}
        style={styles.webview}
        javaScriptEnabled
        domStorageEnabled
        startInLoadingState
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  webview: { flex: 1 },
});
""".trimIndent()

    fun inlineHtml(htmlContent: String): String {
        val escaped = htmlContent
            .replace("\\", "\\\\")
            .replace("`", "\\`")
            .replace("\${", "\\\${")
        return """
import React from 'react';
import { View, StatusBar, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';

const HTML_CONTENT = `$escaped`;

export default function App() {
  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <WebView
        source={{ html: HTML_CONTENT }}
        style={styles.webview}
        javaScriptEnabled
        domStorageEnabled
        originWhitelist={['*']}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  webview: { flex: 1 },
});
""".trimIndent()
    }

    fun multiWeb(config: MultiWebConfig): String {
        val sites = config.sites
        val tabsJson = sites.mapIndexed { i, site ->
            val name = site.name.replace("'", "\\'")
            val url = site.url.replace("'", "\\'")
            "  { key: 'tab$i', label: '$name', url: '$url' }"
        }.joinToString(",\n")

        return """
import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StatusBar, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';

const TABS = [
$tabsJson
];

export default function App() {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.tabBar}>
        {TABS.map((tab, i) => (
          <TouchableOpacity
            key={tab.key}
            style={[styles.tab, activeTab === i && styles.activeTab]}
            onPress={() => setActiveTab(i)}
          >
            <Text style={[styles.tabText, activeTab === i && styles.activeTabText]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
      <WebView
        source={{ uri: TABS[activeTab].url }}
        style={styles.webview}
        javaScriptEnabled
        domStorageEnabled
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  tabBar: { flexDirection: 'row', backgroundColor: '#fff', borderBottomWidth: 1, borderColor: '#e0e0e0' },
  tab: { flex: 1, paddingVertical: 12, alignItems: 'center' },
  activeTab: { borderBottomWidth: 2, borderBottomColor: '#6200ee' },
  tabText: { fontSize: 13, color: '#666' },
  activeTabText: { color: '#6200ee', fontWeight: '600' },
  webview: { flex: 1 },
});
""".trimIndent()
    }

    fun serverApp(url: String, serverNote: String): String = """
import React from 'react';
import { View, StatusBar, StyleSheet, Text } from 'react-native';
import { WebView } from 'react-native-webview';

// ${serverNote.replace("\n", "\n// ")}

export default function App() {
  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <WebView
        source={{ uri: '${url.replace("'", "\\'")}' }}
        style={styles.webview}
        javaScriptEnabled
        domStorageEnabled
        startInLoadingState
        renderError={() => (
          <View style={styles.error}>
            <Text>Could not connect. Make sure your server is running and accessible.</Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  webview: { flex: 1 },
  error: { flex: 1, padding: 24, justifyContent: 'center', alignItems: 'center' },
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
    "sdkVersion": "$sdkVersion.0.0"
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
    "expo-status-bar": "~1.11.1",
    "react": "18.2.0",
    "react-native": "0.73.0",
    "react-native-webview": "13.6.4"
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

Generated by WebToApp. Run this project on iOS and Android with Expo Go.

## Quick Start

1. Install dependencies:
   ```
   npm install
   ```

2. Start the development server:
   ```
   npx expo start
   ```

3. Scan the QR code with the **Expo Go** app on your phone.
   - iOS: Download Expo Go from the App Store
   - Android: Download Expo Go from Google Play

## Build for Production

Install the EAS CLI and build native binaries:

```
npm install -g eas-cli
eas build --platform all
```

This produces an .apk (Android) and .ipa (iOS) that can be submitted to app stores.

## Notes

- Requires Node.js 18+ installed on your machine
- Expo SDK 51 targets React Native 0.73
""".trimIndent()
}
