export function sma(data: number[], period: number): number {
  if (data.length < period) return 0;
  const slice = data.slice(-period);
  return slice.reduce((a, b) => a + b, 0) / period;
}

export function emaArray(data: number[], period: number): number[] {
  if (data.length === 0) return [];
  const k = 2 / (period + 1);
  const result: number[] = [data[0]];
  for (let i = 1; i < data.length; i++) {
    result.push(data[i] * k + result[i - 1] * (1 - k));
  }
  return result;
}

export function rsi(closes: number[], period: number = 14): number {
  if (closes.length < period + 1) return 50;

  let gains = 0;
  let losses = 0;

  for (let i = 1; i <= period; i++) {
    const diff = closes[i] - closes[i - 1];
    if (diff > 0) gains += diff;
    else losses -= diff;
  }

  let avgGain = gains / period;
  let avgLoss = losses / period;

  for (let i = period + 1; i < closes.length; i++) {
    const diff = closes[i] - closes[i - 1];
    avgGain = (avgGain * (period - 1) + Math.max(0, diff)) / period;
    avgLoss = (avgLoss * (period - 1) + Math.max(0, -diff)) / period;
  }

  if (avgLoss === 0) return 100;
  const rs = avgGain / avgLoss;
  return 100 - 100 / (1 + rs);
}

export interface MacdResult {
  macdLine: number;
  signalLine: number;
  histogram: number;
  isBullish: boolean;
  crossedUp: boolean; // histogram turned positive this period
}

export function macd(
  closes: number[],
  fastPeriod = 12,
  slowPeriod = 26,
  signalPeriod = 9
): MacdResult {
  if (closes.length < slowPeriod + signalPeriod) {
    return { macdLine: 0, signalLine: 0, histogram: 0, isBullish: false, crossedUp: false };
  }

  const ema12 = emaArray(closes, fastPeriod);
  const ema26 = emaArray(closes, slowPeriod);
  const macdLine = ema12.map((v, i) => v - ema26[i]);
  const signalArr = emaArray(macdLine.slice(-(signalPeriod + 10)), signalPeriod);

  const lastMacd = macdLine[macdLine.length - 1];
  const prevMacd = macdLine[macdLine.length - 2] ?? 0;
  const lastSignal = signalArr[signalArr.length - 1];
  const prevSignal = signalArr[signalArr.length - 2] ?? 0;
  const histogram = lastMacd - lastSignal;
  const prevHistogram = prevMacd - prevSignal;

  return {
    macdLine: lastMacd,
    signalLine: lastSignal,
    histogram,
    isBullish: histogram > 0,
    crossedUp: histogram > 0 && prevHistogram <= 0,
  };
}

export function bollingerBands(
  closes: number[],
  period = 20,
  stdDevMultiplier = 2
): { upper: number; middle: number; lower: number } {
  if (closes.length < period) {
    const last = closes[closes.length - 1] ?? 0;
    return { upper: last, middle: last, lower: last };
  }
  const slice = closes.slice(-period);
  const mean = slice.reduce((a, b) => a + b, 0) / period;
  const variance = slice.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / period;
  const stdDev = Math.sqrt(variance);
  return {
    upper: mean + stdDev * stdDevMultiplier,
    middle: mean,
    lower: mean - stdDev * stdDevMultiplier,
  };
}

export function volumeRatio(volumes: number[], period = 20): number {
  if (volumes.length < period + 1) return 1;
  const avg = sma(volumes.slice(0, -1), period);
  if (avg === 0) return 1;
  return volumes[volumes.length - 1] / avg;
}

export function periodReturn(closes: number[], days: number): number {
  if (closes.length < days + 1) return 0;
  const current = closes[closes.length - 1];
  const past = closes[closes.length - 1 - days];
  if (past === 0) return 0;
  return (current - past) / past;
}
