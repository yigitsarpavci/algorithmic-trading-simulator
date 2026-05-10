"use client";

import { 
  TrendingUp, 
  TrendingDown,
  CheckCircle2, 
  Wallet, 
  Activity,
  Zap,
  Trophy,
  Target,
  BarChart3,
  ShieldAlert,
  ArrowDownRight, 
  ArrowUpRight, 
  Clock, 
  Terminal 
} from "lucide-react";
import { useState, useEffect, useRef } from "react";
import { api, getWsBaseUrl } from "@/lib/api";
import { useWebSocket } from "@/hooks/use-websocket";
import { cn } from "@/lib/utils";

function formatCompactCurrency(value: number) {
  if (Math.abs(value) >= 1e6) {
    return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 }).format(value);
  }
  return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatCompactPercent(value: number) {
  if (Math.abs(value) >= 1000) {
    return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 2 }).format(value);
  }
  return value.toFixed(3);
}

export default function DashboardPage() {
  const [stats, setStats] = useState({
    currentBalance: 0,
    totalReturn: 0.0,
    winRate: 0.0,
    closedTrades: 0,
    wins: 0,
    losses: 0,
  });
  const [initialBalance, setInitialBalance] = useState<number | null>(null);
  const [liveSignals, setLiveSignals] = useState<any[]>([]);
  const [openTrades, setOpenTrades] = useState<any[]>([]);
  const [closedTrades, setClosedTrades] = useState<any[]>([]);
  const [lastTradeResult, setLastTradeResult] = useState<"win" | "loss" | null>(null);
  const [riskSettings, setRiskSettings] = useState({ leverage: 15, risk_per_trade: 0.05 });
  const prevBalanceRef = useRef<number | null>(null);

  const [wsUrl, setWsUrl] = useState<string>("");
  const { lastMessage, isConnected } = useWebSocket(wsUrl);

  useEffect(() => {
    setWsUrl(getWsBaseUrl());
  }, []);

  useEffect(() => {
    if (!lastMessage) return;
    
    if (lastMessage.type === "PORTFOLIO_UPDATE") {
      const nl = lastMessage.payload.net_liquidity;
      setInitialBalance(prev => {
        const init = prev !== null ? prev : nl;
        const prevBal = prevBalanceRef.current !== null ? prevBalanceRef.current : nl;
        prevBalanceRef.current = nl;
        if (nl > prevBal + 10) setLastTradeResult("win");
        else if (nl < prevBal - 10) setLastTradeResult("loss");
        setTimeout(() => setLastTradeResult(null), 600);
        
        setStats(s => ({ ...s, currentBalance: nl, totalReturn: init > 0 ? ((nl - init) / init) * 100 : 0 }));
        return init;
      });
    } else if (lastMessage.type === "SIGNAL_GENERATED") {
      setLiveSignals(prev => [lastMessage.payload, ...prev].slice(0, 50));
    } else if (lastMessage.type === "PRICE_BATCH_UPDATE") {
      setOpenTrades(prev => prev.map(trade => {
        const q = lastMessage.payload[trade.ticker];
        return (q?.price) ? { ...trade, current: q.price } : trade;
      }));
    } else if (lastMessage.type === "SYNC_TRIGGER" || lastMessage.type === "SIGNAL_GENERATED") {
      fetchData();
    }
  }, [lastMessage]);

  const fetchData = async () => {
    try {
      const [summary, trades, portfolio] = await Promise.all([
        api.get("/paper-trades/summary"), api.get("/paper-trades/"), api.get("/user/portfolio")
      ]);
      if (summary) setStats(prev => ({ 
        ...prev, 
        winRate: summary.winRate ?? 0, 
        closedTrades: summary.closedTrades ?? 0,
        wins: summary.wins ?? 0,
        losses: summary.losses ?? 0
      }));
      if (portfolio) {
        const nl = portfolio.net_liquidity ?? 0;
        setInitialBalance(prev => {
          const init = prev !== null ? prev : nl;
          setStats(s => ({ ...s, currentBalance: nl, totalReturn: init > 0 ? ((nl - init) / init) * 100 : 0 }));
          if (prevBalanceRef.current === null) prevBalanceRef.current = nl;
          return init;
        });
      }
      if (trades) {
        const mapped = trades.map((t: any) => ({
          id: t.id, ticker: t.ticker, strategy: t.strategy_name ?? "Turbo Scalp", status: t.status,
          entry: Number(t.paper_entry_price ?? 0), current: Number(t.current_price ?? t.paper_entry_price ?? 0),
          exit: Number(t.paper_exit_price ?? 0), pl_pct: Number(t.pnl_percent ?? 0),
          pl_usd: Number(t.pnl_dollar ?? 0), exit_reason: t.exit_reason ?? "",
        }));
        setOpenTrades(mapped.filter((t: any) => t.status === "OPEN" || t.status === "PENDING_TRIGGER"));
        setClosedTrades(mapped.filter((t: any) => t.status?.startsWith("CLOSED")));
      }
    } catch {}
  };

  useEffect(() => {
    fetchData();
    api.get("/settings/").then(res => { if (res) setRiskSettings(res); }).catch(() => {});
  }, []);

  const baseBalance = initialBalance !== null ? initialBalance : 0;
  const totalPnlDollar = stats.currentBalance - baseBalance;
  const wins = closedTrades.filter(t => t.pl_pct > 0).length;
  const losses = closedTrades.filter(t => t.pl_pct <= 0).length;
  
  const grossProfit = closedTrades.filter(t => t.pl_pct > 0).reduce((sum, t) => sum + t.pl_pct, 0);
  const grossLoss = Math.abs(closedTrades.filter(t => t.pl_pct <= 0).reduce((sum, t) => sum + t.pl_pct, 0));
  const profitFactor = grossLoss > 0 ? grossProfit / grossLoss : (grossProfit > 0 ? 99.9 : 0);

  return (
    <div className="min-h-screen bg-[#060606] text-white font-sans selection:bg-emerald-500/30 -m-8 -mb-16 p-6 md:p-8">
      
      {/* ─── STATS BAR ─── */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2.5 mb-8">
        {/* Net Liquidity */}
        <StatCard
          label="Net Liquidity"
          icon={<Wallet className="w-3.5 h-3.5" />}
          glowClass={cn(
            lastTradeResult === "win" ? "animate-flash-green" : lastTradeResult === "loss" ? "animate-flash-red" : "",
            totalPnlDollar >= 0 ? "border-emerald-500/15 animate-glow-green" : "border-rose-500/15 animate-glow-red"
          )}
        >
          <span className="text-xl font-mono font-black tracking-tighter tabular-nums truncate" title={`$${stats.currentBalance.toLocaleString()}`}>
            ${formatCompactCurrency(stats.currentBalance)}
          </span>
        </StatCard>

        {/* Session PnL */}
        <StatCard label="Session PnL" icon={stats.totalReturn >= 0
          ? <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
          : <TrendingDown className="w-3.5 h-3.5 text-rose-400" />
        }>
          <span className={cn("text-xl font-mono font-black tracking-tighter tabular-nums truncate", stats.totalReturn >= 0 ? "text-emerald-400" : "text-rose-400")} title={`${stats.totalReturn}%`}>
            {stats.totalReturn > 0 ? "+" : ""}{formatCompactPercent(stats.totalReturn)}%
          </span>
          <span className={cn("text-[10px] font-mono opacity-40 tabular-nums truncate", totalPnlDollar >= 0 ? "text-emerald-500" : "text-rose-500")} title={`$${totalPnlDollar}`}>
            {totalPnlDollar > 0 ? "+" : ""}${formatCompactCurrency(totalPnlDollar)}
          </span>
        </StatCard>

        {/* Win Rate */}
        <StatCard label="Win Rate" icon={<Trophy className="w-3.5 h-3.5 text-amber-400" />}>
          <span className={cn("text-xl font-mono font-black tracking-tighter tabular-nums",
            stats.closedTrades === 0 ? "text-white/30" : stats.winRate >= 50 ? "text-emerald-400" : "text-rose-400"
          )}>
            {stats.closedTrades === 0 ? "—" : `${stats.winRate.toFixed(1)}%`}
          </span>
          <span className="text-[10px] font-mono text-white/20 tabular-nums">{stats.wins}W / {stats.losses}L</span>
        </StatCard>

        {/* Risk Level */}
        <StatCard label="Leverage" icon={<ShieldAlert className="w-3.5 h-3.5 text-white/30" />}>
          <span className={cn("text-xl font-mono font-black tracking-tighter tabular-nums",
            riskSettings.leverage >= 25 ? "text-rose-400" : riskSettings.leverage >= 10 ? "text-amber-400" : "text-emerald-400"
          )}>
            {riskSettings.leverage}x
          </span>
          <span className="text-[10px] font-mono text-white/20">{(riskSettings.risk_per_trade * 100).toFixed(1)}% risk</span>
        </StatCard>

        {/* Throughput */}
        <StatCard label="Trades" icon={<BarChart3 className="w-3.5 h-3.5 text-blue-400" />}>
          <span className="text-xl font-mono font-black tracking-tighter tabular-nums text-blue-400">{stats.closedTrades}</span>
          <span className="text-[10px] font-mono text-white/20">executed</span>
        </StatCard>
      </div>

      {/* ─── MAIN GRID ─── */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-5">
        
        {/* LEFT: TABLES (9/12) */}
        <div className="xl:col-span-9 space-y-5">
          
          {/* Active Positions */}
          <Panel>
            <PanelHeader title="Active Positions" icon={Activity} count={openTrades.length} accent />
            <div className="overflow-x-auto">
              <table className="w-full text-left min-w-[500px]">
                <thead>
                  <tr className="border-b border-white/5">
                    <TH>Asset</TH>
                    <TH>Strategy</TH>
                    <TH align="right">Entry</TH>
                    <TH align="right">Live</TH>
                    <TH align="right">PnL</TH>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.03]">
                  {openTrades.map((t) => {
                    const pnlPct = t.entry > 0 ? ((t.current - t.entry) / t.entry) * 100 : t.pl_pct;
                    return (
                      <tr key={t.id} className="trade-row group">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2.5">
                            <div className={cn(
                              "w-7 h-7 rounded-md flex items-center justify-center text-[9px] font-black border",
                              pnlPct >= 0 ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" : "bg-rose-500/10 border-rose-500/20 text-rose-400"
                            )}>
                              {t.ticker.replace("-USD", "").substring(0, 3)}
                            </div>
                            <span className="font-bold text-[13px] tracking-tight">{t.ticker}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-[10px] text-white/20 font-medium">{t.strategy}</td>
                        <td className="px-4 py-3 text-right font-mono text-[12px] tabular-nums text-white/30">${t.entry.toLocaleString()}</td>
                        <td className="px-4 py-3 text-right font-mono text-[12px] tabular-nums font-bold">${t.current.toLocaleString()}</td>
                        <td className="px-4 py-3 text-right">
                          <PnLBadge value={pnlPct} usd={(pnlPct / 100) * t.entry * riskSettings.leverage} />
                        </td>
                      </tr>
                    );
                  })}
                  {openTrades.length === 0 && (
                    <tr>
                      <td colSpan={5} className="py-20 text-center">
                        <div className="flex flex-col items-center gap-2 opacity-15">
                          <Target className="w-7 h-7" />
                          <span className="text-[10px] font-black uppercase tracking-widest">Scanning for entries...</span>
                        </div>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Panel>

          {/* Trade History */}
          <Panel>
            <PanelHeader title="Trade History" icon={CheckCircle2} count={closedTrades.length} />
            <div className="max-h-[400px] overflow-y-auto custom-scrollbar">
              <table className="w-full text-left min-w-[500px]">
                <thead className="sticky top-0 bg-[#0a0a0a] z-10">
                  <tr className="border-b border-white/5">
                    <TH>Asset</TH>
                    <TH align="right">PnL</TH>
                    <TH align="right">Exit Reason</TH>
                    <TH align="right">Result</TH>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.03]">
                  {closedTrades.slice(0, 50).map((t) => (
                    <tr key={t.id} className="trade-row">
                      <td className="px-4 py-3 font-bold text-[12px] tracking-tight">{t.ticker}</td>
                      <td className="px-4 py-3 text-right"><PnLBadge value={t.pl_pct} usd={t.pl_usd} small /></td>
                      <td className="px-4 py-3 text-right text-[10px] text-white/20 font-medium">{t.exit_reason || "—"}</td>
                      <td className="px-4 py-3 text-right"><StatusBadge status={t.status} /></td>
                    </tr>
                  ))}
                  {closedTrades.length === 0 && (
                    <tr>
                      <td colSpan={4} className="py-16 text-center opacity-15">
                        <span className="text-[10px] font-black uppercase tracking-widest">No trades settled yet</span>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Panel>
        </div>

        {/* RIGHT SIDEBAR (3/12) */}
        <aside className="xl:col-span-3 space-y-4">
          
          {/* Engine Status */}
          <Panel className={cn(
            isConnected ? "border-emerald-500/15 bg-emerald-500/[0.03]" : "border-rose-500/15 bg-rose-500/[0.03]"
          )}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Zap className={cn("w-4 h-4", isConnected ? "text-emerald-500" : "text-rose-500")} />
                <span className={cn("text-[10px] font-black uppercase tracking-widest", isConnected ? "text-emerald-500" : "text-rose-500")}>
                  {isConnected ? "Engine Active" : "Engine Offline"}
                </span>
              </div>
              <div className={cn("w-2 h-2 rounded-full", isConnected ? "bg-emerald-500 animate-pulse" : "bg-rose-500")} />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <MiniStat label="Open" value={openTrades.length} />
              <MiniStat label="Closed" value={stats.closedTrades} />
            </div>
          </Panel>

          {/* Performance */}
          <Panel>
            <h4 className="text-[10px] font-black uppercase tracking-widest text-white/30 mb-4">Performance</h4>
            <div className="space-y-3">
              <ProgressBar label="Win Rate" value={stats.winRate} max={100} color="emerald" />
              <ProgressBar label="Profit Factor" value={profitFactor} max={3} color="blue" />
            </div>
            <div className="mt-4 pt-3 border-t border-white/5 space-y-2.5">
              <div className="flex justify-between text-[10px]">
                <span className="text-white/25 font-bold uppercase">Best</span>
                <span className="font-mono font-bold text-emerald-400">+{Math.max(...closedTrades.map(t => t.pl_pct), 0).toFixed(2)}%</span>
              </div>
              <div className="flex justify-between text-[10px]">
                <span className="text-white/25 font-bold uppercase">Worst</span>
                <span className="font-mono font-bold text-rose-400">{Math.min(...closedTrades.map(t => t.pl_pct), 0).toFixed(2)}%</span>
              </div>
            </div>
          </Panel>

          {/* Live Order Tape */}
          <Panel className="flex-1 min-h-[350px] flex flex-col">
            <div className="flex items-center justify-between mb-3 border-b border-white/5 pb-3">
              <h4 className="text-[10px] font-black uppercase tracking-widest text-white/30 flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5" /> Live Execution Tape
              </h4>
              <div className="flex items-center gap-1.5 opacity-50">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[8px] uppercase tracking-widest font-bold text-white/50">Streaming</span>
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto space-y-1.5 pr-1 custom-scrollbar">
              {liveSignals.length === 0 ? (
                <div className="h-full flex items-center justify-center text-[10px] uppercase tracking-widest text-white/20 font-bold">
                  Awaiting Signals...
                </div>
              ) : (
                liveSignals.map((sig, i) => (
                  <div key={i} className="flex items-center justify-between py-1.5 px-2 rounded-md bg-white/[0.015] hover:bg-white/[0.03] transition-colors border border-white/[0.02]">
                    <div className="flex items-center gap-3">
                      <span className={cn(
                        "text-[9px] font-bold px-1.5 py-0.5 rounded-sm w-10 text-center shrink-0",
                        sig.type === "BUY" ? "bg-emerald-500/10 text-emerald-400" : "bg-rose-500/10 text-rose-400"
                      )}>
                        {sig.type}
                      </span>
                      <span className="text-[10px] font-mono font-bold text-white/80 w-16 shrink-0">{sig.ticker.replace("-USD", "")}</span>
                    </div>
                    <div className="flex items-center gap-4 text-right">
                      <span className="text-[9px] font-mono text-white/40 hidden 2xl:block w-20 text-right truncate">{sig.strategy}</span>
                      <span className="text-[10px] font-mono font-bold text-white/60 w-20 text-right shrink-0">${Number(sig.price).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 6})}</span>
                      <span className="text-[9px] font-mono text-white/20 w-14 text-right shrink-0">{new Date(sig.timestamp).toLocaleTimeString([], {hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit'})}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </Panel>
        </aside>
      </div>
    </div>
  );
}

// ─── Primitives ───

function StatCard({ label, icon, children, glowClass }: { label: string; icon: React.ReactNode; children: React.ReactNode; glowClass?: string }) {
  return (
    <div className={cn("px-4 py-3.5 bg-white/[0.025] border border-white/[0.06] rounded-xl flex flex-col gap-1 transition-all duration-500", glowClass)}>
      <div className="flex items-center gap-1.5">
        {icon}
        <span className="text-[9px] font-bold uppercase tracking-widest text-white/30">{label}</span>
      </div>
      <div className="flex flex-col">{children}</div>
    </div>
  );
}

function Panel({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("bg-white/[0.02] border border-white/[0.06] rounded-xl p-4", className)}>{children}</div>;
}

function PanelHeader({ title, icon: Icon, count, accent }: { title: string; icon: any; count?: number; accent?: boolean }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center gap-2">
        <Icon className={cn("w-3.5 h-3.5", accent ? "text-emerald-400" : "text-white/30")} />
        <h2 className="text-[11px] font-black uppercase tracking-widest text-white/50">{title}</h2>
      </div>
      {count !== undefined && (
        <span className="text-[10px] font-mono font-bold bg-white/[0.04] px-2 py-0.5 rounded-md text-white/30 tabular-nums">{count}</span>
      )}
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="p-2.5 bg-black/20 rounded-lg">
      <span className="text-[9px] text-white/25 font-bold uppercase block">{label}</span>
      <span className="text-base font-mono font-black tabular-nums">{value}</span>
    </div>
  );
}

function ProgressBar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = Math.min((value / max) * 100, 100);
  const bg = color === "emerald" ? "bg-emerald-500" : color === "blue" ? "bg-blue-500" : "bg-rose-500";
  return (
    <div className="space-y-1">
      <div className="flex justify-between">
        <span className="text-[10px] text-white/25 font-bold uppercase">{label}</span>
        <span className="text-[10px] font-mono font-bold text-white/50">{value.toFixed(1)}{max === 100 ? "%" : "x"}</span>
      </div>
      <div className="h-1 bg-white/[0.04] rounded-full overflow-hidden">
        <div className={cn("h-full rounded-full transition-all duration-1000 ease-out", bg)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function TH({ children, align = "left" }: any) {
  return <th className={cn("px-4 py-3 text-[9px] font-black uppercase tracking-widest text-white/20", align === "right" && "text-right")}>{children}</th>;
}

function StatusBadge({ status }: { status: string }) {
  const label = status?.replace("CLOSED_", "");
  const s = status === "CLOSED_WIN" ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
    : status === "CLOSED_LOSS" ? "bg-rose-500/10 text-rose-400 border-rose-500/20"
    : "bg-amber-500/10 text-amber-400 border-amber-500/20";
  return <span className={cn("text-[9px] font-black uppercase px-1.5 py-0.5 rounded border", s)}>{label}</span>;
}

function PnLBadge({ value, usd, small }: { value: number; usd?: number; small?: boolean }) {
  const v = value ?? 0;
  const pos = v >= 0;
  return (
    <div className="flex flex-col items-end">
      <span className={cn("font-mono font-bold tabular-nums", small ? "text-[11px]" : "text-[13px]", pos ? "text-emerald-400" : "text-rose-400")}>
        {pos ? "+" : ""}{v.toFixed(2)}%
      </span>
      {!small && usd !== undefined && (
        <span className={cn("font-mono text-[10px] opacity-25 tabular-nums", pos ? "text-emerald-500" : "text-rose-500")}>
          {pos ? "+" : ""}${formatCompactCurrency(usd)}
        </span>
      )}
    </div>
  );
}
