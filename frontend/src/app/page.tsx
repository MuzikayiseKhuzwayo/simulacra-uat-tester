"use client";

import React, { useState } from "react";
import { Header } from "@/components/Header";
import { SimulationStudio } from "@/components/SimulationStudio";
import { ExecutiveReports } from "@/components/ExecutiveReports";
import { SessionsTelemetry } from "@/components/SessionsTelemetry";
import { SurveyInspector } from "@/components/SurveyInspector";
import { TestPackDesigner } from "@/components/TestPackDesigner";
import {
  Activity,
  BarChart3,
  FileCode,
  MessageSquare,
  PlayCircle,
} from "lucide-react";

type TabId = "studio" | "reports" | "sessions" | "surveys" | "designer";

export default function Home() {
  const [activeTab, setActiveTab] = useState<TabId>("studio");
  const [activeCampaignId, setActiveCampaignId] = useState<string | null>(null);

  const tabs: { id: TabId; label: string; icon: React.ElementType }[] = [
    { id: "studio", label: "Simulation Studio", icon: PlayCircle },
    { id: "reports", label: "Executive UAT Reports", icon: BarChart3 },
    { id: "sessions", label: "User Sessions & Telemetry", icon: Activity },
    { id: "surveys", label: "Persona UX Surveys", icon: MessageSquare },
    { id: "designer", label: "TestPack Design Agent", icon: FileCode },
  ];

  return (
    <div className="min-h-screen bg-[#080c14] text-slate-100 flex flex-col font-sans">
      <Header />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">
        {/* Navigation Tabs Bar */}
        <div className="flex overflow-x-auto no-scrollbar space-x-2 p-1.5 rounded-2xl bg-slate-950/70 border border-slate-800/80 backdrop-blur-md">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-2.5 px-4 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                  isActive
                    ? "bg-slate-800 text-white shadow-lg shadow-black/40 border border-slate-700/80"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/50"
                }`}
              >
                <Icon
                  className={`w-4 h-4 ${
                    isActive ? "text-cyan-400" : "text-slate-500"
                  }`}
                />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Content Display */}
        <div className="transition-all duration-200">
          {activeTab === "studio" && (
            <SimulationStudio
              onSimulationComplete={(campaignId) => {
                setActiveCampaignId(campaignId);
                setActiveTab("reports");
              }}
            />
          )}

          {activeTab === "reports" && (
            <ExecutiveReports initialCampaignId={activeCampaignId} />
          )}

          {activeTab === "sessions" && <SessionsTelemetry />}

          {activeTab === "surveys" && <SurveyInspector />}

          {activeTab === "designer" && <TestPackDesigner />}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950/50 py-6 text-center text-xs text-slate-500">
        Simulacra UAT Platform &bull; Autonomous Persona Journey Architecture &bull; Next.js 15 &bull; FastAPI &bull; Playwright
      </footer>
    </div>
  );
}
