import Constants from 'expo-constants';

const fallbackUrl = 'https://example.com';

const fromExpoConfig =
  (Constants.expoConfig?.extra?.websiteUrl as string | undefined) ||
  (Constants.manifest2?.extra?.expoClient?.extra?.websiteUrl as string | undefined);

export const WEBSITE_URL = (fromExpoConfig || process.env.EXPO_PUBLIC_WEBSITE_URL || fallbackUrl).trim();

export const ALLOWED_HOSTS = [new URL(WEBSITE_URL).host];
