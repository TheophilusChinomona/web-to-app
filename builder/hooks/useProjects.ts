import { create } from 'zustand';
import { ProjectConfig } from '../types';
import { StorageService } from '../services/StorageService';

interface ProjectsState {
  projects: ProjectConfig[];
  isLoading: boolean;
  loadProjects: () => Promise<void>;
  addProject: (project: ProjectConfig) => Promise<void>;
  updateProject: (project: ProjectConfig) => Promise<void>;
  deleteProject: (id: string) => Promise<void>;
}

export const useProjects = create<ProjectsState>((set) => ({
  projects: [],
  isLoading: false,

  loadProjects: async () => {
    set({ isLoading: true });
    const projects = await StorageService.getProjects();
    set({ projects, isLoading: false });
  },

  addProject: async (project) => {
    await StorageService.saveProject(project);
    set((state) => ({ projects: [...state.projects, project] }));
  },

  updateProject: async (project) => {
    await StorageService.saveProject(project);
    set((state) => ({
      projects: state.projects.map((p) => (p.id === project.id ? project : p)),
    }));
  },

  deleteProject: async (id) => {
    await StorageService.deleteProject(id);
    set((state) => ({
      projects: state.projects.filter((p) => p.id !== id),
    }));
  },
}));
