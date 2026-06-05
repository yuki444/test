import React, { useEffect, useCallback } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useStore } from '../store';
import { StockScore } from '../types';
import MiniChart from '../components/MiniChart';
import { theme, rankColors } from '../theme';

const RANK_MEDALS = ['🥇', '🥈', '🥉'];

function RankBadge({ rank }: { rank: number }) {
  if (rank <= 3) {
    return <Text style={styles.medal}>{RANK_MEDALS[rank - 1]}</Text>;
  }
  return (
    <View style={[styles.rankBadge, { borderColor: theme.border }]}>
      <Text style={styles.rankNum}>{rank}</Text>
    </View>
  );
}

function StockCard({
  item,
  rank,
  onPress,
}: {
  item: StockScore;
  rank: number;
  onPress: () => void;
}) {
  const isUp = item.priceChangePct >= 0;
  const changeColor = isUp ? theme.success : theme.error;
  const maxScore = 90 + 75 + 45 + 45;
  const scorePct = Math.round((item.totalScore / maxScore) * 100);

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.8}>
      <View style={styles.cardLeft}>
        <RankBadge rank={rank} />
        <View style={styles.cardInfo}>
          <Text style={styles.stockCode}>{item.code}</Text>
          <Text style={styles.stockName} numberOfLines={1}>
            {item.name}
          </Text>
          <View style={styles.scoreRow}>
            <View
              style={[
                styles.scorePill,
                { backgroundColor: scorePct >= 60 ? theme.primaryDim : theme.border },
              ]}
            >
              <Text style={styles.scoreText}>{item.totalScore}pt</Text>
            </View>
            <View style={styles.miniAxes}>
              {[item.technical, item.fundamental, item.momentum, item.news].map(
                (ax, i) => {
                  const colors = ['#00D4FF', '#FFB300', '#00E676', '#FF6B6B'];
                  const pct = (ax.score / ax.max) * 100;
                  return (
                    <View key={i} style={styles.miniBarWrap}>
                      <View
                        style={[
                          styles.miniBar,
                          { height: `${Math.max(pct, 5)}%`, backgroundColor: colors[i] },
                        ]}
                      />
                    </View>
                  );
                }
              )}
            </View>
          </View>
        </View>
      </View>

      <View style={styles.cardRight}>
        <MiniChart quotes={item.quotes} positive={isUp} />
        <Text style={styles.price}>
          ¥{item.currentPrice.toLocaleString()}
        </Text>
        <Text style={[styles.change, { color: changeColor }]}>
          {isUp ? '+' : ''}
          {item.priceChangePct.toFixed(2)}%
        </Text>
      </View>
    </TouchableOpacity>
  );
}

