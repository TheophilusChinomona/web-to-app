import React, { useEffect } from 'react';
import { View, FlatList, StyleSheet } from 'react-native';
import { FAB, IconButton } from 'react-native-paper';
import { Card, Title, Paragraph } from 'react-native-paper';
import { useProjects } from '../hooks/useProjects';
import { useUI } from '../hooks/useUI';
import { useRouter } from 'expo-router';

export default function HomeScreen() {
  const router = useRouter();
  const { projects, isLoading, loadProjects, deleteProject } = useProjects();
  const { isDarkMode } = useUI();

  useEffect(() => {
    loadProjects();
  }, []);

  const handleDelete = async (id: string) => {
    await deleteProject(id);
  };

  const renderProject = ({ item: project }: { item: any }) => (
    <Card style={styles.card} onPress={() => router.push(`/projects/${project.id}`)}>
      <Card.Cover
        source={{ uri: project.icon || 'https://via.placeholder.com/100' }}
        style={styles.icon}
      />
      <Card.Content>
        <Title>{project.name}</Title>
        <Paragraph numberOfLines={1}>{project.url}</Paragraph>
        <Paragraph style={styles.packageName}>{project.packageName}</Paragraph>
      </Card.Content>
      <Card.Actions>
        <IconButton icon="open-in-new" onPress={() => router.push(`/projects/${project.id}`)} />
        <IconButton icon="delete" onPress={() => handleDelete(project.id)} disabled={isLoading} />
      </Card.Actions>
    </Card>
  );

  return (
    <View style={[styles.container, isDarkMode && styles.darkContainer]}>
      <FlatList
        data={projects}
        keyExtractor={(item) => item.id}
        renderItem={renderProject}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Paragraph>No projects yet.</Paragraph>
            <Paragraph>Tap + to create your first app.</Paragraph>
          </View>
        }
      />

      <FAB icon="plus" style={styles.fab} onPress={() => router.push('/create')} label="Create App" />

      <IconButton icon="cog" size={24} style={styles.settingsBtn} onPress={() => router.push('/settings')} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  darkContainer: { backgroundColor: '#121212' },
  list: { padding: 16 },
  card: { marginBottom: 16, elevation: 2 },
  icon: { height: 100, width: 100, alignSelf: 'center', marginTop: 16 },
  packageName: { fontSize: 12, color: '#666', marginTop: 4 },
  fab: { position: 'absolute', right: 16, bottom: 16 },
  settingsBtn: { position: 'absolute', right: 16, top: 16 },
  empty: { marginTop: 100, alignItems: 'center' },
});