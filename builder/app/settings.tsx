import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import {
  List,
  Switch,
  Divider,
  Button,
  Title,
  Paragraph,
} from 'react-native-paper';
import { useUI } from '../hooks/useUI';

export default function SettingsScreen() {
  const { isDarkMode, toggleTheme } = useUI();

  return (
    <ScrollView style={styles.container}>
      <Title style={styles.title}>Settings</Title>

      <List.Item
        title="Dark Mode"
        description="Toggle between light and dark theme"
        left={(props) => <List.Icon {...props} icon="theme-light-dark" />}
        right={() => (
          <Switch value={isDarkMode} onValueChange={toggleTheme} />
        )}
      />

      <Divider />

      <List.Item
        title="About WebToApp Builder"
        description="Version 1.0.0"
        left={(props) => <List.Icon {...props} icon="information" />}
      />

      <List.Item
        title="Source Code"
        description="View on GitHub"
        left={(props) => <List.Icon {...props} icon="github" />}
        onPress={() => {}}
      />

      <View style={styles.footer}>
        <Paragraph>Generated apps are compatible with Expo Go.</Paragraph>
        <Paragraph>Build standalone APKs with EAS Build.</Paragraph>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  title: { marginBottom: 16 },
  footer: { marginTop: 32, gap: 8 },
});
