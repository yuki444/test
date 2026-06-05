import React from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
} from 'react-native';
import { useStore } from '../store';
import { Position, Trade } from '../types';
import { theme } from '../theme';

function PositionCard({ position }: { position: Position }) {
  const { sellPosition } = useStore();
  const pnl = (position.currentPrice - position.buyPrice) * position.shares;
  const pnlPct = (position.currentPrice - position.buyPrice) / position.buyPrice * 100;
  const isUp = pnl >= 0;
  const color = isUp ? theme.success : theme.error;

  function handleSell() {
    Alert.alert(
      `${position.name} を売却`,
      `${position.shares}株 ¥${position.currentPrice.toLocaleString()}/株`,
      [
        { text: 'キャンセル', style: 'cancel' },
        {
          text: '売却確定',
          style: 'destructive',
          onPress: () =>
            sellPosition(position.id, position.currentPrice, '手動売却'),
        },
      ]
    );
  }

  return (
    <View style={styles.posCard}>
      <View style={styles.posHeader}>
        <View>
          <Text style={styles.posCode}>{position.code}</Text>
          <Text style={styles.posName}>{position.name}</Text>
          <Text style={styles.posDate}>購入 {position.buyDate}</Text>
        </View>
        <View style={styles.posRight}>
          <Text style={styles.posPrice}>
            ¥{position.currentPrice.toLocaleString()}
          </Text>
          <Text style={[styles.posPnl, { color }]}>
            {isUp ? '+' : ''}
            {pnl.toLocaleString(undefined, { maximumFractionDigits: 0 })}円
            ({isUp ? '+' : ''}{pnlPct.toFixed(1)}%)
          </Text>
        </View>
      </View>

      <View style={styles.posDetails}>
        <Detail label="保有株数" value={`${position.shares}株`} />
        <Detail
          label="取得単価"
          value={`¥${position.buyPrice.toLocaleString()}`}
        />
        <Detail
          label="評価額"
          value={`¥${(position.currentPrice * position.shares).toLocaleString()}`}
        />
      </View>

      <View style={styles.rulesRow}>
        {position.sellRules.stopLoss !== undefined && (
          <RulePill
            label={`損切 -${position.sellRules.stopLoss}%`}
            color={theme.error}
          />
        )}
        {position.sellRules.takeProfit !== undefined && (
          <RulePill
            label={`利確 +${position.sellRules.takeProfit}%`}
            color={theme.success}
          />
        )}
        {position.sellRules.trailingStop !== undefined && (
          <RulePill
            label={`トレール ${position.sellRules.trailingStop}%`}
            color={theme.warning}
          />
        )}
        {position.sellRules.daysToHold !== undefined && (
          <RulePill
            label={`${position.sellRules.daysToHold}日後`}
            color={theme.primary}
          />
        )}
      </View>

      <TouchableOpacity style={styles.sellBtn} onPress={handleSell}>
        <Text style={styles.sellBtnText}>手動売却</Text>
      </TouchableOpacity>
    </View>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.detail}>
      <Text style={styles.detailLabel}>{label}</Text>
      <Text style={styles.detailValue}>{value}</Text>
    </View>
  );
}

function RulePill({ label, color }: { label: string; color: string }) {
  return (
    <View style={[styles.rulePill, { borderColor: color }]}>
      <Text style={[styles.rulePillText, { color }]}>{label}</Text>
    </View>
  );
}

function TradeHistoryItem({ trade }: { trade: Trade }) {
  const isBuy = trade.type === 'buy';
  const color = isBuy ? theme.primary : trade.pnl !== undefined && trade.pnl >= 0 ? theme.success : theme.error;
  return (
    <View style={styles.tradeRow}>
      <View style={[styles.tradeDot, { backgroundColor: color }]} />
      <View style={styles.tradeInfo}>
        <Text style={styles.tradeName}>{trade.name}</Text>
        <Text style={styles.tradeDate}>{trade.date} {trade.reason ? `— ${trade.reason}` : ''}</Text>
      </View>
      <View style={styles.tradeNumbers}>
        <Text style={[styles.tradeType, { color }]}>{isBuy ? '買い' : '売り'}</Text>
        <Text style={styles.tradeShares}>{trade.shares}株 ¥{trade.price.toLocaleString()}</Text>
        {trade.pnl !== undefined && (
          <Text style={[styles.tradePnl, { color }]}>
            {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toLocaleString(undefined, {maximumFractionDigits: 0})}円
          </Text>
        )}
      </View>
    </View>
  );
}

