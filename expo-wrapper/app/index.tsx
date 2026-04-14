import { StatusBar } from 'expo-status-bar';
import { SafeAreaView, StyleSheet } from 'react-native';
import { WebViewScreen } from '@/screens/WebViewScreen';

export default function Home() {
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />
      <WebViewScreen />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff'
  }
});
