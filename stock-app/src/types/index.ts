export interface DailyQuote {
  Date: string;
  Code: string;
  Open: number;
  High: number;
  Low: number;
  Close: number;
  Volume: number;
  AdjustmentClose: number;
  AdjustmentVolume: number;
}

export interface FinancialStatement {
  DisclosedDate: string;
  LocalCode: string;
  TypeOfDocument: string;
  BookValuePerShare: number;
  EarningsPerShare: number;
  ForecastEarningsPerShare: number;
  ResultDividendPerShareAnnual: number | null;
  ForecastDividendPerShareAnnual: number | null;
  NetSales: number;
  OperatingProfit: number;
  Profit: number;
  TotalAssets: number;
  Equity: number;
}

export interface ListedInfo {
  Code: string;
  CompanyName: string;
  CompanyNameEnglish: string;
  Sector17Code: string;
  Sector17CodeName: string;
  MarketCode: string;
  MarketCodeName: string;
}

export interface ScoreDetail {
  score: number;
  max: number;
  details: string[];
}

export interface StockScore {
  code: string;
  name: string;
  totalScore: number;
  technical: ScoreDetail;
  fundamental: ScoreDetail;
  momentum: ScoreDetail;
  news: ScoreDetail;
  currentPrice: number;
  priceChange: number;
  priceChangePct: number;
  rsi: number;
  quotes: DailyQuote[];
}

export interface SellRules {
  stopLoss?: number;
  takeProfit?: number;
  trailingStop?: number;
  daysToHold?: number;
}

export interface Position {
  id: string;
  code: string;
  name: string;
  shares: number;
  buyPrice: number;
  buyDate: string;
  currentPrice: number;
  peakPrice: number;
  sellRules: SellRules;
}

export interface Trade {
  id: string;
  code: string;
  name: string;
  type: 'buy' | 'sell';
  shares: number;
  price: number;
  date: string;
  reason?: string;
  pnl?: number;
  pnlPct?: number;
}
