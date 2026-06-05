import React, { useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import { StockScore } from '../types';
import ScoreBreakdown from '../components/ScoreBreakdown';
import SellRulesModal from '../components/SellRulesModal';
import { useStore } from '../store';
import { theme } from '../theme';

export default function DetailScreen() {
  const route = useRoute<any>();
  const score: StockScore = route.params.score;
  const navigation = useNavigation();
  const { cash, positions, buyStock } = useStore();
  const [modalVisible, setModalVisible] = useState(false);

  const isOwned = positions.some((p) => p.code === score.code);
  const isUp = score.priceChangePct >= 0;
  const changeColor = isUp ? theme.success : theme.error;
  const maxTotal = 90 + 75 + 45 + 45;
  const scorePct = Math.round((score.totalScore / maxTotal) * 100);

  return (
    <View style={styles.container}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {/* Hero */}
        <View style={styles.hero}>
          <View>
            <Text style={styles.codeText}>{score.code} | 東証</Text>
            <Text style={styles.nameText}>{score.name}</Text>
          </View>
          <View style={styles.priceBlock}>
            <Text style={styles.priceText}>
              ¥{score.currentPrice.toLocaleString()}
            </Text>
            <Text style={[styles.changeText, { color: changeColor }]}>
              {isUp ? '+' : ''}
              {score.priceChange.toFixed(0)}円 ({isUp ? '+' : ''}
              {score.priceChangePct.toFixed(2)}%)
            </Text>
          </View>
        </View>

        {/* Total Score */}
        <View style={styles.totalScoreCard}>
          <View>
            <Text style={styles.totalLabel}>総合スコア</Text>
            <Text style={styles.totalScore}>{score.totalScore}pt</Text>
            <Text style={styles.totalMax}>/ {maxTotal}pt 満点</Text>
          </View>
          <View style={styles.gaugeWrap}>
            <View style={styles.gaugeTrack}>
              <View
                style={[
                  styles.gaugeFill,
                  {
                    width: `${scorePct}%`,
                    backgroundColor:
                      scorePct >= 60
                        ? theme.success
                        : scorePct >= 40
                        ? theme.warning
                        : theme.error,
                  },
                ]}
              />
            </View>
            <Text style={styles.gaugeLabel}>{scorePct}%</Text>
          </View>
        </View>

        {/* Key Stats */}
        <View style={styles.statsCard}>
          <Text style={styles.sectionTitle}>主要指標</Text>
          <View style={styles.statsGrid}>
            <StatItem label="RSI(14)" value={score.rsi.toFixed(1)} />
            <StatItem
              label="テクニカル"
              value={`${score.technical.score}/${score.technical.max}`}
              color="#00D4FF"
            />
            <StatItem
              label="ファンダメンタル"
              value={`${score.fundamental.score}/${score.fundamental.max}`}
              color="#FFB300"
            />
            <StatItem
              label="モメンタム"
              value={`${score.momentum.score}/${score.momentum.max}`}
              color="#00E676"
            />
            <StatItem
              label="ニュース"
              value={`${score.news.score}/${score.news.max}`}
              color="#FF6B6B"
            />
          </View>
        </View>

        {/* Score Breakdown */}
        <ScoreBreakdown score={score} />

        <View style={{ height: 80 }} />
      </ScrollView>

      {/* Buy Button */}
      <View style={styles.buyBar}>
        <View style={styles.cashInfo}>
          <Text style={styles.cashLabel}>残高</Text>
          <Text style={styles.cashValue}>¥{cash.toLocaleString()}</Text>
        </View>
        <TouchableOpacity
          style={[styles.buyBtn, isOwned && styles.ownedBtn]}
          onPress={() => !isOwned && setModalVisible(true)}
          activeOpacity={0.8}
        >
          <Text style={[styles.buyBtnText, isOwned && styles.ownedText]}>
            {isOwned ? '保有中' : '購入する'}
          </Text>
        </TouchableOpacity>
      </View>

      <SellRulesModal
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
        onConfirm={(shares, rules) => {
          buyStock(score, shares, rules);
          navigation.goBack();
        }}
        stockName={score.name}
        price={score.currentPrice}
        availableCash={cash}
      />
    </View>
  );
}

function StatItem({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <View style={styles.statItem}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={[styles.statValue, color ? { color } : {}]}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.background,
  },
  content: {
    padding: 16,
  },
  hero: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  codeText: {
    color: theme.textMuted,
    fontSize: 12,
    fontWeight: '600',
  },
  nameText: {
    color: theme.textPrimary,
    fontSize: 20,
    fontWeight: '700',
    marginTop: 4,
    maxWidth: 200,
  },
  priceBlock: {
    alignItems: 'flex-end',
  },
  priceText: {
    color: theme.textPrimary,
    fontSize: 24,
    fontWeight: '700',
  },
  changeText: {
    fontSize: 13,
    fontWeight: '600',
    marginTop: 2,
  },
  totalScoreCard: {
    backgroundColor: theme.surface,
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  totalLabel: {
    color: theme.textSecondary,
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  totalScore: {
    color: theme.textPrimary,
    fontSize: 36,
    fontWeight: '800',
    lineHeight: 42,
  },
  totalMax: {
    color: theme.textMuted,
    fontSize: 11,
  },
  gaugeWrap: {
    alignItems: 'flex-end',
    width: 120,
  },
  gaugeTrack: {
    width: 120,
    height: 8,
    backgroundColor: theme.border,
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 4,
  },
  gaugeFill: {
    height: '100%',
    borderRadius: 4,
  },
  gaugeLabel: {
    color: theme.textSecondary,
    fontSize: 12,
  },
  statsCard: {
    backgroundColor: theme.surface,
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
  },
  sectionTitle: {
    color: theme.textSecondary,
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 12,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  statItem: {
    backgroundColor: theme.surfaceElevated,
    borderRadius: 8,
    padding: 10,
    minWidth: '30%',
    flex: 1,
  },
  statLabel: {
    color: theme.textMuted,
    fontSize: 10,
    marginBottom: 4,
  },
  statValue: {
    color: theme.textPrimary,
    fontSize: 15,
    fontWeight: '700',
  },
  buyBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.surface,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: theme.border,
    gap: 12,
  },
  cashInfo: {
    flex: 1,
  },
  cashLabel: {
    color: theme.textMuted,
    fontSize: 11,
  },
  cashValue: {
    color: theme.textPrimary,
    fontSize: 15,
    fontWeight: '700',
  },
  buyBtn: {
    backgroundColor: theme.primary,
    borderRadius: 12,
    paddingHorizontal: 28,
    paddingVertical: 13,
  },
  buyBtnText: {
    color: '#000',
    fontWeight: '700',
    fontSize: 16,
  },
  ownedBtn: {
    backgroundColor: theme.border,
  },
  ownedText: {
    color: theme.textMuted,
  },
});
