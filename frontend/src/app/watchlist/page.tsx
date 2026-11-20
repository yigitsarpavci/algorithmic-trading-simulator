"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import { useWsUrl } from "@/hooks/use-ws-url";
import type { WsMessage } from "@/types/ws";
import { cn } from "@/lib/utils";
import { SectionHeader, SignalBadge, PriceChange } from "@/components/shared";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import {
  Plus,
  Trash2,
  Search
} from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from "@/components/ui/select";

import { useWebSocket } from "@/hooks/use-websocket";

interface ApiWatchlistItem {
  id?: number | string;
  ticker?: string;
  asset_type?: string;
  type?: string;
  priority?: string;
  price?: number;
  change?: number;
  volume?: string;
  rel_strength?: number;
  relStrength?: number;
  signal?: string;
}

interface WatchlistItem {
  id: string;
  ticker: string;
  type: "Stock" | "ETF";
  priority: "High" | "Medium" | "Low";
  price: number;
  change: number;
  volume: string;
  relStrength: number;
  signal: "BUY" | "WAIT" | "AVOID" | "STRONG_BUY" | "BUY_IF_TRIGGER";
}


export default function WatchlistPage() {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [newTicker, setNewTicker] = useState("");
  const [newPriority, setNewPriority] = useState<"High" | "Medium" | "Low">("Medium");
  
  const wsUrl = useWsUrl();

  const handleMessage = useCallback((message: WsMessage) => {
    if (message.type === "PRICE_BATCH_UPDATE") {
      const quotes = message.payload;
      setItems(prev => prev.map(item => {
        const q = quotes[item.ticker];
        if (q) {
          return { 
            ...item, 
            price: q.price !== undefined ? q.price : item.price, 
            change: q.change !== undefined ? q.change : item.change,
            relStrength: q.rs !== undefined ? q.rs : item.relStrength,
            signal: (q.signal !== undefined ? q.signal : item.signal) as WatchlistItem["signal"]
          };
        }
        return item;
      }));
    }
    if (message.type === "SIGNAL_GENERATED") {
      setItems(prev => prev.map(item => 
        item.ticker === message.payload.ticker 
          ? { ...item, signal: (message.payload.type || "BUY") as WatchlistItem["signal"] } 
          : item
      ));
    }
  }, []);

  useWebSocket(wsUrl, handleMessage);

  const [refreshKey, setRefreshKey] = useState(0);
  const fetchWatchlist = useCallback(() => setRefreshKey((k) => k + 1), []);

  useEffect(() => {
    let active = true;
    (api.get("/watchlist/") as Promise<ApiWatchlistItem[] | null>)
      .then((data) => {
        if (!active) return;
        if (data && data.length > 0) {
          const mapped: WatchlistItem[] = data.map((item) => ({
            id: String(item.id ?? Math.random()),
            ticker: item.ticker ?? "???",
            type: (item.asset_type ?? item.type ?? "Stock") as "Stock" | "ETF",
            priority: (item.priority ?? "Medium") as "High" | "Medium" | "Low",
            price: Number(item.price ?? 0),
            change: Number(item.change ?? 0),
            volume: item.volume ?? "-",
            relStrength: Number(item.rel_strength ?? item.relStrength ?? 1.0),
            signal: (item.signal ?? "WAIT") as WatchlistItem["signal"],
          }));
          setItems(mapped);
        } else {
          setItems([]);
        }
      })
      .catch(() => {
        if (active) setItems([]);
      });
    return () => {
      active = false;
    };
  }, [refreshKey]);

  const addItem = async () => {
    if (!newTicker) return;
    try {
      const resp = await api.post("/watchlist/", {
        ticker: newTicker.toUpperCase(),
        asset_type: "Stock",
        priority: newPriority
      });
      if (resp) {
        fetchWatchlist();
        setNewTicker("");
      }
    } catch (error) {
      console.error("Failed to add ticker:", error);
    }
  };

  const removeItem = async (id: string) => {
    try {
      // Optimistically remove from UI
      setItems(prev => prev.filter(i => i.id !== id));
      await api.delete(`/watchlist/${id}`);
    } catch (error) {
      console.error("Failed to remove ticker:", error);
      // Re-fetch if it failed to keep UI in sync with server
      fetchWatchlist();
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      <SectionHeader title="Portfolio Watchlist" subtitle="Institutional asset monitoring" />

      <div className="flex flex-col md:flex-row gap-4 items-center bg-card/40 p-4 rounded-xl border border-border">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
          <Input 
            placeholder="Add ticker (e.g. MSFT)..." 
            value={newTicker}
            onChange={(e) => setNewTicker(e.target.value)}
            className="pl-9 h-10 bg-transparent border-none focus-visible:ring-0 text-sm font-bold uppercase"
          />
        </div>
        
        <div className="w-32">
          <Select value={newPriority} onValueChange={(val) => setNewPriority(val as "High" | "Medium" | "Low")}>
            <SelectTrigger className="h-10 bg-muted/30 border-border text-[10px] font-bold uppercase tracking-widest">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="High">High Priority</SelectItem>
              <SelectItem value="Medium">Medium Priority</SelectItem>
              <SelectItem value="Low">Low Priority</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Button onClick={addItem} className="h-10 px-6 gap-2 text-[10px] font-bold uppercase tracking-widest">
          <Plus className="w-3.5 h-3.5" />
          Add
        </Button>
      </div>

      <div className="bg-card/20 border border-border rounded-xl overflow-hidden backdrop-blur-sm">
        <Table>
          <TableHeader className="bg-muted/30">
            <TableRow className="hover:bg-transparent border-border/50">
              <TableHead className="text-[10px] font-bold uppercase tracking-widest h-10">Ticker</TableHead>
              <TableHead className="text-[10px] font-bold uppercase tracking-widest h-10">Priority</TableHead>
              <TableHead className="text-[10px] font-bold uppercase tracking-widest h-10">Price</TableHead>
              <TableHead className="text-[10px] font-bold uppercase tracking-widest h-10">Change</TableHead>
              <TableHead className="text-[10px] font-bold uppercase tracking-widest h-10">RS</TableHead>
              <TableHead className="text-[10px] font-bold uppercase tracking-widest h-10">Signal</TableHead>
              <TableHead className="text-right h-10"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length > 0 ? (
              items.map((item) => (
                <TableRow key={item.id} className="hover:bg-muted/30 transition-colors border-border/50">
                  <TableCell className="font-bold text-sm">{item.ticker}</TableCell>
                  <TableCell>
                    <span className={cn(
                      "text-[9px] font-bold uppercase px-1.5 py-0.5 rounded border",
                      item.priority === "High" ? "bg-primary/10 text-primary border-primary/20" :
                      item.priority === "Medium" ? "bg-blue-500/10 text-blue-500 border-blue-500/20" :
                      "bg-zinc-500/10 text-zinc-500 border-zinc-500/20"
                    )}>
                      {item.priority}
                    </span>
                  </TableCell>
                  <TableCell className="font-mono text-xs">${(item.price ?? 0).toFixed(2)}</TableCell>
                  <TableCell>
                    <PriceChange value={item.change} className="text-xs" />
                  </TableCell>
                  <TableCell className="text-xs font-mono">{(item.relStrength ?? 0).toFixed(2)}</TableCell>
                  <TableCell>
                    <SignalBadge signal={item.signal} className="text-[8px] h-4" />
                  </TableCell>
                  <TableCell className="text-right">
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      onClick={() => removeItem(item.id)}
                      className="h-8 w-8 text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={7} className="h-64 text-center">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/40">Watchlist Empty</p>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

