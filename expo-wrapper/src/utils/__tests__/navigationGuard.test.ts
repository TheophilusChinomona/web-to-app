import { isSafeNavigationUrl } from '../navigationGuard';

describe('isSafeNavigationUrl', () => {
  const allowedHosts = ['example.com'];

  it('allows https links on approved host', () => {
    expect(isSafeNavigationUrl('https://example.com/path', allowedHosts)).toBe(true);
  });

  it('blocks non-approved hosts', () => {
    expect(isSafeNavigationUrl('https://evil.com', allowedHosts)).toBe(false);
  });

  it('blocks non-http(s) schemes', () => {
    expect(isSafeNavigationUrl('mailto:test@example.com', allowedHosts)).toBe(false);
    expect(isSafeNavigationUrl('javascript:alert(1)', allowedHosts)).toBe(false);
  });

  it('blocks malformed urls', () => {
    expect(isSafeNavigationUrl('not-a-url', allowedHosts)).toBe(false);
  });
});
