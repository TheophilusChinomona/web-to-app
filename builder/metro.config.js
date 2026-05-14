const { getDefaultConfig } = require('expo/metro-config');

module.exports = (async () => {
  const defaultConfig = await getDefaultConfig(__dirname);
  // Disable Hermes parser for all platforms (simpler, more compatible)
  defaultConfig.transformer = {
    ...defaultConfig.transformer,
    hermesParser: false,
  };
  return defaultConfig;
})();
