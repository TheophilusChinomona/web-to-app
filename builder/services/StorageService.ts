import { ProjectConfig } from '../types';
const FileSystem = require('expo-file-system') as any;

const PROJECTS_FILE = `${FileSystem.documentDirectory}projects.json`;

export const StorageService = {
  async getProjects(): Promise<ProjectConfig[]> {
    try {
      const exists = await FileSystem.getInfoAsync(PROJECTS_FILE);
      if (!exists.exists) return [];
      const content = await FileSystem.readAsStringAsync(PROJECTS_FILE);
      return JSON.parse(content);
    } catch (error) {
      console.error('Failed to read projects:', error);
      return [];
    }
  },

  async saveProject(project: ProjectConfig): Promise<void> {
    const projects = await this.getProjects();
    const index = projects.findIndex((p) => p.id === project.id);
    if (index >= 0) {
      projects[index] = project;
    } else {
      projects.push(project);
    }
    await FileSystem.writeAsStringAsync(PROJECTS_FILE, JSON.stringify(projects, null, 2));
  },

  async deleteProject(id: string): Promise<void> {
    const projects = (await this.getProjects()).filter((p) => p.id !== id);
    await FileSystem.writeAsStringAsync(PROJECTS_FILE, JSON.stringify(projects, null, 2));
  },

  async getProject(id: string): Promise<ProjectConfig | null> {
    const projects = await this.getProjects();
    return projects.find((p) => p.id === id) || null;
  },
};