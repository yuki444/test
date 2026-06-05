import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { StockScore, Position, Trade, SellRules } from '../types';
import { STOCK_UNIVERSE } from '../data/universe';
import { getIdToken, getDailyQuotes, getFinancialStatements, getDateRange } from '../api/jquants';
import { calculateStockScore } from '../utils/scoring';

const REFRESH_TOKEN = process.env.EXPO_PUBLIC_JQUANTS_REFRESH_TOKEN ?? '';
const INITIAL_CASH = 5_000_000;
const CACHE_KEY = 'rankings_cache';
const PORTFOLIO_KEY = 'portfolio_data';
const CACHE_TTL_MS = 12 * 60 * 60 * 1000; // 12h

interface StoreState {
  // Market data
  rankings: StockScore[];
  lastUpdated: number | null;
  isLoading: boolean;
  loadingProgress: number;
  loadingStatus: string;
  error: string | null;

  // Portfolio
  cash: number;
  positions: Position[];
  tradeHistory: Trade[];
  autoBuy: boolean;

  // Actions
  refreshRankings: () => Promise<void>;
  loadFromCache: () => Promise<void>;
  buyStock: (score: StockScore, shares: number, rules: SellRules) => void;
  sellPosition: (positionId: string, currentPrice: number, reason: string) => void;
  updatePositionPrices: (prices: Record<string, number>) => void;
  checkSellRules: () => void;
  setAutoBuy: (v: boolean) => void;
  buyTop10: () => void;
  resetPortfolio: () => void;
}

async function savePortfolio(
  cash: number,
  positions: Position[],
  tradeHistory: Trade[]
) {
  await AsyncStorage.setItem(
    PORTFOLIO_KEY,
    JSON.stringify({ cash, positions, tradeHistory })
  );
}

