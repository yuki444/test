import { DailyQuote, FinancialStatement, ListedInfo, ScoreDetail, StockScore } from '../types';
import { sma, rsi, macd, volumeRatio, periodReturn } from './technicals';

function techScore(closes: number[], volumes: number[]): ScoreDetail {
  let score = 0;
  const details: string[] = [];

  const ma5 = sma(closes, 5);
  const ma25 = sma(closes, 25);
  const ma50 = sma(closes, 50);
  const last = closes[closes.length - 1];

  if (closes.length >= 25 && ma5 > ma25) {
    score += 20;
    details.push(`MA5(${ma5.toFixed(0)}) > MA25(${ma25.toFixed(0)}) ✓ 短期上昇トレンド`);
  }

  if (closes.length >= 50 && ma25 > ma50) {
    score += 30;
    details.push(`MA25 > MA50 ✓ ゴールデンクロス圏`);
  }

  const rsiVal = rsi(closes);
  if (rsiVal >= 30 && rsiVal <= 55) {
    score += 20;
    details.push(`RSI ${rsiVal.toFixed(1)} ✓ 売られすぎからの回復ゾーン`);
  } else if (rsiVal < 30) {
    score += 8;
    details.push(`RSI ${rsiVal.toFixed(1)} △ 売られすぎ水準`);
  } else if (rsiVal > 70) {
    details.push(`RSI ${rsiVal.toFixed(1)} ✗ 買われすぎ水準`);
  }

  const { isBullish, crossedUp, histogram } = macd(closes);
  if (crossedUp) {
    score += 20;
    details.push(`MACDゴールデンクロス発生 ✓`);
  } else if (isBullish) {
    score += 10;
    details.push(`MACDヒストグラム プラス(${histogram.toFixed(2)}) ✓`);
  }

  const vr = volumeRatio(volumes, 20);
  if (vr >= 2.0) {
    score += 10;
    details.push(`出来高急増 ✓ 20日平均比 ${(vr * 100).toFixed(0)}%`);
  } else if (vr >= 1.5) {
    score += 5;
    details.push(`出来高増加 ${(vr * 100).toFixed(0)}%`);
  }

  // near-period high
  const periodHigh = Math.max(...closes.slice(-60));
  const highRatio = last / periodHigh;
  if (highRatio >= 0.95) {
    score += 10;
    details.push(`期間高値圏 ${(highRatio * 100).toFixed(1)}% ✓`);
  }

  return { score, max: 90, details };
}

function fundScore(
  currentPrice: number,
  statements: FinancialStatement[]
): ScoreDetail {
  let score = 0;
  const details: string[] = [];

  const s = statements[0];
  if (!s) return { score: 0, max: 75, details: ['財務データなし'] };

  const bps = s.BookValuePerShare;
  const eps = s.EarningsPerShare;
  const divAnnual = s.ResultDividendPerShareAnnual ?? s.ForecastDividendPerShareAnnual ?? 0;

  if (bps > 0) {
    const pbr = currentPrice / bps;
    if (pbr < 1.0) {
      score += 20;
      details.push(`PBR ${pbr.toFixed(2)}倍 ✓ 解散価値以下`);
    } else if (pbr < 2.0) {
      score += 10;
      details.push(`PBR ${pbr.toFixed(2)}倍 ✓ 割安圏`);
    } else {
      details.push(`PBR ${pbr.toFixed(2)}倍`);
    }
  }

  if (eps > 0) {
    const per = currentPrice / eps;
    if (per < 12) {
      score += 20;
      details.push(`PER ${per.toFixed(1)}倍 ✓ 割安`);
    } else if (per < 20) {
      score += 12;
      details.push(`PER ${per.toFixed(1)}倍 ✓ 適正圏`);
    } else if (per < 30) {
      score += 4;
      details.push(`PER ${per.toFixed(1)}倍`);
    } else {
      details.push(`PER ${per.toFixed(1)}倍 ✗ 割高`);
    }

    score += 15;
    details.push(`EPS ${eps.toFixed(0)}円 ✓ 黒字`);
  } else if (eps < 0) {
    details.push(`EPS ${eps.toFixed(0)}円 ✗ 赤字`);
  }

  if (divAnnual > 0 && currentPrice > 0) {
    const divYield = (divAnnual / currentPrice) * 100;
    if (divYield >= 3) {
      score += 20;
      details.push(`配当利回り ${divYield.toFixed(1)}% ✓ 高配当`);
    } else if (divYield >= 2) {
      score += 12;
      details.push(`配当利回り ${divYield.toFixed(1)}% ✓`);
    } else if (divYield > 0) {
      score += 5;
      details.push(`配当利回り ${divYield.toFixed(1)}%`);
    }
  } else {
    details.push('無配当');
  }

  return { score, max: 75, details };
}

