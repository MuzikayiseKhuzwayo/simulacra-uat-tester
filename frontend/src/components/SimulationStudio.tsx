"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Globe,
  Play,
  Server,
  Users,
} from "lucide-react";
import {
  PersonaPreset,
  SimulationStepEvent,
  fetchPresetPersonas,
  startDemoApp,
  streamSimulation,
} from "@/lib/api";

interface SimulationStudioProps {
  onSimulationComplete: (campaignId: string) => void;
}

export function SimulationStudio({ onSimulationComplete }: SimulationStudioProps) {
  const [presets, setPresets] = useState<PersonaPreset[]>([]);
  const [selectedIndices, setSelectedIndices] = useState<number[]>([0, 1, 2]);
  const [cohortMode, setCohortMode] = useState<"curated" | "algorithmic">("curated");
  const [cohortSize, setCohortSize] = useState<number>(5);

  const [targetUrl, setTargetUrl] = useState("http://localhost:4200/");
  const [campaignTitle, setCampaignTitle] = useState("Quantix Live Web App UAT Audit");
  const [missionGoal, setMissionGoal] = useState(
    "Explore features, inspect pricing tiers and risk models, test signup onboarding, and reach the main portfolio dashboard."
  );

  const [maxSteps, setMaxSteps] = useState(12);
  const [headless, setHeadless] = useState(true);
  const [captureScreenshots, setCaptureScreenshots] = useState(true);

  // Streaming State
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentStatus, setCurrentStatus] = useState<string>("");
  const [terminalLogs, setTerminalLogs] = useState<SimulationStepEvent[]>([]);
  const [demoServerStatus, setDemoServerStatus] = useState<string | null>(null);

  useEffect(() => {
    fetchPresetPersonas()
      .then((data) => setPresets(data))
      .catch((err) => console.error("Error loading personas:", err));
  }, []);

  const handleLaunch = async () => {
    if (!targetUrl.trim()) {
      alert("Please provide a valid Target URL");
      return;
    }

    setIsRunning(true);
    setProgress(5);
    setCurrentStatus("Initializing Chromium headless browser cluster...");
    setTerminalLogs([]);

    try {
      await streamSimulation(
        {
          target_url: targetUrl,
          campaign_title: campaignTitle,
          primary_goal: missionGoal,
          cohort_mode: cohortMode,
          selected_preset_indices: selectedIndices,
          cohort_size: cohortSize,
          max_steps: maxSteps,
          headless: headless,
          capture_screenshots: captureScreenshots,
        },
        (event: SimulationStepEvent) => {
          if (event.type === "step") {
            const stepProg = Math.min(
              95,
              Math.round(
                ((event.current_persona - 1 + event.step_number / event.max_steps) /
                  event.total_personas) *
                  100
              )
            );
            setProgress(stepProg);
            setCurrentStatus(
              `Simulating ${event.persona_name} (${event.persona_role}) - Step ${event.step_number}/${event.max_steps}: ${event.action_type}`
            );
            setTerminalLogs((prev) => [...prev, event]);
          } else if (event.type === "complete") {
            setProgress(100);
            setCurrentStatus("🎉 Simulation complete! UX audit synthesized.");
            setIsRunning(false);
            if (event.campaign_id) {
              onSimulationComplete(event.campaign_id);
            }
          }
        }
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setCurrentStatus(`⚠️ Simulation stopped: ${msg}`);
      setIsRunning(false);
    }
  };

  const handleStartDemo = async () => {
    try {
      const res = await startDemoApp();
      setDemoServerStatus(`Running at ${res.url}`);
      setTargetUrl("http://127.0.0.1:8585");
      setCampaignTitle("AcmeCloud SaaS Trial & Onboarding");
      setMissionGoal(
        "Explore features, inspect pricing plans, sign up for a free trial, and reach the dashboard to issue an invoice."
      );
    } catch {
      setDemoServerStatus("Failed to start server");
    }
  };

  return (
    <div className="space-y-8">
      {/* 2-Column Cockpit Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Target Environment & Objective */}
        <div className="lg:col-span-6 space-y-6">
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
              <div className="flex items-center space-x-2.5">
                <Globe className="w-5 h-5 text-cyan-400" />
                <h2 className="text-base font-semibold text-white">Target Web Environment</h2>
              </div>
              <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
                Step 1 of 3
              </span>
            </div>

            {/* Environment Presets */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Quick Environment Presets
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                <button
                  type="button"
                  onClick={() => {
                    setTargetUrl("http://localhost:4200/");
                    setCampaignTitle("Quantix Live Web App UAT Audit");
                    setMissionGoal(
                      "Explore features, inspect pricing tiers and risk models, test signup onboarding, and reach the main portfolio dashboard."
                    );
                  }}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    targetUrl.includes("4200")
                      ? "border-cyan-500/50 bg-cyan-950/30 text-cyan-200 shadow-md shadow-cyan-950/40"
                      : "border-slate-800 bg-slate-950/50 hover:border-slate-700 text-slate-300"
                  }`}
                >
                  <div className="text-xs font-bold">⚡ Quantix App</div>
                  <div className="text-[11px] text-slate-400 mt-0.5 font-mono">localhost:4200</div>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setTargetUrl("http://127.0.0.1:8585");
                    setCampaignTitle("AcmeCloud SaaS Trial & Onboarding");
                    setMissionGoal(
                      "Explore features, inspect pricing plans, sign up for a free trial, and reach the dashboard to issue an invoice."
                    );
                  }}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    targetUrl.includes("8585")
                      ? "border-indigo-500/50 bg-indigo-950/30 text-indigo-200 shadow-md shadow-indigo-950/40"
                      : "border-slate-800 bg-slate-950/50 hover:border-slate-700 text-slate-300"
                  }`}
                >
                  <div className="text-xs font-bold">🏢 AcmeCloud SaaS</div>
                  <div className="text-[11px] text-slate-400 mt-0.5 font-mono">127.0.0.1:8585</div>
                </button>

                <button
                  type="button"
                  onClick={handleStartDemo}
                  className="p-3 rounded-xl border border-dashed border-emerald-500/40 bg-emerald-950/20 hover:bg-emerald-950/40 text-emerald-300 transition-all text-left flex flex-col justify-between"
                >
                  <div className="text-xs font-bold flex items-center justify-between">
                    <span>Demo Server</span>
                    <Server className="w-3.5 h-3.5" />
                  </div>
                  <div className="text-[10px] text-emerald-400/80 mt-1">
                    {demoServerStatus ? "● Ready" : "Start Built-in"}
                  </div>
                </button>
              </div>
            </div>

            {/* Target Inputs */}
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Target Application URL
                </label>
                <input
                  type="text"
                  value={targetUrl}
                  onChange={(e) => setTargetUrl(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
                  placeholder="https://example.com or http://localhost:4200/"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Campaign Title
                </label>
                <input
                  type="text"
                  value={campaignTitle}
                  onChange={(e) => setCampaignTitle(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                  placeholder="Campaign Title"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Primary User Goal / Mission Objective
                </label>
                <textarea
                  value={missionGoal}
                  onChange={(e) => setMissionGoal(e.target.value)}
                  rows={3}
                  className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 resize-none leading-relaxed"
                  placeholder="What should the synthetic users attempt to accomplish?"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Synthetic Persona Cohort & Engine Parameters */}
        <div className="lg:col-span-6 space-y-6">
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
              <div className="flex items-center space-x-2.5">
                <Users className="w-5 h-5 text-indigo-400" />
                <h2 className="text-base font-semibold text-white">Synthetic Persona Cohort</h2>
              </div>
              <span className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
                Step 2 of 3
              </span>
            </div>

            {/* Mode Toggle */}
            <div className="flex rounded-xl bg-slate-950 p-1 border border-slate-800">
              <button
                type="button"
                onClick={() => setCohortMode("curated")}
                className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all ${
                  cohortMode === "curated"
                    ? "bg-slate-800 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Curated Archetypes ({selectedIndices.length} Selected)
              </button>
              <button
                type="button"
                onClick={() => setCohortMode("algorithmic")}
                className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold transition-all ${
                  cohortMode === "algorithmic"
                    ? "bg-slate-800 text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                Algorithmic Cohort Generator
              </button>
            </div>

            {/* Persona Selection */}
            {cohortMode === "curated" ? (
              <div className="space-y-2.5 max-h-[220px] overflow-y-auto pr-1">
                {presets.map((p, idx) => {
                  const isSelected = selectedIndices.includes(idx);
                  return (
                    <div
                      key={p.persona_id}
                      onClick={() => {
                        if (isSelected) {
                          setSelectedIndices(selectedIndices.filter((i) => i !== idx));
                        } else {
                          setSelectedIndices([...selectedIndices, idx]);
                        }
                      }}
                      className={`p-3 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${
                        isSelected
                          ? "border-indigo-500/50 bg-indigo-950/20 text-white"
                          : "border-slate-800/80 bg-slate-950/40 text-slate-400 hover:border-slate-700"
                      }`}
                    >
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-bold text-slate-100">{p.name}</span>
                          <span className="text-[10px] text-cyan-400 font-medium">({p.role})</span>
                        </div>
                        <div className="flex items-center space-x-1.5 text-[10px] text-slate-400">
                          <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                            Tech: {p.technical_skill}
                          </span>
                          <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                            Patience: {p.patience}
                          </span>
                          <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                            Device: {p.device_type}
                          </span>
                        </div>
                      </div>
                      <div
                        className={`w-5 h-5 rounded-md border flex items-center justify-center transition-all ${
                          isSelected
                            ? "bg-indigo-600 border-indigo-500 text-white"
                            : "border-slate-700 bg-slate-900"
                        }`}
                      >
                        {isSelected && <CheckCircle2 className="w-3.5 h-3.5" />}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-300 font-medium">Cohort Volume:</span>
                  <span className="text-cyan-400 font-bold">{cohortSize} Personas</span>
                </div>
                <input
                  type="range"
                  min={1}
                  max={20}
                  value={cohortSize}
                  onChange={(e) => setCohortSize(parseInt(e.target.value))}
                  className="w-full accent-cyan-500"
                />
                <p className="text-[11px] text-slate-400">
                  Generates statistically diverse demographic profiles, technical proficiencies, and
                  psychological biases.
                </p>
              </div>
            )}

            {/* Execution Parameters */}
            <div className="grid grid-cols-3 gap-3 pt-2 border-t border-slate-800">
              <div className="space-y-1">
                <label className="text-[11px] font-semibold text-slate-400 uppercase">
                  Max Steps / User
                </label>
                <input
                  type="number"
                  min={3}
                  max={40}
                  value={maxSteps}
                  onChange={(e) => setMaxSteps(parseInt(e.target.value) || 10)}
                  className="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-white"
                />
              </div>

              <div className="flex flex-col justify-center space-y-1">
                <label className="text-[11px] font-semibold text-slate-400 uppercase">Headless</label>
                <label className="inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={headless}
                    onChange={(e) => setHeadless(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-600 relative"></div>
                </label>
              </div>

              <div className="flex flex-col justify-center space-y-1">
                <label className="text-[11px] font-semibold text-slate-400 uppercase">Screenshots</label>
                <label className="inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={captureScreenshots}
                    onChange={(e) => setCaptureScreenshots(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-9 h-5 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-indigo-600 relative"></div>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Launch Trigger Button */}
      <div className="relative">
        <button
          type="button"
          disabled={isRunning}
          onClick={handleLaunch}
          className={`w-full py-4 px-6 rounded-2xl font-bold text-base tracking-wide flex items-center justify-center space-x-3 transition-all shadow-xl ${
            isRunning
              ? "bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700"
              : "bg-gradient-to-r from-indigo-600 via-indigo-500 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white shadow-indigo-900/30 hover:shadow-cyan-900/40 hover:scale-[1.005] active:scale-[0.995]"
          }`}
        >
          {isRunning ? (
            <>
              <Activity className="w-5 h-5 animate-spin text-cyan-400" />
              <span>Simulating Autonomous Synthetic Users... ({progress}%)</span>
            </>
          ) : (
            <>
              <Play className="w-5 h-5 fill-current" />
              <span>Launch Autonomous Synthetic UAT Simulation</span>
              <ArrowRight className="w-5 h-5" />
            </>
          )}
        </button>
      </div>

      {/* Real-time Streaming Activity Console */}
      {(isRunning || terminalLogs.length > 0) && (
        <div className="bg-slate-950 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-4">
          <div className="flex items-center justify-between border-b border-slate-900 pb-3">
            <div className="flex items-center space-x-2.5">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse" />
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                Live Synthetic Cognitive Stream
              </h3>
            </div>
            <span className="text-xs font-mono text-cyan-400 font-semibold">{progress}%</span>
          </div>

          {/* Progress Bar */}
          <div className="w-full h-1.5 rounded-full bg-slate-900 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>

          <div className="text-xs font-mono text-slate-300">{currentStatus}</div>

          {/* Terminal Log Stream */}
          <div className="bg-slate-950/90 rounded-xl p-4 border border-slate-800/80 font-mono text-xs max-h-72 overflow-y-auto space-y-3">
            {terminalLogs.slice(-10).map((log, i) => (
              <div key={i} className="space-y-1 border-b border-slate-900/80 pb-2.5 last:border-0">
                <div className="flex items-center justify-between text-slate-400">
                  <div className="flex items-center space-x-2">
                    <span className="text-cyan-400 font-bold">[{log.persona_name}]</span>
                    <span className="px-1.5 py-0.5 rounded bg-slate-900 text-[10px] text-slate-300 font-semibold">
                      {log.action_type}
                    </span>
                    <span className="text-slate-500">on</span>
                    <span className="text-slate-300 truncate max-w-xs">{log.page_title || log.page_url}</span>
                  </div>
                  <span className="text-[11px] text-slate-500">
                    Emotion: <span className="text-amber-400">{log.emotion}</span> &bull; Conf:{" "}
                    {log.confidence.toFixed(2)}
                  </span>
                </div>
                <p className="text-slate-300 italic text-[11px] pl-3 border-l-2 border-indigo-500/50">
                  &ldquo;{log.cognitive_reasoning}&rdquo;
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
