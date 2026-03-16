/**
 * Centralized Theme Constants
 * Modern Glassmorphism Design System
 */

export const colors = {
  // Primary Gradient
  gradientStart: '#667eea',
  gradientEnd: '#764ba2',
  
  // Background
  background: '#0a0a14',
  backgroundGradientStart: '#0a0a14',
  backgroundGradientEnd: '#141428',
  
  // Glass Effect
  glass: 'rgba(255, 255, 255, 0.06)',
  glassBorder: 'rgba(255, 255, 255, 0.1)',
  glassHover: 'rgba(255, 255, 255, 0.12)',
  glassLight: 'rgba(255, 255, 255, 0.03)',
  
  // Accent Colors
  accent: '#667eea',
  accentLight: '#8b9cf7',
  accentGlow: 'rgba(102, 126, 234, 0.25)',
  cyan: '#00d9ff',
  cyanGlow: 'rgba(0, 217, 255, 0.2)',
  
  // Status Colors
  success: '#34d399',
  successGlow: 'rgba(52, 211, 153, 0.2)',
  error: '#f87171',
  errorGlow: 'rgba(248, 113, 113, 0.2)',
  warning: '#fbbf24',
  warningGlow: 'rgba(251, 191, 36, 0.2)',
  
  // Recording State
  recording: '#f87171',
  recordingGlow: 'rgba(248, 113, 113, 0.4)',
  
  // Text Colors
  textPrimary: '#f1f5f9',
  textSecondary: 'rgba(241, 245, 249, 0.65)',
  textMuted: 'rgba(241, 245, 249, 0.4)',
  
  // Form Colors
  inputBackground: 'rgba(255, 255, 255, 0.04)',
  inputBorder: 'rgba(255, 255, 255, 0.08)',
  inputFocusBorder: '#667eea',
  placeholder: 'rgba(255, 255, 255, 0.3)',
  
  // Field status
  fieldFilled: 'rgba(52, 211, 153, 0.1)',
  fieldFilledBorder: 'rgba(52, 211, 153, 0.3)',
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const borderRadius = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  round: 9999,
};

export const shadows = {
  glass: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 32,
    elevation: 10,
  },
  glow: (color) => ({
    shadowColor: color,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.6,
    shadowRadius: 20,
    elevation: 15,
  }),
  button: {
    shadowColor: '#667eea',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
  },
  soft: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
  },
};

export const typography = {
  fontFamily: {
    regular: 'System',
    medium: 'System',
    bold: 'System',
  },
  sizes: {
    xs: 11,
    sm: 13,
    md: 15,
    lg: 17,
    xl: 22,
    xxl: 28,
    hero: 48,
  },
};

export const animations = {
  fast: 150,
  normal: 300,
  slow: 500,
  
  pulse: {
    duration: 1500,
    scale: 1.1,
  },
  glow: {
    duration: 2000,
  },
};

export const glassCard = {
  backgroundColor: colors.glass,
  borderWidth: 1,
  borderColor: colors.glassBorder,
  borderRadius: borderRadius.lg,
  ...shadows.glass,
};

export const gradientButton = {
  colors: [colors.gradientStart, colors.gradientEnd],
  start: { x: 0, y: 0 },
  end: { x: 1, y: 1 },
};

export default {
  colors,
  spacing,
  borderRadius,
  shadows,
  typography,
  animations,
  glassCard,
  gradientButton,
};
