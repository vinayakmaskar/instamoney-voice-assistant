/**
 * AudioWaveform Component
 * Real-time audio visualization with animated bars
 */
import React, { useEffect, useRef, useState } from 'react';
import { View, StyleSheet, Animated, Platform } from 'react-native';
import { colors } from '../styles/theme';

const NUM_BARS = 20;
const MIN_HEIGHT = 4;
const MAX_HEIGHT = 40;

const AudioWaveform = ({ isActive, audioLevel = 0, style }) => {
  const barAnimations = useRef(
    Array(NUM_BARS).fill(0).map(() => new Animated.Value(MIN_HEIGHT))
  ).current;
  
  const [bars, setBars] = useState(Array(NUM_BARS).fill(MIN_HEIGHT));
  
  useEffect(() => {
    if (isActive) {
      // Animate bars based on audio level
      const animateBars = () => {
        const newBars = barAnimations.map((anim, index) => {
          // Create a wave-like pattern
          const baseLevel = audioLevel * MAX_HEIGHT;
          const wave = Math.sin((Date.now() / 100) + index * 0.5) * 0.3 + 0.7;
          const randomFactor = 0.7 + Math.random() * 0.6;
          const targetHeight = Math.max(
            MIN_HEIGHT,
            Math.min(MAX_HEIGHT, baseLevel * wave * randomFactor)
          );
          
          Animated.spring(anim, {
            toValue: targetHeight,
            friction: 8,
            tension: 100,
            useNativeDriver: false,
          }).start();
          
          return targetHeight;
        });
        setBars(newBars);
      };
      
      const interval = setInterval(animateBars, 50);
      return () => clearInterval(interval);
    } else {
      // Reset to minimum height when inactive
      barAnimations.forEach(anim => {
        Animated.timing(anim, {
          toValue: MIN_HEIGHT,
          duration: 300,
          useNativeDriver: false,
        }).start();
      });
    }
  }, [isActive, audioLevel]);
  
  return (
    <View style={[styles.container, style]}>
      {barAnimations.map((anim, index) => (
        <Animated.View
          key={index}
          style={[
            styles.bar,
            {
              height: anim,
              backgroundColor: isActive ? colors.accent : colors.textMuted,
              opacity: isActive ? 1 : 0.3,
            },
          ]}
        />
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    height: 50,
    gap: 3,
  },
  bar: {
    width: 4,
    borderRadius: 2,
    minHeight: MIN_HEIGHT,
  },
});

export default AudioWaveform;