function momScore(closes: number[], volumes: number[]): ScoreDetail {
  let score = 0;
  const details: string[] = [];

  const ret5 = periodReturn(closes, 5) * 100;
  const ret20 = periodReturn(closes, 20) * 100;
  const ret60 = periodReturn(closes, 60) * 100;

  if (ret5 > 3) {
    score += 15;
    details.push(`5日リターン +${ret5.toFixed(1)}% ✓`);
  } else if (ret5 > 0) {
    score += 8;
    details.push(`5日リターン +${ret5.toFixed(1)}%`);
  } else {
    details.push(`5日リターン ${ret5.toFixed(1)}%`);
  }

  if (ret20 > 5) {
    score += 20;
    details.push(`20日リターン +${ret20.toFixed(1)}% ✓`);
  } else if (ret20 > 0) {
    score += 10;
    details.push(`20日リターン +${ret20.toFixed(1)}%`);
  } else {
    details.push(`20日リターン ${ret20.toFixed(1)}%`);
  }

  if (ret60 > 10) {
    score += 10;
    details.push(`60日リターン +${ret60.toFixed(1)}% ✓`);
  } else if (ret60 > 0) {
    score += 5;
    details.push(`60日リターン +${ret60.toFixed(1)}%`);
  }

  return { score, max: 45, details };
}

function newsScore(statements: FinancialStatement[]): ScoreDetail {
  let score = 0;
  const details: string[] = [];

  if (statements.length === 0) {
    return { score: 0, max: 45, details: ['決算情報なし'] };
  }

  const latest = statements[0];
  const disclosedDate = new Date(latest.DisclosedDate);
  const daysSince = Math.floor(
    (Date.now() - disclosedDate.getTime()) / (1000 * 60 * 60 * 24)
  );

  if (daysSince <= 7) {
    score += 20;
    details.push(`直近決算開示 ${daysSince}日前 ✓ 最新情報`);
  } else if (daysSince <= 30) {
    score += 10;
    details.push(`決算開示 ${daysSince}日前`);
  } else {
    details.push(`直近決算 ${daysSince}日前`);
  }

  const eps = latest.EarningsPerShare;
  const forecastEps = latest.ForecastEarningsPerShare;
  if (forecastEps !== 0 && eps !== 0) {
    const beat = (eps - forecastEps) / Math.abs(forecastEps);
    if (beat > 0.1) {
      score += 25;
      details.push(`EPS 予想比 +${(beat * 100).toFixed(0)}% 上振れ ✓`);
    } else if (beat > 0.02) {
      score += 12;
      details.push(`EPS 予想比 +${(beat * 100).toFixed(0)}%`);
    } else if (beat < -0.1) {
      details.push(`EPS 予想比 ${(beat * 100).toFixed(0)}% 下振れ ✗`);
    }
  }

  if (latest.OperatingProfit > 0) {
    score += 5;
    details.push(`営業利益 ${(latest.OperatingProfit / 1e8).toFixed(0)}億円`);
  }

  return { score, max: 45, details };
}

export function calculateStockScore(
  info: { code: string; name: string },
  quotes: DailyQuote[],
  statements: FinancialStatement[]
): StockScore {
  if (quotes.length < 5) {
    return {
      code: info.code,
      name: info.name,
      totalScore: 0,
      technical: { score: 0, max: 90, details: ['データ不足'] },
      fundamental: { score: 0, max: 75, details: ['データ不足'] },
      momentum: { score: 0, max: 45, details: ['データ不足'] },
      news: { score: 0, max: 45, details: ['データ不足'] },
      currentPrice: 0,
      priceChange: 0,
      priceChangePct: 0,
      rsi: 50,
      quotes,
    };
  }

  const closes = quotes.map((q) => q.AdjustmentClose || q.Close);
  const volumes = quotes.map((q) => q.AdjustmentVolume || q.Volume);
  const currentPrice = closes[closes.length - 1];
  const prevPrice = closes[closes.length - 2] ?? currentPrice;
  const priceChange = currentPrice - prevPrice;
  const priceChangePct = prevPrice !== 0 ? (priceChange / prevPrice) * 100 : 0;

  const technical = techScore(closes, volumes);
  const fundamental = fundScore(currentPrice, statements);
  const momentum = momScore(closes, volumes);
  const news = newsScore(statements);

  return {
    code: info.code,
    name: info.name,
    totalScore: technical.score + fundamental.score + momentum.score + news.score,
    technical,
    fundamental,
    momentum,
    news,
    currentPrice,
    priceChange,
    priceChangePct,
    rsi: rsi(closes),
    quotes,
  };
}