export const useStore = create<StoreState>((set, get) => ({
  rankings: [],
  lastUpdated: null,
  isLoading: false,
  loadingProgress: 0,
  loadingStatus: '',
  error: null,

  cash: INITIAL_CASH,
  positions: [],
  tradeHistory: [],
  autoBuy: true,

  loadFromCache: async () => {
    try {
      const [cacheRaw, portfolioRaw] = await Promise.all([
        AsyncStorage.getItem(CACHE_KEY),
        AsyncStorage.getItem(PORTFOLIO_KEY),
      ]);

      if (cacheRaw) {
        const { rankings, lastUpdated } = JSON.parse(cacheRaw);
        const age = Date.now() - lastUpdated;
        if (age < CACHE_TTL_MS) {
          set({ rankings, lastUpdated });
        }
      }

      if (portfolioRaw) {
        const { cash, positions, tradeHistory } = JSON.parse(portfolioRaw);
        set({ cash, positions: positions ?? [], tradeHistory: tradeHistory ?? [] });
      }
    } catch (_) {
      // ignore cache errors
    }
  },

  refreshRankings: async () => {
    set({ isLoading: true, error: null, loadingProgress: 0 });
    try {
      set({ loadingStatus: 'APIトークン取得中...' });
      const idToken = await getIdToken(REFRESH_TOKEN);

      const { from, to } = getDateRange(120);
      const scores: StockScore[] = [];

      for (let i = 0; i < STOCK_UNIVERSE.length; i++) {
        const stock = STOCK_UNIVERSE[i];
        set({
          loadingStatus: `${stock.name} を分析中... (${i + 1}/${STOCK_UNIVERSE.length})`,
          loadingProgress: (i + 1) / STOCK_UNIVERSE.length,
        });

        try {
          const [quotes, statements] = await Promise.all([
            getDailyQuotes(idToken, stock.code, from, to),
            getFinancialStatements(idToken, stock.code),
          ]);

          const score = calculateStockScore(stock, quotes, statements);
          if (score.currentPrice > 0) {
            scores.push(score);
          }
        } catch (_) {
          // skip failed stocks
        }

        // small delay to avoid rate limiting
        await new Promise((r) => setTimeout(r, 100));
      }

      scores.sort((a, b) => b.totalScore - a.totalScore);
      const lastUpdated = Date.now();

      set({ rankings: scores, lastUpdated, isLoading: false, loadingStatus: '' });

      await AsyncStorage.setItem(
        CACHE_KEY,
        JSON.stringify({ rankings: scores, lastUpdated })
      );

      // auto buy top10
      if (get().autoBuy && scores.length > 0) {
        get().buyTop10();
      }
    } catch (e) {
      set({
        isLoading: false,
        error: e instanceof Error ? e.message : 'データ取得に失敗しました',
        loadingStatus: '',
      });
    }
  },

  buyStock: (score: StockScore, shares: number, rules: SellRules) => {
    const state = get();
    const cost = score.currentPrice * shares;
    if (cost > state.cash) return;

    const position: Position = {
      id: `${score.code}-${Date.now()}`,
      code: score.code,
      name: score.name,
      shares,
      buyPrice: score.currentPrice,
      buyDate: new Date().toISOString().split('T')[0],
      currentPrice: score.currentPrice,
      peakPrice: score.currentPrice,
      sellRules: rules,
    };

    const trade: Trade = {
      id: `trade-${Date.now()}`,
      code: score.code,
      name: score.name,
      type: 'buy',
      shares,
      price: score.currentPrice,
      date: new Date().toISOString().split('T')[0],
    };

    const newCash = state.cash - cost;
    const newPositions = [...state.positions, position];
    const newHistory = [trade, ...state.tradeHistory];

    set({ cash: newCash, positions: newPositions, tradeHistory: newHistory });
    savePortfolio(newCash, newPositions, newHistory);
  },

  sellPosition: (positionId: string, currentPrice: number, reason: string) => {
    const state = get();
    const position = state.positions.find((p) => p.id === positionId);
    if (!position) return;

    const proceeds = currentPrice * position.shares;
    const pnl = proceeds - position.buyPrice * position.shares;
    const pnlPct = (pnl / (position.buyPrice * position.shares)) * 100;

    const trade: Trade = {
      id: `trade-${Date.now()}`,
      code: position.code,
      name: position.name,
      type: 'sell',
      shares: position.shares,
      price: currentPrice,
      date: new Date().toISOString().split('T')[0],
      reason,
      pnl,
      pnlPct,
    };

    const newCash = state.cash + proceeds;
    const newPositions = state.positions.filter((p) => p.id !== positionId);
    const newHistory = [trade, ...state.tradeHistory];

    set({ cash: newCash, positions: newPositions, tradeHistory: newHistory });
    savePortfolio(newCash, newPositions, newHistory);
  },

  updatePositionPrices: (prices: Record<string, number>) => {
    const state = get();
    const updated = state.positions.map((p) => {
      const price = prices[p.code];
      if (!price) return p;
      return {
        ...p,
        currentPrice: price,
        peakPrice: Math.max(p.peakPrice, price),
      };
    });
    set({ positions: updated });
    get().checkSellRules();
  },

  checkSellRules: () => {
    const state = get();
    for (const pos of state.positions) {
      const { currentPrice, buyPrice, peakPrice, sellRules } = pos;
      const changePct = (currentPrice - buyPrice) / buyPrice;

      if (sellRules.stopLoss !== undefined && changePct <= -sellRules.stopLoss / 100) {
        get().sellPosition(pos.id, currentPrice, `損切り(-${sellRules.stopLoss}%)`);
        continue;
      }

      if (sellRules.takeProfit !== undefined && changePct >= sellRules.takeProfit / 100) {
        get().sellPosition(pos.id, currentPrice, `利確(+${sellRules.takeProfit}%)`);
        continue;
      }

      if (sellRules.trailingStop !== undefined) {
        const drawdown = (peakPrice - currentPrice) / peakPrice;
        if (drawdown >= sellRules.trailingStop / 100) {
          get().sellPosition(pos.id, currentPrice, `トレーリングストップ`);
          continue;
        }
      }

      if (sellRules.daysToHold !== undefined) {
        const buyDate = new Date(pos.buyDate);
        const daysSince = Math.floor(
          (Date.now() - buyDate.getTime()) / (1000 * 60 * 60 * 24)
        );
        if (daysSince >= sellRules.daysToHold) {
          get().sellPosition(pos.id, currentPrice, `保有期間満了(${sellRules.daysToHold}日)`);
        }
      }
    }
  },

  buyTop10: () => {
    const state = get();
    const top10 = state.rankings.slice(0, 10);
    if (top10.length === 0 || state.cash < 10_000) return;

    const budgetPerStock = Math.floor(state.cash / top10.length / 1000) * 1000;
    const defaultRules: SellRules = { stopLoss: 8, takeProfit: 25, daysToHold: 30 };

    for (const stock of top10) {
      if (stock.currentPrice <= 0) continue;
      const alreadyOwned = state.positions.some((p) => p.code === stock.code);
      if (alreadyOwned) continue;

      const shares = Math.floor(budgetPerStock / stock.currentPrice / 100) * 100;
      if (shares <= 0) continue;

      get().buyStock(stock, shares, defaultRules);
    }
  },

  setAutoBuy: (v) => set({ autoBuy: v }),

  resetPortfolio: () => {
    const newState = { cash: INITIAL_CASH, positions: [], tradeHistory: [] };
    set(newState);
    savePortfolio(newState.cash, [], []);
  },
}));
