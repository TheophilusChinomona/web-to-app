import * as Linking from 'expo-linking';

const SAFE_PROTOCOLS = ['http:', 'https:', 'mailto:', 'tel:'];

export function canOpenExternally(url: string) {
  try {
    const parsed = new URL(url);
    return SAFE_PROTOCOLS.includes(parsed.protocol);
  } catch {
    return false;
  }
}

export async function openExternalLink(url: string) {
  if (!canOpenExternally(url)) {
    return false;
  }

  const supported = await Linking.canOpenURL(url);
  if (!supported) {
    return false;
  }

  await Linking.openURL(url);
  return true;
}
