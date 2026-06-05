import { DailyQuote, FinancialStatement, ListedInfo } from '../types';

const BASE_URL = 'https://api.jquants.com/v1';

let cachedIdToken: string | null = null;
let tokenExpiry: number = 0;

export async function getIdToken(refreshToken: string): Promise<string> {
  if (cachedIdToken && Date.now() < tokenExpiry) {
    return cachedIdToken;
  }

  const res = await fetch(`${BASE_URL}/token/auth_refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refreshtoken: refreshToken }),
  });

  if (!res.ok) {
    throw new Error(`Auth failed: ${res.status}`);
  }

  const data = await res.json();
  if (!data.idToken) {
    throw new Error('No idToken in response');
  }

  cachedIdToken = data.idToken;
  tokenExpiry = Date.now() + 23 * 60 * 60 * 1000; // 23h
  return data.idToken;
}

export async function getDailyQuotes(
  idToken: string,
  code: string,
  from: string,
  to: string
): Promise<DailyQuote[]> {
  const url = `${BASE_URL}/prices/daily_quotes?code=${code}&from=${from}&to=${to}`;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${idToken}` },
  });

  if (!res.ok) return [];

  const data = await res.json();
  const quotes: DailyQuote[] = (data.daily_quotes || []).sort(
    (a: DailyQuote, b: DailyQuote) => a.Date.localeCompare(b.Date)
  );
  return quotes;
}

export async function getFinancialStatements(
  idToken: string,
  code: string
): Promise<FinancialStatement[]> {
  const url = `${BASE_URL}/fins/statements?code=${code}`;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${idToken}` },
  });

  if (!res.ok) return [];

  const data = await res.json();
  const statements: FinancialStatement[] = (data.statements || []).sort(
    (a: FinancialStatement, b: FinancialStatement) =>
      b.DisclosedDate.localeCompare(a.DisclosedDate)
  );
  return statements;
}

export async function getListedInfo(
  idToken: string,
  code?: string
): Promise<ListedInfo[]> {
  const url = code
    ? `${BASE_URL}/listed/info?code=${code}`
    : `${BASE_URL}/listed/info`;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${idToken}` },
  });

  if (!res.ok) return [];

  const data = await res.json();
  return data.info || [];
}

export function getDateRange(daysBack: number): { from: string; to: string } {
  const to = new Date();
  const from = new Date();
  from.setDate(from.getDate() - daysBack);

  const fmt = (d: Date) => d.toISOString().split('T')[0].replace(/-/g, '-');
  return { from: fmt(from), to: fmt(to) };
}
