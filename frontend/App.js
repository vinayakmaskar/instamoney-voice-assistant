/**
 * Main App Component
 * Modern UI with branded header, centered form, and floating voice assistant
 */
import React, { useState } from 'react';
import { 
  SafeAreaView, 
  StatusBar, 
  StyleSheet, 
  View, 
  Text,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import BasicDetailsForm from './src/components/BasicDetailsForm';
import VoiceChatbot from './src/components/VoiceChatbot';
import { colors, spacing, typography, borderRadius } from './src/styles/theme';

export default function App() {
  const [formData, setFormData] = useState({
    fullName: '',
    panNumber: '',
    dateOfBirth: '',
    state: '',
    preferredLanguage: '',
  });
  
  const [validationResults, setValidationResults] = useState({});
  
  const handleFormUpdate = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };
  
  const handleValidationResult = (field, isValid, message) => {
    setValidationResults(prev => ({
      ...prev,
      [field]: { isValid, message },
    }));
  };

  const filledCount = Object.values(formData).filter(v => v && v.trim()).length;

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={colors.background} />
      
      <LinearGradient
        colors={[colors.backgroundGradientStart, colors.backgroundGradientEnd, colors.backgroundGradientStart]}
        style={StyleSheet.absoluteFill}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      />
      
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.content}>
          {/* Header */}
          <View style={styles.header}>
            <View style={styles.logoRow}>
              <LinearGradient
                colors={[colors.gradientStart, colors.gradientEnd]}
                style={styles.logoIcon}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Text style={styles.logoIconText}>IM</Text>
              </LinearGradient>
              <View>
                <Text style={styles.logo}>InstaMoney</Text>
                <Text style={styles.subtitle}>Loan Application</Text>
              </View>
            </View>
            
            {/* Completion pill */}
            <View style={[
              styles.completionPill,
              filledCount === 5 && styles.completionPillDone,
            ]}>
              <Text style={[
                styles.completionText,
                filledCount === 5 && styles.completionTextDone,
              ]}>
                {filledCount}/5
              </Text>
            </View>
          </View>
          
          {/* Form */}
          <View style={styles.formWrapper}>
            <BasicDetailsForm 
              formData={formData}
              onFormUpdate={handleFormUpdate}
              validationResults={validationResults}
            />
          </View>
        </View>
        
        {/* Floating Voice Button */}
        <VoiceChatbot 
          onFormUpdate={handleFormUpdate}
          onValidationResult={handleValidationResult}
        />
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  safeArea: {
    flex: 1,
  },
  content: {
    flex: 1,
    paddingHorizontal: spacing.lg,
    paddingTop: Platform.OS === 'web' ? spacing.xl : spacing.md,
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    width: '100%',
    maxWidth: 480,
    marginBottom: spacing.xl,
    paddingHorizontal: spacing.xs,
  },
  logoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  logoIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoIconText: {
    fontSize: 16,
    fontWeight: '800',
    color: '#fff',
    letterSpacing: -0.5,
  },
  logo: {
    fontSize: typography.sizes.xl,
    fontWeight: '700',
    color: colors.textPrimary,
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: typography.sizes.sm,
    color: colors.textMuted,
    marginTop: 1,
  },
  completionPill: {
    backgroundColor: colors.glass,
    borderWidth: 1,
    borderColor: colors.glassBorder,
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: borderRadius.round,
  },
  completionPillDone: {
    backgroundColor: colors.successGlow,
    borderColor: colors.success,
  },
  completionText: {
    fontSize: typography.sizes.sm,
    fontWeight: '700',
    color: colors.textSecondary,
  },
  completionTextDone: {
    color: colors.success,
  },
  formWrapper: {
    flex: 1,
    width: '100%',
    maxWidth: 480,
  },
});
