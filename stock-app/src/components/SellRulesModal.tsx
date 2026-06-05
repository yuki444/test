import React, { useState } from 'react';
import {
  Modal,
  View,
  Text,
  TouchableOpacity,
  TextInput,
  StyleSheet,
  Switch,
  ScrollView,
} from 'react-native';
import { SellRules } from '../types';
import { theme } from '../theme';

interface Props {
  visible: boolean;
  onClose: () => void;
  onConfirm: (shares: number, rules: SellRules) => void;
  stockName: string;
  price: number;
  availableCash: number;
}

export default function SellRulesModal({
  visible,
  onClose,
  onConfirm,
  stockName,
  price,
  availableCash,
}: Props) {
  const [shares, setShares] = useState('100');
  const [useStopLoss, setUseStopLoss] = useState(true);
  const [stopLoss, setStopLoss] = useState('8');
  const [useTakeProfit, setUseTakeProfit] = useState(true);
  const [takeProfit, setTakeProfit] = useState('25');
  const [useTrailing, setUseTrailing] = useState(false);
  const [trailing, setTrailing] = useState('5');
  const [useDays, setUseDays] = useState(false);
  const [days, setDays] = useState('30');

  const sharesNum = parseInt(shares, 10) || 0;
  const totalCost = sharesNum * price;
  const canBuy = sharesNum > 0 && totalCost <= availableCash;

  function handleConfirm() {
    const rules: SellRules = {};
    if (useStopLoss) rules.stopLoss = parseFloat(stopLoss) || 8;
    if (useTakeProfit) rules.takeProfit = parseFloat(takeProfit) || 25;
    if (useTrailing) rules.trailingStop = parseFloat(trailing) || 5;
    if (useDays) rules.daysToHold = parseInt(days, 10) || 30;
    onConfirm(sharesNum, rules);
    onClose();
  }

  return (
    <Modal visible={visible} transparent animationType="slide">
      <View style={styles.overlay}>
        <View style={styles.sheet}>
          <Text style={styles.title}>{stockName} を購入</Text>
          <Text style={styles.price}>¥{price.toLocaleString()}/株</Text>

          <View style={styles.inputRow}>
            <Text style={styles.label}>株数</Text>
            <TextInput
              style={styles.input}
              value={shares}
              onChangeText={setShares}
              keyboardType="numeric"
              placeholderTextColor={theme.textMuted}
            />
          </View>

          <View style={styles.costRow}>
            <Text style={styles.costLabel}>購入金額</Text>
            <Text style={[styles.costValue, !canBuy && { color: theme.error }]}>
              ¥{totalCost.toLocaleString()}
            </Text>
          </View>

          <Text style={styles.sectionTitle}>売却ルール</Text>

          <RuleRow
            label="損切り"
            enabled={useStopLoss}
            onToggle={setUseStopLoss}
            value={stopLoss}
            onChange={setStopLoss}
            suffix="%下落"
            color={theme.error}
          />
          <RuleRow
            label="利確"
            enabled={useTakeProfit}
            onToggle={setUseTakeProfit}
            value={takeProfit}
            onChange={setTakeProfit}
            suffix="%上昇"
            color={theme.success}
          />
          <RuleRow
            label="トレーリングストップ"
            enabled={useTrailing}
            onToggle={setUseTrailing}
            value={trailing}
            onChange={setTrailing}
            suffix="%下落（高値比）"
            color={theme.warning}
          />
          <RuleRow
            label="保有期間"
            enabled={useDays}
            onToggle={setUseDays}
            value={days}
            onChange={setDays}
            suffix="日後に売却"
            color={theme.primary}
          />

          <View style={styles.buttons}>
            <TouchableOpacity style={styles.cancelBtn} onPress={onClose}>
              <Text style={styles.cancelText}>キャンセル</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.buyBtn, !canBuy && styles.disabled]}
              onPress={handleConfirm}
              disabled={!canBuy}
            >
              <Text style={styles.buyText}>購入確定</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
}

function RuleRow({
  label,
  enabled,
  onToggle,
  value,
  onChange,
  suffix,
  color,
}: {
  label: string;
  enabled: boolean;
  onToggle: (v: boolean) => void;
  value: string;
  onChange: (v: string) => void;
  suffix: string;
  color: string;
}) {
  return (
    <View style={styles.ruleRow}>
      <Switch
        value={enabled}
        onValueChange={onToggle}
        trackColor={{ true: color, false: theme.border }}
        thumbColor={theme.textPrimary}
      />
      <Text style={[styles.ruleLabel, { color: enabled ? theme.textPrimary : theme.textMuted }]}>
        {label}
      </Text>
      {enabled && (
        <>
          <TextInput
            style={styles.ruleInput}
            value={value}
            onChangeText={onChange}
            keyboardType="numeric"
          />
          <Text style={[styles.ruleSuffix, { color }]}>{suffix}</Text>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: theme.surface,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 24,
    paddingBottom: 40,
  },
  title: {
    color: theme.textPrimary,
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 4,
  },
  price: {
    color: theme.primary,
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 20,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  label: {
    color: theme.textSecondary,
    fontSize: 14,
    width: 60,
  },
  input: {
    flex: 1,
    backgroundColor: theme.surfaceElevated,
    borderRadius: 8,
    padding: 10,
    color: theme.textPrimary,
    fontSize: 16,
    fontWeight: '700',
  },
  costRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
    paddingHorizontal: 4,
  },
  costLabel: {
    color: theme.textSecondary,
    fontSize: 14,
  },
  costValue: {
    color: theme.textPrimary,
    fontSize: 16,
    fontWeight: '700',
  },
  sectionTitle: {
    color: theme.textSecondary,
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 12,
  },
  ruleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
    gap: 8,
  },
  ruleLabel: {
    fontSize: 13,
    width: 120,
  },
  ruleInput: {
    backgroundColor: theme.surfaceElevated,
    borderRadius: 6,
    padding: 6,
    color: theme.textPrimary,
    fontSize: 14,
    fontWeight: '700',
    width: 48,
    textAlign: 'center',
  },
  ruleSuffix: {
    fontSize: 12,
    flex: 1,
  },
  buttons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 24,
  },
  cancelBtn: {
    flex: 1,
    backgroundColor: theme.border,
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
  },
  cancelText: {
    color: theme.textSecondary,
    fontWeight: '600',
  },
  buyBtn: {
    flex: 2,
    backgroundColor: theme.primary,
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
  },
  buyText: {
    color: '#000',
    fontWeight: '700',
    fontSize: 16,
  },
  disabled: {
    opacity: 0.4,
  },
});
