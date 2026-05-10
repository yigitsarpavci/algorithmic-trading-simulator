import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle, LucideIcon, Info, Clock, Activity } from "lucide-react";

type SignalType = "STRONG_BUY" | "BUY" | "BUY_IF_TRIGGER" | "WAIT" | "AVOID";

interface SignalBadgeProps {
  signal: SignalType;
  className?: string;
}

export function SignalBadge({ signal, className }: SignalBadgeProps) {
  const variants: Record<SignalType, string> = {
    STRONG_BUY: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
    BUY: "bg-green-500/10 text-green-400 border-green-500/20",
    BUY_IF_TRIGGER: "bg-blue-500/15 text-blue-400 border-blue-500/20",
    WAIT: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    AVOID: "bg-rose-500/10 text-rose-400 border-rose-500/20",
  };

  return (
    <Badge variant="outline" className={cn("font-bold tracking-tight px-2 py-0.5 rounded", variants[signal], className)}>
      {signal?.replace(/_/g, " ") || "N/A"}
    </Badge>
  );
}

interface ConfidenceBadgeProps {
  score: number;
  className?: string;
}

export function ConfidenceBadge({ score, className }: ConfidenceBadgeProps) {
  let color = "text-muted-foreground";
  if (score >= 80) color = "text-emerald-400";
  else if (score >= 60) color = "text-blue-400";
  else if (score >= 40) color = "text-amber-400";
  else color = "text-rose-400";

  return (
    <div className={cn("text-[10px] font-bold uppercase tracking-widest flex items-center gap-1.5", className)}>
      <div className={cn("w-1 h-1 rounded-full bg-current shadow-[0_0_5px_currentColor]", color)} />
      {score}% CONF.
    </div>
  );
}

interface PriceChangeProps {
  value: number;
  isPercent?: boolean;
  className?: string;
}

export function PriceChange({ value, isPercent = true, className }: PriceChangeProps) {
  const isPositive = value > 0;
  const isZero = value === 0;

  return (
    <span className={cn(
      "font-mono text-sm font-bold tabular-nums",
      isPositive ? "text-emerald-400" : isZero ? "text-muted-foreground" : "text-rose-400",
      className
    )}>
      {isPositive ? "+" : ""}{Number(value ?? 0).toFixed(2)}{isPercent ? "%" : ""}
    </span>
  );
}

interface MetricCardProps {
  title: string;
  value: string | number;
  subValue?: string;
  icon?: any;
  trend?: "up" | "down" | "neutral";
}

