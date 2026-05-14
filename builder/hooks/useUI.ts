import { create } from 'zustand';

interface UIState {
  isDarkMode: boolean;
  toggleTheme: () => void;
}

export const useUI = create<UIState>((set) => ({
  isDarkMode: false,
  toggleTheme: () => set((state) => ({ isDarkMode: !state.isDarkMode })),
}));
