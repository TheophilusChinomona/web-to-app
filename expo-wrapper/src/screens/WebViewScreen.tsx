import { useCallback, useRef, useState } from 'react';
import { StyleSheet, View } from 'react-native';
import WebView, { ShouldStartLoadRequest } from 'react-native-webview';
import { ErrorState } from '@/components/ErrorState';
import { LoadingOverlay } from '@/components/LoadingOverlay';
import { ALLOWED_HOSTS, WEBSITE_URL } from '@/config/env';
import { openExternalLink } from '@/utils/linking';
import { isSafeNavigationUrl } from '@/utils/navigationGuard';

export function WebViewScreen() {
  const webviewRef = useRef<WebView>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  const onShouldStartLoadWithRequest = useCallback((request: ShouldStartLoadRequest) => {
    const isSafeInternal = isSafeNavigationUrl(request.url, ALLOWED_HOSTS);

    if (isSafeInternal) {
      return true;
    }

    void openExternalLink(request.url);
    return false;
  }, []);

  const handleRetry = useCallback(() => {
    setHasError(false);
    setIsLoading(true);
    webviewRef.current?.reload();
  }, []);

  return (
    <View style={styles.container}>
      <WebView
        ref={webviewRef}
        source={{ uri: WEBSITE_URL }}
        originWhitelist={['http://*', 'https://*']}
        javaScriptEnabled
        domStorageEnabled
        onLoadStart={() => setIsLoading(true)}
        onLoadEnd={() => setIsLoading(false)}
        onError={() => {
          setHasError(true);
          setIsLoading(false);
        }}
        onHttpError={() => {
          setHasError(true);
          setIsLoading(false);
        }}
        onShouldStartLoadWithRequest={onShouldStartLoadWithRequest}
        setSupportMultipleWindows={false}
      />

      {isLoading && !hasError ? <LoadingOverlay /> : null}
      {hasError ? <ErrorState message="Could not load the website. Check the URL and network, then retry." onRetry={handleRetry} /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1
  }
});
