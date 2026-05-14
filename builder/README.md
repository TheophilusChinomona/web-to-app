# WebToApp Expo Builder

A React Native (Expo) app that generates complete Expo projects from any website URL.

## Architecture

The builder itself is an Expo app (React Native) that:
- Accepts user configuration (URL, app name, icon, features)
- Generates a **standalone Expo project** (source code) to a folder
- The generated project can be opened, modified, and built with Expo Go / EAS Build

## Quick Start

```bash
cd builder
npm install
npx expo start
```

- Scan QR with Expo Go (Android/iOS) to run the builder on your device
- Or press `w` to open in web browser (Expo Web)

## Using the Builder

1. Tap **Create App**
2. Fill in:
   - **App Name** (e.g., "My Shop")
   - **Website URL** (https://...)
   - **Package Name** (Android, e.g., `com.myshop.app`)
   - **Version** (default `1.0.0`)
3. Next → optionally pick an app icon
4. Next → configure features (splash, BGM)
5. Confirm → **Generate App**

The generated project is saved to your device's documents folder (Expo FileSystem). On mobile, use a file manager to access it. On web, it's saved to IndexedDB (not directly accessible).

## Next Steps with Generated App

```bash
# Copy generated folder to your computer (via USB, cloud, etc.)
cd MyGeneratedApp
npm install
npx expo start        # Opens QR; scan with Expo Go to test
npx expo run:android  # Build standalone APK (no Android Studio)
eas build --platform android   # Or use EAS Cloud Build
```

## Modifying the Generated App

The generated project is **fully editable React Native source code**:
- Edit `App.tsx` to change WebView settings
- Add new screens in `app/`
- Customize extensions in `constants/Extensions.ts`
- Change theme in `constants/Colors.ts`

## Project Structure

```
builder/
├── app/                      # Builder UI (Expo Router)
│   ├── _layout.tsx           # Providers (Paper, Navigation)
│   ├── index.tsx             # Home: list + FAB
│   ├── create.tsx            # Multi-step wizard
│   ├── projects/
│   │   └── [id].tsx          # Project detail / actions
│   └── settings.tsx          # Theme toggle
├── services/
│   ├── GeneratorService.ts   # Core code generator
│   └── StorageService.ts     # Project config CRUD
├── hooks/
│   ├── useProjects.ts        # Zustand store
│   └── useUI.ts              # Theme state
├── templates/
│   └── base/                 # Skeleton for generated apps
│       ├── App.tsx
│       ├── app/
│       │   ├── _layout.tsx
│       │   └── webview.tsx
│       ├── app.json
│       ├── package.json
│       ├── eas.json
│       └── ...
├── extensions/               # Built-in JS modules
│   ├── ad-blocker.js
│   ├── dark-mode.js
│   └── spoof-ua.js
├── types/
│   └── index.ts              # TypeScript interfaces
├── playwright-tests/         # E2E tests
└── README.md
```

## Running E2E Tests

```bash
cd builder
npm install
npx playwright install
npm run test:e2e
```

Playwright will:
1. Start Expo web dev server on port 19006
2. Open Chromium
3. Exercise full wizard flow (create project, validation, delete)
4. Generate HTML report at `playwright-report/index.html`

## Tech Stack

- **Expo SDK 52** with TypeScript
- **Expo Router** (file-based navigation)
- **React Native Paper** (Material 3)
- **Zustand** for state
- **expo-file-system** for local persistence
- **Playwright** for E2E

## CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`):
- TypeScript type checking
- Playwright E2E suite (Chromium)

## License

MIT

---

Generated apps use the same Expo template (see `templates/base/`). You can customize the template to change default styling, add native modules, or include additional boilerplate.
