import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Button,
} from 'react-native-paper';
import { useLocalSearchParams, useRouter } from 'expo-router';
import * as FileSystem from 'expo-file-system';
import { useProjects } from '../../hooks/useProjects';

export default function ProjectDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { projects, deleteProject } = useProjects();

  const project = projects.find(p => p.id === id);

  if (!project) {
    return (
      <View style={styles.center}>
        <Text>Project not found</Text>
        <Button onPress={() => router.back()}>Go Back</Button>
      </View>
    );
  }

  const handleDelete = () => {
    Alert.alert('Delete Project?', 'This cannot be undone.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          await deleteProject(project.id);
          router.back();
        },
      },
    ]);
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Title>{project.name}</Title>
        <Paragraph>{project.url}</Paragraph>
      </View>

      <Card style={styles.card}>
        <Card.Title title="Configuration" />
        <Card.Content>
          <Text>Package: {project.packageName}</Text>
          <Text>Version: {project.version}</Text>
          <Text>Created: {new Date(project.createdAt).toLocaleDateString()}</Text>
          <Text>Splash: {project.features.splashEnabled ? 'Yes' : 'No'}</Text>
          <Text>Extensions: {project.features.extensions.length} selected</Text>
        </Card.Content>
      </Card>

      <View style={styles.buttonGroup}>
        <Button
          mode="contained"
          onPress={() => {}}
          style={styles.button}
        >
          Regenerate Project
        </Button>

        <Button
          mode="outlined"
          onPress={() => {}}
          style={styles.button}
        >
          Share / Export
        </Button>

        <Button
          mode="text"
          onPress={() => {
            Alert.alert(
              'Open in Expo Go',
              'Go to generated folder and run:\n\nnpx expo start\n\nThen scan QR with Expo Go.'
            );
          }}
          style={styles.button}
        >
          How to Open in Expo Go
        </Button>

        <Button
          mode="text"
          onPress={handleDelete}
          textColor="#d32f2f"
          style={styles.button}
        >
          Delete Project
        </Button>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { marginBottom: 24 },
  card: { marginBottom: 24 },
  buttonGroup: { gap: 12 },
  button: { paddingVertical: 8 },
});
