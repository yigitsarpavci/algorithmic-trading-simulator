"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { SectionHeader, SignalBadge, PriceChange, ConfidenceBadge } from "@/components/shared";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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
  Search, 
  TrendingUp, 
  BarChart2, 
  ArrowRightLeft,
  LayoutGrid,
  List as ListIcon
} from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

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

const mockWatchlist = [
  { id: "1", ticker: "MSFT", type: "Stock", priority: "High", price: 415.20, change: 1.2, volume: "12M", relStrength: 1.05, signal: "BUY" },
  { id: "2", ticker: "NVDA", type: "Stock", priority: "High", price: 124.50, change: 2.4, volume: "85M", relStrength: 1.42, signal: "STRONG_BUY" },
  { id: "3", ticker: "AAPL", type: "Stock", priority: "Medium", price: 220.10, change: -0.5, volume: "45M", relStrength: 0.98, signal: "WAIT" },
];

import { useWebSocket } from "@/hooks/use-websocket";

export default function WatchlistPage() {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [newTicker, setNewTicker] = useState("");
  const [newPriority, setNewPriority] = useState<"High" | "Medium" | "Low">("Medium");
  
  const { lastMessage } = useWebSocket("ws://localhost:8000/api/v1/ws/");

  useEffect(() => {
    if (lastMessage) {
      console.log("WS Message Received:", lastMessage.type);
    }
    if (lastMessage?.type === "PRICE_BATCH_UPDATE") {
      const quotes = lastMessage.payload;
      console.log("Updating items with quotes:", Object.keys(quotes));
      setItems(prev => prev.map(item => {
        const q = quotes[item.ticker];
        if (q) {
          return { 
            ...item, 
            price: q.price !== undefined ? q.price : item.price, 
            change: q.change !== undefined ? q.change : item.change,
            relStrength: q.rs !== undefined ? q.rs : item.relStrength,
            signal: q.signal !== undefined ? q.signal : item.signal
          };
        }
        return item;
      }));
    }
    if (lastMessage?.type === "SIGNAL_GENERATED") {
      setItems(prev => prev.map(item => 
        item.ticker === lastMessage.payload.ticker 
          ? { ...item, signal: lastMessage.payload.type || "BUY" } 
          : item
      ));
    }
  }, [lastMessage]);

  const fetchWatchlist = async () => {
    try {
      setLoading(true);
      const data = await api.get("/watchlist/");
      if (data && data.length > 0) {
        const mapped: WatchlistItem[] = data.map((item: any) => ({
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
    } catch (error) {
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWatchlist();
  }, []);

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
      await api.delete(`/watchlist/${id}`);
      setItems(items.filter(i => i.id !== id));
    } catch (error) {
      console.error("Failed to remove ticker:", error);
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
          <Select value={newPriority} onValueChange={(val: any) => setNewPriority(val)}>
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

