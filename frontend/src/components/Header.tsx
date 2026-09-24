"use client";

import React, { useEffect, useState } from "react";
import { Bot, Cpu, Sparkles } from "lucide-react";
import { HealthStatus, checkHealth } from "@/lib/api";

export function Header() {
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    checkHealth()
      .then((data) => setHealth(data))
      .catch(() =>
        setHealth({
          status: "offline",
          engine: "FastAPI",
          version: "2.5.0",
          browser_automation: "Playwright",
        })
      );
  }, []);

  return (
    <header className="border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 py-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Brand Title */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-0.5 shadow-lg shadow-indigo-500/20 flex items-center justify-center">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <Bot className="w-5 h-5 text-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                Simulacra UAT
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-semibold tracking-wider uppercase rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                v2.5 Next Engine
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Autonomous Synthetic Persona Testing &bull; Fine-Grained Cognitive Telemetry &bull; UX Audits
            </p>
          </div>
        </div>

        {/* System Telemetry Badges */}
        <div className="flex items-center space-x-4 text-xs font-medium text-slate-400">
          <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800">
            <span
              className={`w-2 h-2 rounded-full ${
                health?.status === "online" ? "bg-emerald-400 shadow-[0_0_8px_#34d399]" : "bg-rose-500"
              }`}
            />
            <span>Engine:</span>
            <span className="text-slate-200 font-semibold">
              {health?.status === "online" ? "FastAPI + Chromium" : "Connecting..."}
            </span>
          </div>

          <div className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800">
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span>Telemetry:</span>
            <span className="text-slate-200 font-semibold">60Hz DOM Tracking</span>
          </div>

          <div className="hidden sm:flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>LLM Synthesis:</span>
            <span className="text-slate-200 font-semibold">Ready</span>
          </div>
        </div>
      </div>
    </header>
  );
}