export function MetricCard({ title, value, subValue, icon: Icon, trend }: MetricCardProps) {
  return (
    <Card className="bg-card/40 border-border hover:bg-card/60 transition-colors group">
      <CardContent className="p-5 flex items-center gap-4">
        <div className="p-2.5 rounded-lg bg-muted/50 border border-border/50">
          {Icon && <Icon className="w-5 h-5 text-muted-foreground" />}
        </div>
        <div className="flex-1 space-y-0.5">
          <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/60">{title}</p>
          <div className="flex items-baseline gap-2">
            <h4 className="text-2xl font-bold tracking-tight">{value}</h4>
            {trend && (
              <span className={cn(
                "text-[10px] font-bold",
                trend === "up" ? "text-emerald-500" : trend === "down" ? "text-destructive" : "text-muted-foreground"
              )}>
                {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"}
              </span>
            )}
          </div>
          {subValue && <p className="text-[10px] text-muted-foreground/50 font-medium">{subValue}</p>}
        </div>
      </CardContent>
    </Card>
  );
}

export function RiskWarningBox() {
  return (
    <div className="bg-amber-500/5 border border-amber-500/10 rounded-xl p-5 flex gap-4 items-start">
      <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
      <div className="space-y-1">
        <h4 className="text-xs font-bold uppercase tracking-wider text-amber-500/90">Institutional Risk Disclosure</h4>
        <p className="text-[10px] text-muted-foreground leading-relaxed font-medium">
          AlphaTrigger AI is a simulation terminal. Signals are research-based and hypothetical. 
          Trading involves risk. Past performance does not guarantee future results. 
        </p>
      </div>
    </div>
  );
}

export function SectionHeader({ title, subtitle, icon: Icon, children }: { title: string; subtitle?: string; icon?: LucideIcon; children?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between mb-8">
      <div className="flex items-center gap-3">
        {Icon && (
          <div className="p-2 bg-primary/10 rounded-lg">
            <Icon className="w-5 h-5 text-primary" />
          </div>
        )}
        <div>
          <h2 className="text-xl font-bold tracking-tight uppercase">{title}</h2>
          {subtitle && <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-widest opacity-60 mt-0.5">{subtitle}</p>}
        </div>
      </div>
      <div className="flex items-center gap-3">
        {children}
      </div>
    </div>
  );
}

interface SignalCardProps {
  ticker: string;
  name: string;
  price: number;
  signal: SignalType;
  confidence: number;
  entry: number;
  stopLoss: number;
  takeProfit: number;
  amount: string;
  timeframe: string;
  strategy?: string;
}

import { useState, useEffect, useRef } from "react";

export function SignalCard(props: SignalCardProps) {
  const [flash, setFlash] = useState<"up" | "down" | null>(null);
  const prevPrice = useRef(props.price);

  useEffect(() => {
    if (props.price > prevPrice.current) {
      setFlash("up");
      const timer = setTimeout(() => setFlash(null), 2000);
      return () => clearTimeout(timer);
    } else if (props.price < prevPrice.current) {
      setFlash("down");
      const timer = setTimeout(() => setFlash(null), 2000);
      return () => clearTimeout(timer);
    }
    prevPrice.current = props.price;
  }, [props.price]);

  return (
    <Card className="group relative overflow-hidden bg-card/40 border-border hover:bg-card/60 transition-all duration-300">
      <div className="absolute top-0 left-0 w-1 h-full bg-primary/20 group-hover:bg-primary transition-colors" />
      
      <CardContent className="p-5">
        <div className="flex justify-between items-start mb-4">
          <div className="space-y-0.5">
            <h3 className="text-xl font-bold tracking-tight">{props.ticker}</h3>
            <p className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground/60">{props.name}</p>
          </div>
          <div className="text-right">
            <p className={cn(
              "text-lg font-mono font-bold tabular-nums transition-colors",
              flash === "up" ? "animate-price-up text-emerald-400" : 
              flash === "down" ? "animate-price-down text-rose-400" : ""
            )}>
              ${(props.price ?? 0).toFixed(2)}
            </p>
            <SignalBadge signal={props.signal} className="text-[8px] h-4" />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 py-3 border-y border-border/50 text-center">
          <div className="space-y-0.5">
            <p className="text-[9px] uppercase font-bold text-muted-foreground/50">Entry</p>
            <p className="text-xs font-mono font-bold">${(props.entry ?? 0).toFixed(2)}</p>
          </div>
          <div className="space-y-0.5">
            <p className="text-[9px] uppercase font-bold text-muted-foreground/50">Stop</p>
            <p className="text-xs font-mono font-bold text-destructive/80">${(props.stopLoss ?? 0).toFixed(2)}</p>
          </div>
          <div className="space-y-0.5">
            <p className="text-[9px] uppercase font-bold text-muted-foreground/50">Target</p>
            <p className="text-xs font-mono font-bold text-emerald-500/80">${(props.takeProfit ?? 0).toFixed(2)}</p>
          </div>
        </div>

        <div className="mt-4">
          <div className="flex justify-between items-center mb-1.5">
            <span className="text-[10px] font-bold text-muted-foreground/70 uppercase">Confidence</span>
            <span className="text-[10px] font-mono font-bold">{props.confidence}%</span>
          </div>
          <div className="h-1 w-full bg-muted/30 rounded-full overflow-hidden">
            <div 
              className="h-full bg-primary transition-all duration-1000" 
              style={{ width: `${props.confidence}%` }} 
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
