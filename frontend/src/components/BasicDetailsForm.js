/**
 * Basic Details Form Component
 * Modern Glassmorphism Design with Field Icons and Status Indicators
 */
import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Animated,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, spacing, borderRadius, shadows, typography } from '../styles/theme';

const FIELD_ICONS = {
  fullName: '\u{1F464}',
  panNumber: '\u{1F4B3}',
  dateOfBirth: '\u{1F4C5}',
  state: '\u{1F4CD}',
  preferredLanguage: '\u{1F310}',
};

const CARD_BG = '#16162a';

const FloatingLabelInput = ({ 
  label, 
  value, 
  onChangeText, 
  placeholder,
  keyboardType,
  maxLength,
  autoCapitalize,
  isValid,
  validationMessage,
  icon,
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const animatedValue = useRef(new Animated.Value(value ? 1 : 0)).current;
  
  useEffect(() => {
    Animated.timing(animatedValue, {
      toValue: isFocused || value ? 1 : 0,
      duration: 200,
      useNativeDriver: false,
    }).start();
  }, [isFocused, value]);
  
  const hasValue = value && value.trim();
  
  const labelStyle = {
    position: 'absolute',
    left: icon ? 48 : spacing.md,
    top: animatedValue.interpolate({
      inputRange: [0, 1],
      outputRange: [17, -10],
    }),
    fontSize: animatedValue.interpolate({
      inputRange: [0, 1],
      outputRange: [14, 11],
    }),
    color: animatedValue.interpolate({
      inputRange: [0, 1],
      outputRange: [colors.placeholder, isFocused ? colors.accent : colors.textSecondary],
    }),
    backgroundColor: animatedValue.interpolate({
      inputRange: [0, 1],
      outputRange: ['transparent', CARD_BG],
    }),
    paddingHorizontal: animatedValue.interpolate({
      inputRange: [0, 1],
      outputRange: [0, 6],
    }),
    zIndex: 2,
  };
  
  const getBorderColor = () => {
    if (isValid === true) return colors.success;
    if (isValid === false) return colors.error;
    if (isFocused) return colors.accent;
    if (hasValue) return colors.fieldFilledBorder;
    return colors.inputBorder;
  };
  
  const getBackgroundColor = () => {
    if (hasValue && !isFocused) return colors.fieldFilled;
    return colors.inputBackground;
  };

  return (
    <View style={styles.inputContainer}>
      <Animated.Text style={labelStyle}>{label}</Animated.Text>
      <View style={styles.inputRow}>
        {icon && (
          <View style={[
            styles.iconContainer,
            isFocused && styles.iconContainerActive,
            hasValue && !isFocused && styles.iconContainerFilled,
          ]}>
            <Text style={styles.fieldIcon}>{icon}</Text>
          </View>
        )}
        <TextInput
          style={[
            styles.input,
            { 
              borderColor: getBorderColor(),
              backgroundColor: getBackgroundColor(),
              paddingLeft: icon ? 48 : spacing.md,
            },
            isFocused && styles.inputFocused,
          ]}
          value={value}
          onChangeText={onChangeText}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder={isFocused ? placeholder : ''}
          placeholderTextColor={colors.placeholder}
          keyboardType={keyboardType}
          maxLength={maxLength}
          autoCapitalize={autoCapitalize}
        />
        {hasValue && (
          <View style={styles.checkBadge}>
            <Text style={styles.checkIcon}>{'\u2713'}</Text>
          </View>
        )}
      </View>
      {validationMessage && (
        <View style={styles.validationContainer}>
          <Text style={[
            styles.validationText,
            { color: isValid ? colors.success : colors.error }
          ]}>
            {isValid ? '\u2713' : '\u2717'} {validationMessage}
          </Text>
        </View>
      )}
    </View>
  );
};

const CustomDropdown = ({ label, value, options, onValueChange, placeholder, icon }) => {
  const [isOpen, setIsOpen] = useState(false);
  const animatedValue = useRef(new Animated.Value(value ? 1 : 0)).current;
  
  const selectedLabel = options.find(opt => opt.value === value)?.label || '';
  const hasValue = !!value;
  const isActive = isOpen || hasValue;

  useEffect(() => {
    Animated.timing(animatedValue, {
      toValue: isActive ? 1 : 0,
      duration: 200,
      useNativeDriver: false,
    }).start();
  }, [isActive]);

  const labelStyle = {
    position: 'absolute',
    left: icon ? 48 : spacing.md,
    top: animatedValue.interpolate({
      inputRange: [0, 1],
      outputRange: [17, -10],
    }),
    fontSize: animatedValue.interpolate({
      inputRange: [0, 1],
      outputRange: [14, 11],
    }),
    color: animatedValue.interpolate({
      inputRange: [0, 1],
      outputRange: [colors.placeholder, isOpen ? colors.accent : colors.textSecondary],
    }),
    backgroundColor: animatedValue.interpolate({
      inputRange: [0, 1],
      outputRange: ['transparent', CARD_BG],
    }),
    paddingHorizontal: animatedValue.interpolate({
      inputRange: [0, 1],
      outputRange: [0, 6],
    }),
    zIndex: 2,
  };

  return (
    <View style={[styles.inputContainer, { zIndex: isOpen ? 100 : 1 }]}>
      <Animated.Text style={labelStyle}>{label}</Animated.Text>
      <TouchableOpacity
        style={[
          styles.dropdown,
          { 
            borderColor: isOpen ? colors.accent : hasValue ? colors.fieldFilledBorder : colors.inputBorder,
            backgroundColor: hasValue && !isOpen ? colors.fieldFilled : colors.inputBackground,
          },
          isOpen && styles.inputFocused,
        ]}
        onPress={() => setIsOpen(!isOpen)}
        activeOpacity={0.7}
      >
        {icon && (
          <View style={[
            styles.dropdownIcon,
            isOpen && styles.iconContainerActive,
            hasValue && !isOpen && styles.iconContainerFilled,
          ]}>
            <Text style={styles.fieldIcon}>{icon}</Text>
          </View>
        )}
        <Text style={[
          styles.dropdownText,
          !hasValue && styles.dropdownPlaceholder,
          { marginLeft: icon ? 36 : 0 },
        ]}>
          {hasValue ? selectedLabel : (isOpen ? placeholder : '')}
        </Text>
        <View style={styles.dropdownRight}>
          {hasValue && (
            <View style={styles.checkBadgeSmall}>
              <Text style={styles.checkIcon}>{'\u2713'}</Text>
            </View>
          )}
          <Text style={[styles.dropdownArrow, isOpen && styles.dropdownArrowOpen]}>
            {'\u25BE'}
          </Text>
        </View>
      </TouchableOpacity>
      
      {isOpen && (
        <View style={styles.dropdownOptions}>
          <ScrollView style={styles.dropdownScroll} nestedScrollEnabled>
            {options.map((option, index) => (
              <TouchableOpacity
                key={option.value}
                style={[
                  styles.dropdownOption,
                  value === option.value && styles.dropdownOptionSelected,
                  index === options.length - 1 && { borderBottomWidth: 0 },
                ]}
                onPress={() => {
                  onValueChange(option.value);
                  setIsOpen(false);
                }}
                activeOpacity={0.6}
              >
                <Text style={[
                  styles.dropdownOptionText,
                  value === option.value && styles.dropdownOptionTextSelected,
                ]}>
                  {option.label}
                </Text>
                {value === option.value && (
                  <Text style={styles.dropdownCheckmark}>{'\u2713'}</Text>
                )}
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}
    </View>
  );
};

const ProgressIndicator = ({ fields, formData }) => {
  const filledCount = Object.values(formData).filter(v => v && v.trim()).length;
  const progress = filledCount / fields.length;
  
  return (
    <View style={styles.progressContainer}>
      <View style={styles.progressBarBg}>
        <LinearGradient
          colors={progress === 1 ? [colors.success, '#10b981'] : [colors.gradientStart, colors.gradientEnd]}
          style={[styles.progressBarFill, { width: `${Math.max(progress * 100, 2)}%` }]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
        />
      </View>
    </View>
  );
};

const BasicDetailsForm = ({ formData: propFormData, onFormUpdate, validationResults = {} }) => {
  const [localFormData, setLocalFormData] = useState({
    fullName: '',
    panNumber: '',
    dateOfBirth: '',
    state: '',
    preferredLanguage: '',
  });
  
  const formData = propFormData || localFormData;
  
  const handleInputChange = (field, value) => {
    if (onFormUpdate) {
      onFormUpdate(field, value);
    } else {
      setLocalFormData(prev => ({ ...prev, [field]: value }));
    }
  };

  const states = [
    { label: 'Andhra Pradesh', value: 'andhra_pradesh' },
    { label: 'Arunachal Pradesh', value: 'arunachal_pradesh' },
    { label: 'Assam', value: 'assam' },
    { label: 'Bihar', value: 'bihar' },
    { label: 'Chhattisgarh', value: 'chhattisgarh' },
    { label: 'Goa', value: 'goa' },
    { label: 'Gujarat', value: 'gujarat' },
    { label: 'Haryana', value: 'haryana' },
    { label: 'Himachal Pradesh', value: 'himachal_pradesh' },
    { label: 'Jharkhand', value: 'jharkhand' },
    { label: 'Karnataka', value: 'karnataka' },
    { label: 'Kerala', value: 'kerala' },
    { label: 'Madhya Pradesh', value: 'madhya_pradesh' },
    { label: 'Maharashtra', value: 'maharashtra' },
    { label: 'Manipur', value: 'manipur' },
    { label: 'Meghalaya', value: 'meghalaya' },
    { label: 'Mizoram', value: 'mizoram' },
    { label: 'Nagaland', value: 'nagaland' },
    { label: 'Odisha', value: 'odisha' },
    { label: 'Punjab', value: 'punjab' },
    { label: 'Rajasthan', value: 'rajasthan' },
    { label: 'Sikkim', value: 'sikkim' },
    { label: 'Tamil Nadu', value: 'tamil_nadu' },
    { label: 'Telangana', value: 'telangana' },
    { label: 'Tripura', value: 'tripura' },
    { label: 'Uttar Pradesh', value: 'uttar_pradesh' },
    { label: 'Uttarakhand', value: 'uttarakhand' },
    { label: 'West Bengal', value: 'west_bengal' },
  ];

  const languages = [
    { label: 'English', value: 'en' },
    { label: 'Hindi', value: 'hi' },
    { label: 'Marathi', value: 'mr' },
    { label: 'Tamil', value: 'ta' },
    { label: 'Telugu', value: 'te' },
    { label: 'Bengali', value: 'bn' },
    { label: 'Gujarati', value: 'gu' },
    { label: 'Kannada', value: 'kn' },
    { label: 'Malayalam', value: 'ml' },
    { label: 'Punjabi', value: 'pa' },
  ];

  const fields = ['fullName', 'panNumber', 'dateOfBirth', 'state', 'preferredLanguage'];

  return (
    <View style={styles.container}>
      <ScrollView 
        style={styles.scrollView} 
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.glassCard}>
          {/* Step Header */}
          <View style={styles.stepHeader}>
            <View style={styles.stepIndicator}>
              <LinearGradient
                colors={[colors.gradientStart, colors.gradientEnd]}
                style={styles.stepBadge}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
              >
                <Text style={styles.stepNumber}>1</Text>
              </LinearGradient>
              <View style={styles.stepTextContainer}>
                <Text style={styles.stepLabel}>STEP 1 OF 2</Text>
                <Text style={styles.stepTitle}>Basic Details</Text>
              </View>
            </View>
          </View>
          
          <ProgressIndicator fields={fields} formData={formData} />
          
          {/* Voice hint */}
          <View style={styles.voiceHint}>
            <Text style={styles.voiceHintIcon}>{'\u{1F3A4}'}</Text>
            <Text style={styles.voiceHintText}>
              Tap the mic button to fill this form using your voice
            </Text>
          </View>
          
          <View style={styles.divider} />
          
          {/* Form Fields */}
          <View style={styles.formFields}>
            <FloatingLabelInput
              label="Full Name as per PAN"
              value={formData.fullName}
              onChangeText={(value) => handleInputChange('fullName', value)}
              placeholder="Enter your full name"
              autoCapitalize="words"
              icon={FIELD_ICONS.fullName}
            />
            
            <FloatingLabelInput
              label="PAN Number"
              value={formData.panNumber}
              onChangeText={(value) => handleInputChange('panNumber', value.toUpperCase())}
              placeholder="ABCDE1234F"
              maxLength={10}
              autoCapitalize="characters"
              isValid={validationResults.panNumber?.isValid}
              validationMessage={validationResults.panNumber?.message}
              icon={FIELD_ICONS.panNumber}
            />
            
            <FloatingLabelInput
              label="Date of Birth"
              value={formData.dateOfBirth}
              onChangeText={(value) => handleInputChange('dateOfBirth', value)}
              placeholder="DD/MM/YYYY"
              keyboardType="numeric"
              isValid={validationResults.dateOfBirth?.isValid}
              validationMessage={validationResults.dateOfBirth?.message}
              icon={FIELD_ICONS.dateOfBirth}
            />
            
            <CustomDropdown
              label="State"
              value={formData.state}
              options={states}
              onValueChange={(value) => handleInputChange('state', value)}
              placeholder="Select your state"
              icon={FIELD_ICONS.state}
            />
            
            <CustomDropdown
              label="Preferred Language"
              value={formData.preferredLanguage}
              options={languages}
              onValueChange={(value) => handleInputChange('preferredLanguage', value)}
              placeholder="Select language"
              icon={FIELD_ICONS.preferredLanguage}
            />
          </View>
          
          {/* Submit Button */}
          <TouchableOpacity style={styles.submitButton} activeOpacity={0.8}>
            <LinearGradient
              colors={[colors.gradientStart, colors.gradientEnd]}
              style={styles.submitButtonGradient}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
            >
              <Text style={styles.submitButtonText}>Continue</Text>
              <Text style={styles.submitButtonArrow}>{'\u2192'}</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    paddingBottom: 120,
  },
  glassCard: {
    backgroundColor: CARD_BG,
    borderWidth: 1,
    borderColor: colors.glassBorder,
    borderRadius: borderRadius.xl,
    padding: spacing.xl,
    ...shadows.glass,
  },
  stepHeader: {
    marginBottom: spacing.md,
  },
  stepIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  stepBadge: {
    width: 42,
    height: 42,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: spacing.md,
  },
  stepNumber: {
    fontSize: typography.sizes.lg,
    fontWeight: '800',
    color: '#fff',
  },
  stepTextContainer: {
    flex: 1,
  },
  stepLabel: {
    fontSize: typography.sizes.xs,
    color: colors.textMuted,
    letterSpacing: 1.5,
    fontWeight: '600',
    marginBottom: 2,
  },
  stepTitle: {
    fontSize: typography.sizes.xl,
    fontWeight: '700',
    color: colors.textPrimary,
    letterSpacing: -0.3,
  },
  progressContainer: {
    marginBottom: spacing.md,
  },
  progressBarBg: {
    height: 4,
    backgroundColor: colors.inputBackground,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 2,
  },
  voiceHint: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.accentGlow,
    borderRadius: borderRadius.sm,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: spacing.md,
    gap: 8,
  },
  voiceHintIcon: {
    fontSize: 14,
  },
  voiceHintText: {
    fontSize: typography.sizes.sm,
    color: colors.accentLight,
    flex: 1,
  },
  divider: {
    height: 1,
    backgroundColor: colors.glassBorder,
    marginBottom: spacing.lg,
  },
  formFields: {
    gap: 2,
  },
  inputContainer: {
    marginBottom: spacing.lg,
    position: 'relative',
  },
  inputRow: {
    position: 'relative',
  },
  iconContainer: {
    position: 'absolute',
    left: 14,
    top: 0,
    bottom: 0,
    width: 28,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1,
    opacity: 0.4,
  },
  dropdownIcon: {
    width: 28,
    alignItems: 'center',
    justifyContent: 'center',
    opacity: 0.4,
    marginRight: 8,
  },
  iconContainerActive: {
    opacity: 0.9,
  },
  iconContainerFilled: {
    opacity: 0.6,
  },
  fieldIcon: {
    fontSize: 16,
  },
  checkBadge: {
    position: 'absolute',
    right: 14,
    top: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkBadgeSmall: {
    marginRight: 4,
  },
  checkIcon: {
    fontSize: 14,
    color: colors.success,
    fontWeight: '700',
  },
  input: {
    borderWidth: 1,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: 16,
    fontSize: typography.sizes.md,
    color: colors.textPrimary,
    minHeight: 54,
  },
  inputFocused: {
    borderWidth: 1.5,
  },
  validationContainer: {
    marginTop: spacing.xs,
    paddingLeft: 4,
  },
  validationText: {
    fontSize: typography.sizes.xs,
  },
  dropdown: {
    borderWidth: 1,
    borderRadius: borderRadius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: 16,
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: 54,
  },
  dropdownText: {
    fontSize: typography.sizes.md,
    color: colors.textPrimary,
    flex: 1,
  },
  dropdownPlaceholder: {
    color: colors.placeholder,
  },
  dropdownRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  dropdownArrow: {
    fontSize: 16,
    color: colors.textMuted,
  },
  dropdownArrowOpen: {
    transform: [{ rotate: '180deg' }],
  },
  dropdownOptions: {
    position: 'absolute',
    top: '100%',
    left: 0,
    right: 0,
    backgroundColor: '#1a1a32',
    borderWidth: 1,
    borderColor: colors.glassBorder,
    borderRadius: borderRadius.md,
    marginTop: 4,
    zIndex: 100,
    maxHeight: 220,
    ...shadows.glass,
    overflow: 'hidden',
  },
  dropdownScroll: {
    maxHeight: 220,
  },
  dropdownOption: {
    paddingHorizontal: spacing.md,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: colors.glassBorder,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  dropdownOptionSelected: {
    backgroundColor: colors.accentGlow,
  },
  dropdownOptionText: {
    fontSize: typography.sizes.md,
    color: colors.textPrimary,
  },
  dropdownOptionTextSelected: {
    color: colors.accent,
    fontWeight: '600',
  },
  dropdownCheckmark: {
    fontSize: 14,
    color: colors.accent,
    fontWeight: '700',
  },
  submitButton: {
    marginTop: spacing.xl,
    borderRadius: borderRadius.md,
    overflow: 'hidden',
    ...shadows.button,
  },
  submitButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: spacing.xl,
    gap: spacing.sm,
  },
  submitButtonText: {
    fontSize: typography.sizes.lg,
    fontWeight: '700',
    color: '#fff',
  },
  submitButtonArrow: {
    fontSize: typography.sizes.lg,
    color: '#fff',
  },
});

export default BasicDetailsForm;
