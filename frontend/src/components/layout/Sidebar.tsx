"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { 
  Activity, 
  List, 
  ShieldAlert,
  Terminal,
} from "lucide-react";

const navItems = [
  { name: "Dashboard", href: "/dashboard", icon: Activity },
  { name: "Watchlist", href: "/watchlist", icon: List },
  { name: "Risk Control", href: "/settings", icon: ShieldAlert },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-border bg-card/20 flex flex-col h-screen sticky top-0">
      <div className="p-8 flex items-center gap-3">
        <div className="w-9 h-9 bg-primary flex items-center justify-center rounded">
          <Terminal className="w-5 h-5 text-primary-foreground" />
        </div>
        <div className="flex flex-col">
          <span className="font-bold tracking-tight text-base leading-none uppercase">AlphaTrigger</span>
          <span className="text-[10px] font-medium text-muted-foreground tracking-widest uppercase opacity-60">Terminal</span>
        </div>
      </div>
      
      <nav className="flex-1 px-4 py-4 space-y-0.5">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-4 py-2.5 rounded-md text-[13px] font-bold transition-all group",
                isActive 
                  ? "bg-primary/10 text-primary" 
                  : "text-muted-foreground/70 hover:bg-muted/50 hover:text-foreground"
              )}
            >
              <item.icon className={cn("w-4 h-4", isActive ? "text-primary" : "text-muted-foreground/50 group-hover:text-foreground/70")} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="p-6 border-t border-white/5">
        <div className="bg-muted/50 rounded-lg p-3">
          <p className="text-[10px] uppercase font-bold text-muted-foreground mb-1">Status</p>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-medium">Market Live</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
