import React from 'react';
import { View, StyleSheet } from 'react-native';
import Svg, { Polyline, Defs, LinearGradient, Stop, Rect } from 'react-native-svg';
import { DailyQuote } from '../types';

interface Props {
  quotes: DailyQuote[];
  width?: number;
  height?: number;
  positive?: boolean;
}

export default function MiniChart({
  quotes,
  width = 80,
  height = 36,
  positive,
}: Props) {
  if (quotes.length < 2) return <View style={{ width, height }} />;

  const closes = quotes.slice(-30).map((q) => q.AdjustmentClose || q.Close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const range = max - min || 1;

  const points = closes
    .map((c, i) => {
      const x = (i / (closes.length - 1)) * width;
      const y = height - ((c - min) / range) * (height - 4) - 2;
      return `${x},${y}`;
    })
    .join(' ');

  const isUp = positive ?? closes[closes.length - 1] >= closes[0];
  const color = isUp ? '#00E676' : '#FF5252';

  return (
    <Svg width={width} height={height}>
      <Defs>
        <LinearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0" stopColor={color} stopOpacity="0.3" />
          <Stop offset="1" stopColor={color} stopOpacity="0" />
        </LinearGradient>
      </Defs>
      <Polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </Svg>
  );
}

const styles = StyleSheet.create({});
