import React from 'react';
import { Stack } from 'expo-router';
import { PaperProvider, MD3DarkTheme, MD3LightTheme } from 'react-native-paper';
import { useUI } from '../hooks/useUI';

export default function RootLayout() {
  const { isDarkMode } = useUI();
  const theme = isDarkMode ? MD3DarkTheme : MD3LightTheme;

  return (
    <PaperProvider theme={theme}>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="index" options={{ title: 'WebToApp Builder' }} />
        <Stack.Screen name="create" options={{ title: 'Create App' }} />
        <Stack.Screen name="projects/[id]" options={{ title: 'Project Details' }} />
        <Stack.Screen name="settings" options={{ title: 'Settings' }} />
      </Stack>
    </PaperProvider>
  );
}
