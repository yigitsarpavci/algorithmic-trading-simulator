"use client";

import { useState, useEffect } from "react";
import { 
  SectionHeader, 
  RiskWarningBox 
} from "@/components/shared";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { 
  ShieldCheck, 
  Wallet, 
  Settings2, 
  Calculator, 
  AlertTriangle,
  Zap,
  Percent,
  RefreshCcw,
  Timer,
  Check,
  Loader2
} from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function RiskSettingsPage() {
  const [settings, setSettings] = useState({
    leverage: 15,
    commission_rate: 0.0004,
    risk_per_trade: 0.05,
    tp_pct: 0.015,
    sl_pct: 0.01,
    hft_cycle_seconds: 2.0
  });
  const [balance, setBalance] = useState(10_000_000);
  const [saving, setSaving] = useState(false);
  const [deployed, setDeployed] = useState(false);
  const [isManualMode, setIsManualMode] = useState(false);

  useEffect(() => {
    api.get("/settings").then(res => {
      if (res) setSettings(res);
    });
    api.get("/user/portfolio").then(res => {
      if (res) setBalance(res.net_liquidity || 10_000_000);
    });
  }, []);

  const handleDeploy = async () => {
    try {
      setSaving(true);
      setDeployed(false);
      await Promise.all([
        api.post("/settings/update", settings),
        api.post("/user/portfolio/reset", { value: balance }) 
      ]);
      await new Promise(r => setTimeout(r, 600));
      setDeployed(true);
      setTimeout(() => setDeployed(false), 3000);
    } catch (error) {
      console.error("Deploy failed:", error);
    } finally {
      setSaving(false);
    }
  };

  const dollarRisk = (balance * settings.risk_per_trade);
  const maxExposure = balance * settings.leverage;
  
  const currentProfile = isManualMode ? "manual" : (settings.leverage >= 50 ? "aggressive" : settings.leverage === 20 ? "balanced" : "conservative");

  return (
    <div className="space-y-8 pb-12 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-end gap-6 pb-6 border-b border-border">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight">RISK CONTROL</h1>
          <p className="text-xs text-muted-foreground font-medium uppercase tracking-[0.2em]">Institutional Risk Management Engine</p>
        </div>
        <Button 
          onClick={handleDeploy}
          disabled={saving}
          className={cn(
            "h-10 px-8 text-[10px] font-bold uppercase tracking-widest transition-all shadow-lg",
            deployed 
              ? "bg-emerald-600 text-white hover:bg-emerald-600 shadow-emerald-500/20" 
              : "bg-primary text-primary-foreground hover:opacity-90 shadow-primary/20"
          )}
        >
          {saving ? (
            <><Loader2 className="w-3.5 h-3.5 mr-2 animate-spin" /> Deploying...</>
          ) : deployed ? (
            <><Check className="w-3.5 h-3.5 mr-2" /> Deployed ✓</>
          ) : (
            "Deploy Parameters"
          )}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          
          {/* Execution Parameters */}
          <Card className="bg-card/40 border-border">
            <CardHeader className="border-b border-border/50 py-4">
              <CardTitle className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                <Settings2 className="w-3.5 h-3.5" />
                Execution Parameters
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-2">
                  <Label className="text-[10px] font-bold uppercase text-muted-foreground/60">Virtual Capital ($)</Label>
                  <Input 
                    type="number" 
                    value={balance} 
                    onChange={(e) => setBalance(Number(e.target.value))}
                    className="bg-muted/20 border-border h-10 font-mono text-sm"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-[10px] font-bold uppercase text-muted-foreground/60">Risk Profile</Label>
                  <Select 
                    value={currentProfile}
                    onValueChange={(val) => {
                      if (val === "manual") {
                        setIsManualMode(true);
                      } else {
                        setIsManualMode(false);
                        if (val === "conservative") setSettings(s => ({...s, leverage: 5, risk_per_trade: 0.02, tp_pct: 0.02, sl_pct: 0.01, hft_cycle_seconds: 5}));
                        if (val === "balanced") setSettings(s => ({...s, leverage: 20, risk_per_trade: 0.05, tp_pct: 0.015, sl_pct: 0.008, hft_cycle_seconds: 3}));
                        if (val === "aggressive") setSettings(s => ({...s, leverage: 50, risk_per_trade: 0.10, tp_pct: 0.01, sl_pct: 0.005, hft_cycle_seconds: 1}));
                      }
                    }}
                  >
                    <SelectTrigger className="bg-muted/20 border-border h-10 text-xs font-bold">
                      <SelectValue placeholder="Select Profile" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="conservative">Conservative (5x)</SelectItem>
                      <SelectItem value="balanced">Balanced (20x)</SelectItem>
                      <SelectItem value="aggressive">HFT Hyper (50x)</SelectItem>
                      <SelectItem value="manual">Manual Custom</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              {!isManualMode && (
                <div className="mt-4 p-3 bg-primary/10 border border-primary/20 rounded-md">
                  <p className="text-[11px] font-medium text-primary/80">
                    System presets are active. To manually override these parameters, please select "Manual Custom" from the profile dropdown.
                  </p>
                </div>
              )}

              <div className={cn("space-y-10 pt-4 transition-opacity", !isManualMode && "opacity-50 pointer-events-none")}>
                {/* LEVERAGE */}
                <div className="space-y-4">
                  <div className="flex justify-between items-end">
                    <div className="flex items-center gap-2">
                      <Zap className="w-3.5 h-3.5 text-primary" />
                      <Label className="text-[10px] font-bold uppercase text-muted-foreground/60">Leverage Multiplier</Label>
                    </div>
                    <span className={cn(
                      "text-sm font-mono font-bold",
                      settings.leverage >= 25 ? "text-rose-400" : settings.leverage >= 10 ? "text-amber-400" : "text-primary"
                    )}>{settings.leverage}x</span>
                  </div>
                  <Slider 
                    value={[settings.leverage]} 
                    min={1} max={100} step={1} 
                    onValueChange={(val) => setSettings({...settings, leverage: val[0]})}
                  />
                  {settings.leverage >= 25 && (
                    <p className="text-[10px] text-rose-400/70 italic flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" /> Extreme leverage — liquidation risk is very high
                    </p>
                  )}
                </div>

                {/* RISK PER TRADE */}
                <div className="space-y-4">
                  <div className="flex justify-between items-end">
                    <div className="flex items-center gap-2">
                      <Percent className="w-3.5 h-3.5 text-primary" />
                      <Label className="text-[10px] font-bold uppercase text-muted-foreground/60">Portfolio Risk Per Trade</Label>
                    </div>
                    <span className="text-sm font-mono font-bold text-primary">{(settings.risk_per_trade * 100).toFixed(1)}%</span>
                  </div>
                  <Slider 
                    value={[settings.risk_per_trade * 100]} 
                    min={0.5} max={20} step={0.5} 
                    onValueChange={(val) => setSettings({...settings, risk_per_trade: val[0] / 100})}
                  />
                </div>

                {/* HFT CYCLE SPEED */}
                <div className="space-y-4">
                  <div className="flex justify-between items-end">
                    <div className="flex items-center gap-2">
                      <Timer className="w-3.5 h-3.5 text-primary" />
                      <Label className="text-[10px] font-bold uppercase text-muted-foreground/60">HFT Engine Cycle Speed</Label>
                    </div>
                    <span className="text-sm font-mono font-bold text-primary">{settings.hft_cycle_seconds}s</span>
                  </div>
                  <Slider 
                    value={[settings.hft_cycle_seconds]} 
                    min={1} max={10} step={0.5} 
                    onValueChange={(val) => setSettings({...settings, hft_cycle_seconds: val[0]})}
                  />
                </div>

                {/* TP / SL */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="space-y-3">
                    <Label className="text-[10px] font-bold uppercase text-muted-foreground/60 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-emerald-500" /> Take Profit (%)
                    </Label>
                    <Input 
                      type="number" step="0.1"
                      value={(settings.tp_pct * 100).toFixed(1)} 
                      onChange={(e) => setSettings({...settings, tp_pct: Number(e.target.value) / 100})}
                      className="bg-muted/20 border-border h-10 font-mono text-sm"
                    />
                  </div>
                  <div className="space-y-3">
                    <Label className="text-[10px] font-bold uppercase text-muted-foreground/60 flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-rose-500" /> Stop Loss (%)
                    </Label>
                    <Input 
                      type="number" step="0.1"
                      value={(settings.sl_pct * 100).toFixed(1)} 
                      onChange={(e) => setSettings({...settings, sl_pct: Number(e.target.value) / 100})}
                      className="bg-muted/20 border-border h-10 font-mono text-sm"
                    />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Safety Filters */}
          <Card className="bg-card/40 border-border">
            <CardHeader className="border-b border-border/50 py-4">
              <CardTitle className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                <ShieldCheck className="w-3.5 h-3.5" />
                Safety Filters
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="text-sm font-bold">Watchlist Lockdown</Label>
                  <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider opacity-60">Restrict signals to monitored assets only</p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="text-sm font-bold">Trailing Stop Loss</Label>
                  <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider opacity-60">Auto-lock 60% of peak profits</p>
                </div>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label className="text-sm font-bold">BTC Correlation Filter</Label>
                  <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider opacity-60">Pause momentum buys when BTC crashes &gt;0.08%</p>
                </div>
                <Switch defaultChecked />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* RIGHT SIDEBAR */}
        <div className="space-y-6">
          {/* Risk Allocation Calculator */}
          <Card className="bg-muted/20 border-border">
            <CardHeader className="pb-2">
              <CardTitle className="text-[10px] font-bold uppercase tracking-widest flex items-center gap-2">
                <Calculator className="w-3.5 h-3.5" />
                Risk Calculator
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-background/50 rounded-lg border border-border space-y-3 shadow-inner">
                <RiskRow label="Portfolio Value" value={`$${balance.toLocaleString()}`} />
                <RiskRow label="Risk Per Trade" value={`$${dollarRisk.toLocaleString(undefined, { maximumFractionDigits: 0 })}`} color="destructive" />
                <div className="pt-2 border-t border-border/50">
                  <RiskRow label="Max Exposure" value={`$${maxExposure.toLocaleString(undefined, { maximumFractionDigits: 0 })}`} color="primary" />
                  <RiskRow label="Leverage" value={`${settings.leverage}x`} color={settings.leverage >= 25 ? "destructive" : "primary"} />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Risk Warning */}
          <div className="bg-rose-500/5 border border-rose-500/10 rounded-2xl p-6 flex items-start gap-4">
            <AlertTriangle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h4 className="text-[10px] font-black uppercase tracking-widest text-rose-500">Risk Disclosure</h4>
              <p className="text-[10px] text-rose-500/50 leading-relaxed font-medium">
                Leveraged trading involves significant risk. Simulated parameters should be verified against live market conditions before deploying real capital.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function RiskRow({ label, value, color }: { label: string; value: string; color?: string }) {
  const textColor = color === "destructive" ? "text-destructive" : color === "primary" ? "text-primary" : "";
  return (
    <div className="flex justify-between text-[11px] font-bold">
      <span className="text-muted-foreground/60 uppercase">{label}</span>
      <span className={cn("font-mono", textColor)}>{value}</span>
    </div>
  );
}