export default function HomeScreen() {
  const { rankings, isLoading, loadingStatus, loadingProgress, error, lastUpdated, refreshRankings, loadFromCache } =
    useStore();
  const navigation = useNavigation<any>();

  useEffect(() => {
    loadFromCache().then(() => {
      if (useStore.getState().rankings.length === 0) {
        refreshRankings();
      }
    });
  }, []);

  const onRefresh = useCallback(() => refreshRankings(), []);

  const updatedStr = lastUpdated
    ? new Date(lastUpdated).toLocaleString('ja-JP', {
        month: 'numeric',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : null;

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>推奨銘柄 TOP10</Text>
          {updatedStr && (
            <Text style={styles.updated}>更新: {updatedStr}</Text>
          )}
        </View>
        <TouchableOpacity style={styles.refreshBtn} onPress={onRefresh} disabled={isLoading}>
          <Text style={styles.refreshText}>{isLoading ? '更新中' : '更新'}</Text>
        </TouchableOpacity>
      </View>

      {isLoading && (
        <View style={styles.loadingBanner}>
          <ActivityIndicator color={theme.primary} size="small" />
          <View style={styles.loadingInfo}>
            <Text style={styles.loadingStatus}>{loadingStatus}</Text>
            <View style={styles.progressTrack}>
              <View
                style={[styles.progressFill, { width: `${loadingProgress * 100}%` }]}
              />
            </View>
          </View>
        </View>
      )}

      {error && (
        <View style={styles.errorBanner}>
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity onPress={onRefresh}>
            <Text style={styles.retryText}>再試行</Text>
          </TouchableOpacity>
        </View>
      )}

      <FlatList
        data={rankings.slice(0, 10)}
        keyExtractor={(item) => item.code}
        renderItem={({ item, index }) => (
          <StockCard
            item={item}
            rank={index + 1}
            onPress={() => navigation.navigate('Detail', { score: item })}
          />
        )}
        refreshControl={
          <RefreshControl
            refreshing={isLoading}
            onRefresh={onRefresh}
            tintColor={theme.primary}
          />
        }
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          !isLoading ? (
            <View style={styles.empty}>
              <Text style={styles.emptyText}>データがありません</Text>
              <Text style={styles.emptyHint}>下にスワイプして更新してください</Text>
            </View>
          ) : null
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 8,
  },
  title: {
    color: theme.textPrimary,
    fontSize: 20,
    fontWeight: '700',
  },
  updated: {
    color: theme.textMuted,
    fontSize: 11,
    marginTop: 2,
  },
  refreshBtn: {
    backgroundColor: theme.primaryDim,
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 7,
  },
  refreshText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 13,
  },
  loadingBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: theme.surface,
    marginHorizontal: 16,
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
    gap: 12,
  },
  loadingInfo: {
    flex: 1,
  },
  loadingStatus: {
    color: theme.textSecondary,
    fontSize: 12,
    marginBottom: 4,
  },
  progressTrack: {
    height: 3,
    backgroundColor: theme.border,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: theme.primary,
    borderRadius: 2,
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(255,82,82,0.15)',
    borderColor: theme.error,
    borderWidth: 1,
    marginHorizontal: 16,
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
  },
  errorText: {
    color: theme.error,
    fontSize: 13,
    flex: 1,
  },
  retryText: {
    color: theme.primary,
    fontWeight: '600',
    fontSize: 13,
  },
  list: {
    paddingHorizontal: 16,
    paddingBottom: 24,
  },
  card: {
    backgroundColor: theme.surface,
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  cardLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  medal: {
    fontSize: 28,
    marginRight: 10,
  },
  rankBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  rankNum: {
    color: theme.textSecondary,
    fontWeight: '700',
    fontSize: 14,
  },
  cardInfo: {
    flex: 1,
  },
  stockCode: {
    color: theme.textMuted,
    fontSize: 11,
    fontWeight: '600',
  },
  stockName: {
    color: theme.textPrimary,
    fontSize: 15,
    fontWeight: '700',
    marginVertical: 2,
  },
  scoreRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  scorePill: {
    borderRadius: 6,
    paddingHorizontal: 7,
    paddingVertical: 2,
  },
  scoreText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: '700',
  },
  miniAxes: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    height: 16,
    gap: 2,
  },
  miniBarWrap: {
    width: 5,
    height: 16,
    backgroundColor: theme.border,
    borderRadius: 2,
    overflow: 'hidden',
    justifyContent: 'flex-end',
  },
  miniBar: {
    width: '100%',
    borderRadius: 2,
  },
  cardRight: {
    alignItems: 'flex-end',
    gap: 2,
  },
  price: {
    color: theme.textPrimary,
    fontWeight: '700',
    fontSize: 14,
  },
  change: {
    fontSize: 12,
    fontWeight: '600',
  },
  empty: {
    alignItems: 'center',
    marginTop: 80,
  },
  emptyText: {
    color: theme.textSecondary,
    fontSize: 16,
    marginBottom: 8,
  },
  emptyHint: {
    color: theme.textMuted,
    fontSize: 13,
  },
});
