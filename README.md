# WebToApp Builder

Transform any website into a standalone Expo React Native app in minutes.

## ✨ Features

- **No-code app generation** — Enter URL, configure, generate
- **Expo Go compatible** — Test immediately in Expo Go, no build needed
- **Cross-platform** — Generated apps run on Android and iOS
- **Extensible** — Built-in ad blocker, dark mode, UA spoofing
- **Customizable** — Edit generated code; fully documented
- **Production-ready** — E2E tested with Playwright

## 🚀 Quick Start

### 1. Run the Builder

```bash
cd builder
npm install
npx expo start
```

Scan QR with Expo Go (Android) or use iOS simulator.

### 2. Create Your App

1. Tap **Create App**
2. Fill in:
   - **App Name**: My Awesome App
   - **Website URL**: https://myapp.com
   - **Package Name**: com.mycompany.myapp
3. (Optional) Pick an icon, configure features
4. Generate

### 3. Open Generated App in Expo Go

1. After generation, the app is saved to the app's documents folder
2. Open terminal: `cd path/to/generated/folder`
3. Run: `npx expo start`
4. Scan the QR code with Expo Go

Your website now runs as a native app!

## 🏗️ Generated App Structure

```
MyApp/
├── App.tsx                 # Entry point
├── app/
│   ├── _layout.tsx        # Navigation layout
│   └── webview.tsx        # WebView wrapper
├── constants/
│   └── Extensions.ts      # Extension modules (editable)
├── assets/
│   ├── icon.png           # Your app icon
│   └── splash.png         # Splash screen
├── package.json
├── app.json
├── eas.json               # Build configuration
└── README.md              # Usage instructions
```

## 🔧 Customizing Generated Apps

Generated apps are **fully editable React Native code**. You can:

- Add new screens in `app/`
- Change colors in `constants/Colors.ts`
- Add more extensions (copy boilerplate from `constants/Extensions.ts`)
- Integrate native modules (camera, location) via Expo
- Deploy to stores with EAS Build

See generated `README.md` for customization guide.

## ✨ Built-in Extensions

1. **Ad Blocker** — Blocks common ad scripts/requests
2. **Dark Mode** — Forces dark color scheme
3. **User-Agent Spoof** — Spoofs Android Chrome UA

Enable/disable extensions in the generated app's `constants/Extensions.ts` or via future settings UI.

## 📦 Building Standalone APK / IPA

Once you're happy with your app:

```bash
cd MyGeneratedApp
npx eas build --platform android   # Creates AAB/APK
npx eas build --platform ios      # Creates IPA (requires Apple account)
```

Download from Expo website and distribute.

## 🛠️ Development

### Install Dependencies

```bash
cd builder
npm install
```

### Run Tests

```bash
# Unit tests
npm test

# E2E tests (Playwright)
npm run test:e2e
```

### Tech Stack

- **Expo SDK 54** with TypeScript
- **React Native Paper** — Material 3 UI
- **Zustand** — State management
- **Zod** — Validation (future)
- **Playwright** — E2E testing
- **Expo Router** — File-based routing

## 📚 How It Works

1. **User configures** app via multi-step wizard
2. **GeneratorService** writes Expo project files from embedded templates
3. **Placeholders** replaced with user config (name, URL, package, etc.)
4. **Assets** (icon, splash) copied
5. **Metadata** saved for re-generation
6. **User receives** complete, ready-to-run Expo project

## 🧪 CI / CD

GitHub Actions workflow included (`.github/workflows/test.yml`) runs:
- TypeScript type-check
- Unit tests
- E2E Playwright tests on each PR

## 🤝 Contributing

PRs welcome! Please ensure tests pass.

## 📄 License

MIT — same as original WebToApp.

---

*Built by Speccon. Original WebToApp by shiahonb777.*
