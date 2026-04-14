const BLOCKED_SCHEMES = ['javascript:', 'file:', 'data:', 'intent:'];

export function isSafeNavigationUrl(url: string, allowedHosts: string[]) {
  try {
    const parsed = new URL(url);

    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return false;
    }

    if (BLOCKED_SCHEMES.includes(parsed.protocol)) {
      return false;
    }

    return allowedHosts.includes(parsed.host);
  } catch {
    return false;
  }
}
