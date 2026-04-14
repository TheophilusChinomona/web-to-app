import { canOpenExternally, openExternalLink } from '../linking';
import * as Linking from 'expo-linking';

jest.mock('expo-linking', () => ({
  canOpenURL: jest.fn(),
  openURL: jest.fn()
}));

describe('linking utilities', () => {
  it('canOpenExternally allows safe protocols', () => {
    expect(canOpenExternally('https://example.com')).toBe(true);
    expect(canOpenExternally('mailto:test@example.com')).toBe(true);
    expect(canOpenExternally('javascript:alert(1)')).toBe(false);
  });

  it('openExternalLink returns false for unsafe url', async () => {
    await expect(openExternalLink('javascript:alert(1)')).resolves.toBe(false);
    expect(Linking.canOpenURL).not.toHaveBeenCalled();
  });

  it('openExternalLink opens supported safe urls', async () => {
    (Linking.canOpenURL as jest.Mock).mockResolvedValue(true);
    (Linking.openURL as jest.Mock).mockResolvedValue(undefined);

    await expect(openExternalLink('https://example.com')).resolves.toBe(true);
    expect(Linking.canOpenURL).toHaveBeenCalledWith('https://example.com');
    expect(Linking.openURL).toHaveBeenCalledWith('https://example.com');
  });

  it('openExternalLink returns false when unsupported', async () => {
    (Linking.canOpenURL as jest.Mock).mockResolvedValue(false);

    await expect(openExternalLink('https://example.com')).resolves.toBe(false);
    expect(Linking.openURL).not.toHaveBeenCalled();
  });
});
