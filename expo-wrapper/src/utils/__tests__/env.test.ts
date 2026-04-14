jest.mock('expo-constants', () => ({
  expoConfig: {
    extra: {
      websiteUrl: 'https://example.com'
    }
  },
  manifest2: null
}));

describe('env config', () => {
  it('exports website url and allowed host from config', () => {
    jest.resetModules();
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const env = require('../../config/env');
    expect(env.WEBSITE_URL).toBe('https://example.com');
    expect(env.ALLOWED_HOSTS).toEqual(['example.com']);
  });
});
