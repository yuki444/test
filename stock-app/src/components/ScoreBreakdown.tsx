import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { StockScore } from '../types';
import { theme } from '../theme';

interface Props {
  score: StockScore;
}

const AXES = [
  { key: 'technical' as const, label: 'テクニカル', color: '#00D4FF' },
  { key: 'fundamental' as const, label: 'ファンダメンタル', color: '#FFB300' },
  { key: 'momentum' as const, label: 'モメンタム', color: '#00E676' },
  { key: 'news' as const, label: 'ニュース・決算', color: '#FF6B6B' },
];

function ScoreBar({
  score,
  max,
  color,
}: {
  score: number;
  max: number;
  color: string;
}) {
  const pct = Math.min((score / max) * 100, 100);
  return (
    <View style={styles.barTrack}>
      <View style={[styles.barFill, { width: `${pct}%`, backgroundColor: color }]} />
    </View>
  );
}

export default function ScoreBreakdown({ score }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <View style={styles.container}>
      <Text style={styles.sectionTitle}>スコア内訳</Text>
      {AXES.map(({ key, label, color }) => {
        const axis = score[key];
        const isOpen = expanded === key;
        return (
          <TouchableOpacity
            key={key}
            onPress={() => setExpanded(isOpen ? null : key)}
            activeOpacity={0.7}
          >
            <View style={styles.axisRow}>
              <View style={styles.axisHeader}>
                <View style={[styles.dot, { backgroundColor: color }]} />
                <Text style={styles.axisLabel}>{label}</Text>
                <Text style={[styles.axisScore, { color }]}>
                  {axis.score}
                  <Text style={styles.axisMax}>/{axis.max}</Text>
                </Text>
                <Text style={styles.chevron}>{isOpen ? '▲' : '▼'}</Text>
              </View>
              <ScoreBar score={axis.score} max={axis.max} color={color} />
            </View>
            {isOpen && (
              <View style={styles.detailBox}>
                {axis.details.map((d, i) => (
                  <Text key={i} style={styles.detailText}>
                    {d}
                  </Text>
                ))}
              </View>
            )}
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: theme.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  sectionTitle: {
    color: theme.textSecondary,
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 14,
  },
  axisRow: {
    marginBottom: 12,
  },
  axisHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  axisLabel: {
    color: theme.textPrimary,
    fontSize: 14,
    flex: 1,
  },
  axisScore: {
    fontSize: 15,
    fontWeight: '700',
    marginRight: 8,
  },
  axisMax: {
    fontSize: 11,
    color: theme.textSecondary,
    fontWeight: '400',
  },
  chevron: {
    color: theme.textMuted,
    fontSize: 10,
  },
  barTrack: {
    height: 6,
    backgroundColor: theme.border,
    borderRadius: 3,
    overflow: 'hidden',
  },
  barFill: {
    height: '100%',
    borderRadius: 3,
  },
  detailBox: {
    backgroundColor: theme.background,
    borderRadius: 8,
    padding: 10,
    marginBottom: 8,
    borderLeftWidth: 2,
    borderLeftColor: theme.border,
  },
  detailText: {
    color: theme.textSecondary,
    fontSize: 12,
    lineHeight: 18,
  },
});
