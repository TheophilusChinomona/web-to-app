import React, { useMemo } from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';
import * as SplashScreen from 'expo-splash-screen';

SplashScreen.preventAutoHideAsync();

const EXTENSIONS = {{EXTENSIONS}};

export default function WebViewScreen() {
  const url = "{{URL}}";
  const splashEnabled = {{SPLASH_ENABLED}};

  const injectedJavaScript = useMemo(() => {
    return EXTENSIONS
      .filter(ext => ext.enabled)
      .map(ext => ext.code)
      .join('\n\n');
  }, []);

  const handleLoadEnd = () => {
    SplashScreen.hideAsync();
  };

  return (
    <WebView
      source={{ uri: url }}
      style={styles.webview}
      javaScriptEnabled={true}
      domStorageEnabled={true}
      startInLoadingState={true}
      injectedJavaScript={injectedJavaScript}
      onLoadEnd={handleLoadEnd}
      renderLoading={() => (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" />
        </View>
      )}
      onError={(syntheticEvent) => {
        const { nativeEvent } = syntheticEvent;
        console.error('WebView error:', nativeEvent);
      }}
    />
  );
}

const styles = StyleSheet.create({
  webview: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
