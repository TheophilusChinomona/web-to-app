# Expo Wrapper Scaffold Notes

The Expo wrapper app is scaffolded in `expo-wrapper/` as an isolated mobile layer for iOS and Android.

## What was added

- Expo app config (`app.config.ts`)
- EAS build profiles (`eas.json`)
- Router entry (`app/_layout.tsx`, `app/index.tsx`)
- WebView screen with:
  - navigation guard (internal host whitelist)
  - safe external link handling
  - loading and error states
- Environment-based website URL (`EXPO_PUBLIC_WEBSITE_URL`)
- Local run/build instructions (`expo-wrapper/README.md`)

## Next steps

1. Replace placeholder bundle/package identifiers if needed.
2. Set `EXPO_PUBLIC_WEBSITE_URL` to the production site.
3. Set real EAS project id in `app.config.ts`.
4. Run `npm install` and test on both platforms.
