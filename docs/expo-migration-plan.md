# WebToApp Migration Plan: Android-Native Path vs Expo Cross-Platform Wrapper

## 1) Executive summary
- Current path is Android-only, deeply native, and optimized for feature breadth on Android.
- Expo wrapper path gives fast iOS + Android coverage and easier release velocity, but with reduced low-level device/control features.
- Recommendation: run a phased dual-track strategy, ship a stable Expo MVP for cross-platform reach, keep Android-native for advanced/power features until parity is proven.

## 2) Current state (Android-native path)
Based on this repo:
- Platform: Android app module (`app/`) with Kotlin + Jetpack Compose.
- Runtime: Android WebView shell activities (`WebViewActivity`, `ShellActivity`) plus service-heavy background model.
- Permissions/profile: broad Android permission surface (camera, mic, location, bluetooth, NFC, sensors, storage, telephony, foreground services, boot receivers, etc.).
- Build/distribution: Gradle, native C/C++ components (NDK/CMake), APK generation/signing flows.
- Deep links/auth: custom scheme callback already present (`com.webtoapp://oauth2callback`).

## 3) Target state (Expo wrapper path)
- Platform: single React Native + Expo codebase.
- Runtime: Web content hosted in `react-native-webview` inside Expo app shell.
- Distribution: EAS Build/Submit for Android + iOS.
- Native reach: use Expo modules first, add config plugins/custom dev client only when required.

## 4) Architecture comparison
| Area | Current Android-native | Expo wrapper target |
|---|---|---|
| Platform coverage | Android only | Android + iOS from one codebase |
| Native control | Very high (manifest/services/receivers/NDK) | Medium by default, high only after eject/custom plugins |
| Time to iOS | High (new codebase needed) | Low-medium (same app shell) |
| Web wrapper core | Android WebView activities | RN WebView component |
| Release ops | Gradle/manual pipelines | EAS-managed pipelines |
| Background behaviors | Extensive foreground/background service patterns | Limited, iOS-constrained, policy-gated |
| Permission scope | Broad and device-level | Must be narrowed for App Store acceptance |

## 5) Compatibility implications (Apple + Android)

### iOS implications
- iOS will reject Android-style broad permissions and persistent background patterns unless clearly justified.
- Certain capabilities in current Android path (boot receivers, many foreground service modes, unrestricted background persistence) do not map to iOS.
- Must provide purpose strings for each used permission and keep permission requests minimal/contextual.

### Android implications
- Expo can cover standard camera/location/notifications/deep links and WebView wrappers.
- Advanced Android behaviors (special-use foreground service, low-level hardware hooks, boot-time behaviors, some package-level integrations) likely require custom native modules or remain Android-native only.

## 6) Feature gap matrix

### Likely retained in Expo MVP
- URL wrapper in app shell
- Basic navigation controls
- Standard permission-gated web features (camera/mic/location where supported)
- Deep links and OAuth callback handling
- Push notifications (with backend changes)

### Likely partial or deferred
- Heavy background keep-alive patterns
- Broad device/hardware integrations (NFC/Bluetooth edge cases/sensor-heavy features)
- Native binary toolchain features tied to in-app APK generation model
- Some extension/module injection patterns that rely on Android-specific internals

### Likely Android-native only (until dedicated native work)
- Boot receivers and always-on guard behavior
- Special foreground service subtypes and policy-sensitive persistence
- Full parity with current manifest-level capability breadth

## 7) Push notifications strategy
- Use `expo-notifications` for token registration and delivery.
- Introduce a provider abstraction on backend:
  - Android: FCM
  - iOS: APNs via Expo push service or direct provider pipeline
- Migration steps:
  1. Add device registration endpoint with platform + app version + environment.
  2. Dual-send support during transition (native Android + Expo clients).
  3. Standardize payload schema (title/body/data/deepLink).
  4. Add delivery/receipt telemetry and token cleanup job.

## 8) Deep links strategy
- Keep existing OAuth callback semantics but normalize to universal design:
  - Custom scheme for dev/backward compatibility.
  - Universal Links (iOS) + App Links (Android) for production-grade routing.
- Define one routing contract: `app://route` and HTTPS deep links mapped to same internal route names.
- Add fallback logic when app not installed.

## 9) Auth and session handling
- Use secure storage abstraction:
  - Expo SecureStore for tokens
  - Cookie strategy in WebView (shared where possible, explicit refresh flow otherwise)
- Recommended approach:
  1. Move to backend-issued short-lived access token + refresh token.
  2. Keep OAuth completion in system browser/deep-link callback.
  3. On callback, exchange code server-side; store only required client secrets securely.
  4. Add forced logout/session invalidation endpoint for parity with current controls.

## 10) Offline strategy
- Phase 1: baseline offline UX (error state, retry, cached last successful page/skeleton).
- Phase 2: selective offline support via local cache/API sync for key screens, not full site mirror.
- Phase 3: optional content bundles for known static assets where business-critical.

## 11) Store submission considerations

### Apple App Store
- Biggest risk: being seen as “just a website wrapper.”
- Mitigations:
  - Add meaningful native value (notifications, share sheet, saved items/offline, device integration with clear utility).
  - Tighten permissions to only what is used.
  - Clear privacy policy, data usage disclosures, and account deletion flow if login exists.

### Google Play
- Enforce scoped permissions and background behavior compliance.
- Avoid policy-sensitive permission declarations unless essential and user-visible.

## 12) Phased rollout plan

### Phase 0, Discovery and contract freeze (1 week)
- Define feature parity target (MVP vs advanced).
- Freeze deep-link, notification, and auth contracts.
- Identify Android-native-only features to keep out of MVP.

### Phase 1, Expo foundation (1 to 2 weeks)
- Create Expo app shell + WebView wrapper.
- Implement deep-link routing, auth callback, secure token storage.
- Add analytics, crash reporting, and feature flags.

### Phase 2, Core parity MVP (2 to 3 weeks)
- Notifications end-to-end.
- Permission prompts only in-context.
- Offline baseline UX.
- Internal QA matrix across iOS + Android devices.

### Phase 3, Beta and policy hardening (1 to 2 weeks)
- TestFlight + Play Internal Testing.
- Fix review blockers, privacy disclosures, and edge-case auth/session bugs.
- Prepare store metadata/screenshots/compliance text.

### Phase 4, Controlled production rollout (1 week)
- Gradual rollout by cohort.
- Keep Android-native channel active as fallback for advanced users.
- Monitor crash-free rate, login success, push delivery, retention.

### Phase 5, Decision gate
- If Expo KPIs meet targets, expand and deprecate parts of Android-native path.
- If not, keep dual-track: Expo for broad distribution, native Android for advanced feature tier.

## 13) Recommended go/no-go criteria
- Go for Expo MVP if top priority is cross-platform growth and faster release cycles.
- Stay Android-native-first if priority is deep device control and advanced background/system behaviors.
- Most practical near-term path: dual-track with explicit feature tiering and a clear deprecation gate.