export default function PortfolioScreen() {
  const { cash, positions, tradeHistory, resetPortfolio } = useStore();

  const totalValuation = positions.reduce(
    (sum, p) => sum + p.currentPrice * p.shares,
    0
  );
  const totalAssets = cash + totalValuation;
  const totalCost = positions.reduce(
    (sum, p) => sum + p.buyPrice * p.shares,
    0
  );
  const unrealizedPnl = totalValuation - totalCost;
  const initialAssets = 5_000_000;
  const totalReturn = ((totalAssets - initialAssets) / initialAssets) * 100;

  function handleReset() {
    Alert.alert(
      'ポートフォリオをリセット',
      '取引履歴・保有株・資産をすべてリセットします。',
      [
        { text: 'キャンセル', style: 'cancel' },
        { text: 'リセット', style: 'destructive', onPress: resetPortfolio },
      ]
    );
  }

  return (
    <FlatList
      style={styles.container}
      contentContainerStyle={styles.content}
      ListHeaderComponent={
        <>
          {/* Asset Summary */}
          <View style={styles.summaryCard}>
            <Text style={styles.summaryLabel}>仮想総資産</Text>
            <Text style={styles.summaryTotal}>
              ¥{totalAssets.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </Text>
            <Text
              style={[
                styles.summaryReturn,
                { color: totalReturn >= 0 ? theme.success : theme.error },
              ]}
            >
              {totalReturn >= 0 ? '+' : ''}{totalReturn.toFixed(2)}% (初期資金¥5,000,000比)
            </Text>

            <View style={styles.summaryRow}>
              <SummaryItem
                label="現金"
                value={`¥${cash.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
              />
              <SummaryItem
                label="株式評価額"
                value={`¥${totalValuation.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
              />
              <SummaryItem
                label="含み損益"
                value={`${unrealizedPnl >= 0 ? '+' : ''}¥${unrealizedPnl.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
                color={unrealizedPnl >= 0 ? theme.success : theme.error}
              />
            </View>
          </View>

          {positions.length > 0 && (
            <Text style={styles.sectionTitle}>保有銘柄 ({positions.length})</Text>
          )}
        </>
      }
      data={positions}
      keyExtractor={(item) => item.id}
      renderItem={({ item }) => <PositionCard position={item} />}
      ListFooterComponent={
        <>
          {tradeHistory.length > 0 && (
            <>
              <Text style={styles.sectionTitle}>取引履歴 ({tradeHistory.length}件)</Text>
              {tradeHistory.slice(0, 20).map((t) => (
                <TradeHistoryItem key={t.id} trade={t} />
              ))}
            </>
          )}

          {positions.length === 0 && tradeHistory.length === 0 && (
            <View style={styles.empty}>
              <Text style={styles.emptyText}>取引履歴がありません</Text>
              <Text style={styles.emptyHint}>ランキング画面から銘柄を購入できます</Text>
            </View>
          )}

          <TouchableOpacity style={styles.resetBtn} onPress={handleReset}>
            <Text style={styles.resetText}>ポートフォリオをリセット</Text>
          </TouchableOpacity>

          <View style={{ height: 40 }} />
        </>
      }
    />
  );
}

function SummaryItem({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <View style={styles.summaryItem}>
      <Text style={styles.summaryItemLabel}>{label}</Text>
      <Text style={[styles.summaryItemValue, color ? { color } : {}]}>{value}</Text>
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
  summaryCard: {
    backgroundColor: theme.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
  },
  summaryLabel: {
    color: theme.textSecondary,
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  summaryTotal: {
    color: theme.textPrimary,
    fontSize: 32,
    fontWeight: '800',
    marginVertical: 4,
  },
  summaryReturn: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 16,
  },
  summaryRow: {
    flexDirection: 'row',
    gap: 8,
  },
  summaryItem: {
    flex: 1,
    backgroundColor: theme.surfaceElevated,
    borderRadius: 8,
    padding: 10,
  },
  summaryItemLabel: {
    color: theme.textMuted,
    fontSize: 10,
    marginBottom: 4,
  },
  summaryItemValue: {
    color: theme.textPrimary,
    fontSize: 13,
    fontWeight: '700',
  },
  sectionTitle: {
    color: theme.textSecondary,
    fontSize: 13,
    fontWeight: '600',
    marginBottom: 10,
    marginTop: 4,
  },
  posCard: {
    backgroundColor: theme.surface,
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
  },
  posHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  posCode: {
    color: theme.textMuted,
    fontSize: 11,
  },
  posName: {
    color: theme.textPrimary,
    fontSize: 15,
    fontWeight: '700',
    marginVertical: 2,
  },
  posDate: {
    color: theme.textMuted,
    fontSize: 11,
  },
  posRight: {
    alignItems: 'flex-end',
  },
  posPrice: {
    color: theme.textPrimary,
    fontSize: 16,
    fontWeight: '700',
  },
  posPnl: {
    fontSize: 13,
    fontWeight: '600',
  },
  posDetails: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 10,
  },
  detail: {
    flex: 1,
    backgroundColor: theme.surfaceElevated,
    borderRadius: 6,
    padding: 8,
  },
  detailLabel: {
    color: theme.textMuted,
    fontSize: 10,
    marginBottom: 2,
  },
  detailValue: {
    color: theme.textPrimary,
    fontSize: 12,
    fontWeight: '600',
  },
  rulesRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: 10,
  },
  rulePill: {
    borderWidth: 1,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  rulePillText: {
    fontSize: 11,
    fontWeight: '600',
  },
  sellBtn: {
    borderWidth: 1,
    borderColor: theme.error,
    borderRadius: 8,
    padding: 8,
    alignItems: 'center',
  },
  sellBtnText: {
    color: theme.error,
    fontWeight: '600',
    fontSize: 13,
  },
  tradeRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: theme.surface,
    borderRadius: 10,
    padding: 12,
    marginBottom: 6,
    gap: 10,
  },
  tradeDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginTop: 4,
  },
  tradeInfo: {
    flex: 1,
  },
  tradeName: {
    color: theme.textPrimary,
    fontSize: 14,
    fontWeight: '600',
  },
  tradeDate: {
    color: theme.textMuted,
    fontSize: 11,
    marginTop: 2,
  },
  tradeNumbers: {
    alignItems: 'flex-end',
  },
  tradeType: {
    fontSize: 12,
    fontWeight: '700',
  },
  tradeShares: {
    color: theme.textSecondary,
    fontSize: 11,
    marginTop: 1,
  },
  tradePnl: {
    fontSize: 12,
    fontWeight: '600',
    marginTop: 1,
  },
  empty: {
    alignItems: 'center',
    marginTop: 60,
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
  resetBtn: {
    borderWidth: 1,
    borderColor: theme.error,
    borderRadius: 10,
    padding: 14,
    alignItems: 'center',
    marginTop: 24,
  },
  resetText: {
    color: theme.error,
    fontWeight: '600',
  },
});
