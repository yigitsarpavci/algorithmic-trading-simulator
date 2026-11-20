// Messages pushed by the backend WebSocket (see backend/app/api/api_v1/endpoints/ws.py).

export interface QuoteUpdate {
  price?: number;
  change?: number;
  rs?: number;
  signal?: string;
}

export type QuoteBatch = Record<string, QuoteUpdate>;

export interface PortfolioUpdatePayload {
  net_liquidity: number;
}

export interface SignalPayload {
  type: string;
  ticker: string;
  strategy?: string;
  price: number | string;
  timestamp: string | number;
}

export type WsMessage =
  | { type: "PORTFOLIO_UPDATE"; payload: PortfolioUpdatePayload }
  | { type: "SIGNAL_GENERATED"; payload: SignalPayload }
  | { type: "PRICE_BATCH_UPDATE"; payload: QuoteBatch }
  | { type: "SYNC_TRIGGER"; payload?: unknown };
