export interface ProjectConfig {
  id: string;
  name: string;
  url: string;
  packageName: string;
  version: string;
  icon: string | null; // base64 PNG
  splash: string | null;
  features: {
    splashEnabled: boolean;
    bgmEnabled: boolean;
    bgmUrl?: string;
    translationEnabled: boolean;
    extensions: string[];
  };
  createdAt: number;
  updatedAt: number;
}

export interface Extension {
  id: string;
  name: string;
  description: string;
  matches: string[];
  code: string;
  enabled: boolean;
}
