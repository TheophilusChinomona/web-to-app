import React, { useState } from 'react';
import {
  View,
  TextInput,
  ScrollView,
  StyleSheet,
  Alert,
  Platform,
} from 'react-native';
import {
  Button,
  Card,
  Checkbox,
  HelperText,
  Divider,
  Text as PaperText,
} from 'react-native-paper';
import { useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import { v4 as uuidv4 } from 'uuid';
import * as FileSystem from 'expo-file-system';
import { GeneratorService } from '../services/GeneratorService';
import { useProjects } from '../hooks/useProjects';
import type { ProjectConfig } from '../types';

type Step = 'basic' | 'appearance' | 'features' | 'confirm';

export default function CreateScreen() {
  const router = useRouter();
  const { addProject } = useProjects();

  const [step, setStep] = useState<Step>('basic');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [formData, setFormData] = useState({
    name: '',
    url: '',
    packageName: 'com.example.app',
    version: '1.0.0',
    icon: null as string | null,
    splash: null as string | null,
    features: {
      splashEnabled: true,
      bgmEnabled: false,
      bgmUrl: '',
      translationEnabled: false,
      extensions: [] as string[],
    },
  });

  const steps: Step[] = ['basic', 'appearance', 'features', 'confirm'];
  const currentStepIndex = steps.indexOf(step);

  const validateBasic = () => {
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim()) newErrors.name = 'App name is required';
    if (!formData.url.trim()) newErrors.url = 'URL is required';
    if (!/^https?:\/\//i.test(formData.url)) {
      newErrors.url = 'URL must start with http:// or https://';
    }
    if (!/^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+[a-z0-9_]$/i.test(formData.packageName)) {
      newErrors.packageName = 'Invalid package name (e.g., com.example.app)';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      const base64 = await fetch(result.assets[0].uri)
        .then(r => r.blob())
        .then(blob => new Promise<string>((resolve, reject) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result as string);
          reader.onerror = reject;
          reader.readAsDataURL(blob);
        }));
      setFormData(prev => ({ ...prev, icon: base64 }));
    }
  };

  const handleNext = () => {
    if (step === 'basic' && !validateBasic()) return;
    const nextIndex = currentStepIndex + 1;
    if (nextIndex < steps.length) {
      setStep(steps[nextIndex]);
    }
  };

  const handleBack = () => {
    const prevIndex = currentStepIndex - 1;
    if (prevIndex >= 0) {
      setStep(steps[prevIndex]);
    } else {
      router.back();
    }
  };

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const projectId = uuidv4();
      const config: ProjectConfig = {
        id: projectId,
        name: formData.name,
        url: formData.url,
        packageName: formData.packageName,
        version: formData.version,
        icon: formData.icon,
        splash: formData.splash,
        features: formData.features,
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };

      await addProject(config);

      const outputDir = \`\${FileSystem.documentDirectory}\${projectId}\`;
      await GeneratorService.generateProject(config, outputDir);

      Alert.alert('Success!', 'App generated. Check your documents folder.', [
        { text: 'OK', onPress: () => router.push(\`/projects/\${projectId}\`) },
      ]);
    } catch (error) {
      console.error(error);
      Alert.alert('Error', 'Failed to generate app. Check console.');
    } finally {
      setLoading(false);
    }
  };

  const renderBasicStep = () => (
    <View style={styles.step}>
      <PaperText variant="headlineSmall">Basic Information</PaperText>
      <TextInput
        label="App Name"
        value={formData.name}
        onChangeText={(text) => setFormData(prev => ({ ...prev, name: text }))}
        mode="outlined"
        error={!!errors.name}
        style={styles.input}
      />
      {errors.name && <HelperText type="error">{errors.name}</HelperText>}

      <TextInput
        label="Website URL"
        value={formData.url}
        onChangeText={(text) => setFormData(prev => ({ ...prev, url: text }))}
        mode="outlined"
        error={!!errors.url}
        style={styles.input}
        autoCapitalize="none"
        keyboardType="url"
      />
      {errors.url && <HelperText type="error">{errors.url}</HelperText>}

      <TextInput
        label="Package Name (Android)"
        value={formData.packageName}
        onChangeText={(text) => setFormData(prev => ({ ...prev, packageName: text }))}
        mode="outlined"
        error={!!errors.packageName}
        style={styles.input}
        autoCapitalize="none"
      />
      {errors.packageName && <HelperText type="error">{errors.packageName}</HelperText>}

      <TextInput
        label="Version"
        value={formData.version}
        onChangeText={(text) => setFormData(prev => ({ ...prev, version: text }))}
        mode="outlined"
        style={styles.input}
      />
    </View>
  );

  const renderAppearanceStep = () => (
    <View style={styles.step}>
      <PaperText variant="headlineSmall">Appearance</PaperText>
      <Button mode="outlined" onPress={pickImage} icon="image">
        {formData.icon ? 'Change Icon' : 'Select App Icon'}
      </Button>
      {formData.icon && <HelperText type="info">Icon selected</HelperText>}
      <Divider style={styles.divider} />
      <Button mode="outlined" icon="wallpaper" onPress={() => {}}>
        Select Splash Screen (optional)
      </Button>
    </View>
  );

  const renderFeaturesStep = () => (
    <View style={styles.step}>
      <PaperText variant="headlineSmall">Features</PaperText>

      <Card style={styles.featureCard}>
        <Card.Title title="Splash Screen" />
        <Card.Content>
          <View style={styles.checkboxRow}>
            <Checkbox
              status={formData.features.splashEnabled ? 'checked' : 'unchecked'}
              onPress={() =>
                setFormData(prev => ({
                  ...prev,
                  features: { ...prev.features, splashEnabled: !prev.features.splashEnabled },
                }))
              }
            />
            <PaperText>Show splash on launch</PaperText>
          </View>
        </Card.Content>
      </Card>

      <Card style={styles.featureCard}>
        <Card.Title title="Background Music" />
        <Card.Content>
          <Checkbox
            status={formData.features.bgmEnabled ? 'checked' : 'unchecked'}
            onPress={() =>
              setFormData(prev => ({
                ...prev,
                features: { ...prev.features, bgmEnabled: !prev.features.bgmEnabled },
              }))
            }
          />
          <TextInput
            label="BGM URL (MP3)"
            value={formData.features.bgmUrl}
            onChangeText={(text) =>
              setFormData(prev => ({
                ...prev,
                features: { ...prev.features, bgmUrl: text },
              }))
            }
            mode="outlined"
            style={styles.input}
            disabled={!formData.features.bgmEnabled}
          />
        </Card.Content>
      </Card>

      <Card style={styles.featureCard}>
        <Card.Title title="Built-in Extensions" />
        <Card.Content>
          <PaperText>Coming soon: Ad blocker, Dark mode, UA spoofing</PaperText>
        </Card.Content>
      </Card>
    </View>
  );

  const renderConfirmStep = () => (
    <View style={styles.step}>
      <PaperText variant="headlineSmall">Confirm & Generate</PaperText>
      <Card>
        <Card.Content>
          <PaperText><strong>Name:</strong> {formData.name}</PaperText>
          <PaperText><strong>URL:</strong> {formData.url}</PaperText>
          <PaperText><strong>Package:</strong> {formData.packageName}</PaperText>
          <PaperText><strong>Version:</strong> {formData.version}</PaperText>
          <PaperText><strong>Icon:</strong> {formData.icon ? '✅ Set' : '❌ Default'}</PaperText>
          <PaperText><strong>Splash:</strong> {formData.features.splashEnabled ? 'Enabled' : 'Disabled'}</PaperText>
          <PaperText><strong>Extensions:</strong> {formData.features.extensions.length} selected</PaperText>
        </Card.Content>
      </Card>
      <PaperText style={styles.warning}>
        The generated Expo project will be saved to your app's documents folder.
        You can then run `npx expo start` to test it in Expo Go.
      </PaperText>
    </View>
  );

  return (
    <View style={[styles.container, { paddingBottom: 100 }]}>
      <View style={styles.stepIndicator}>
        {steps.map((s, i) => (
          <View
            key={s}
            style={[
              styles.stepDot,
              i <= currentStepIndex && styles.stepDotActive,
            ]}
          />
        ))}
      </View>

      <ScrollView style={styles.content}>
        {step === 'basic' && renderBasicStep()}
        {step === 'appearance' && renderAppearanceStep()}
        {step === 'features' && renderFeaturesStep()}
        {step === 'confirm' && renderConfirmStep()}
      </ScrollView>

      <View style={styles.buttonRow}>
        {step !== 'basic' && (
          <Button mode="text" onPress={handleBack}>Back</Button>
        )}
        {step !== 'confirm' ? (
          <Button mode="contained" onPress={handleNext} style={styles.nextBtn}>
            Next
          </Button>
        ) : (
          <Button
            mode="contained"
            onPress={handleGenerate}
            loading={loading}
            disabled={loading}
            style={styles.nextBtn}
          >
            Generate App
          </Button>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  content: { flex: 1 },
  step: { gap: 16 },
  input: { marginTop: 8 },
  divider: { marginVertical: 16 },
  featureCard: { marginBottom: 16 },
  checkboxRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  stepIndicator: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 16,
    gap: 8,
  },
  stepDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#ccc',
  },
  stepDotActive: { backgroundColor: '#6750A4' },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    padding: 16,
    gap: 12,
  },
  nextBtn: { minWidth: 120 },
  warning: {
    color: '#d32f2f',
    fontSize: 12,
    marginTop: 16,
    fontStyle: 'italic',
  },
});