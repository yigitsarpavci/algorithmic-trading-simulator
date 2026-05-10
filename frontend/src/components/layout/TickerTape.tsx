"use client";

import { useEffect, useState } from "react";
import { useWebSocket } from "@/hooks/use-websocket";

export function TickerTape() {
  const [prices, setPrices] = useState<Record<string, any>>({});
  const { lastMessage } = useWebSocket("ws://localhost:8000/api/v1/ws/");

  useEffect(() => {
    if (lastMessage?.type === "PRICE_BATCH_UPDATE") {
      setPrices(prev => ({ ...prev, ...lastMessage.payload }));
    }
  }, [lastMessage]);

  const tickers = Object.keys(prices).filter(t => prices[t] && typeof prices[t].price === 'number');

  if (tickers.length === 0) return null;

  return (
    <div className="fixed bottom-0 left-0 w-full h-8 bg-black/80 backdrop-blur-md border-t border-primary/20 flex items-center overflow-hidden z-50">
      <div className="flex animate-marquee whitespace-nowrap py-1">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="flex shrink-0">
            {tickers.map(t => {
              const p = Number(prices[t]?.price ?? 0);
              const c = Number(prices[t]?.change ?? 0);
              return (
                <div key={`${i}-${t}`} className="flex items-center gap-2 mx-6">
                  <span className="text-[10px] font-bold text-white uppercase">{t}</span>
                  <span className="text-[10px] font-mono font-bold text-primary">${p.toFixed(2)}</span>
                  <span className={`text-[10px] font-mono font-bold ${c >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {c >= 0 ? '+' : ''}{c.toFixed(2)}%
                  </span>
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
