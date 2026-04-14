import type { ExpoConfig } from 'expo/config';

const APP_NAME = 'Web Wrapper';
const APP_SLUG = 'expo-wrapper';
const SCHEME = 'webwrapper';
const WEBSITE_URL = process.env.EXPO_PUBLIC_WEBSITE_URL || 'https://example.com';

const config: ExpoConfig = {
  name: APP_NAME,
  slug: APP_SLUG,
  scheme: SCHEME,
  version: '1.0.0',
  orientation: 'portrait',
  userInterfaceStyle: 'light',
  platforms: ['ios', 'android'],
  jsEngine: 'hermes',
  ios: {
    supportsTablet: true,
    bundleIdentifier: 'com.theochinomona.webwrapper'
  },
  android: {
    package: 'com.theochinomona.webwrapper'
  },
  extra: {
    websiteUrl: WEBSITE_URL,
    eas: {
      projectId: 'replace-with-your-eas-project-id'
    }
  },
  plugins: ['expo-router']
};

export default config;
