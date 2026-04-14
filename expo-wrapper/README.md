# Expo WebView Wrapper (iOS + Android)

This folder contains an Expo app scaffold that wraps a website in a mobile WebView with safe navigation controls.

## Features

- Expo Router based app shell
- Environment-based website URL config
- Navigation guard to keep in-app browsing on approved host(s)
- Safe external link opening (http/https/mailto/tel only)
- Loading overlay + retryable error state
- EAS build profiles for development, preview, and production

## Prerequisites

- Node.js 18+
- npm or pnpm
- Expo CLI (`npx expo` is enough)
- EAS CLI for cloud builds (`npm i -g eas-cli`)

## Setup

```bash
cd expo-wrapper
npm install
```

## Configure target website

Set the website URL before running/building:

```bash
export EXPO_PUBLIC_WEBSITE_URL="https://your-site.com"
```

The value is read from `EXPO_PUBLIC_WEBSITE_URL` and copied into Expo `extra.websiteUrl`.

## Run locally

```bash
npm run start
npm run android
npm run ios
```

## Type check

```bash
npm run typecheck
```

## EAS build profiles

`eas.json` includes:

- `development`: internal dev client builds
- `preview`: internal testing builds
- `production`: release-ready builds

Example commands:

```bash
eas build --platform android --profile preview
eas build --platform ios --profile production
```

## Key files

- `app.config.ts`: app metadata + env-driven website URL
- `app/index.tsx`: app entry screen
- `src/screens/WebViewScreen.tsx`: WebView wrapper + guards
- `src/utils/navigationGuard.ts`: internal-host navigation policy
- `src/utils/linking.ts`: external link safety checks


## Tests

```bash
npm run test
```

Current coverage targets core wrapper safety logic:
- navigation guard host/scheme enforcement
- safe external link handling
- env-based URL/host resolution
