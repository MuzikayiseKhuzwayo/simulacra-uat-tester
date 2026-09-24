"use client";

import React, { useEffect, useState } from "react";
import {
  Brain,
  Camera,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import {
  API_BASE,
  CampaignSummary,
  SessionRecord,
  TelemetryEvent,
  fetchCampaigns,
  fetchSessionTelemetry,
  fetchSessions,
} from "@/lib/api";

export function SessionsTelemetry() {
  const [campaigns, setCampaigns] = useState<CampaignSummary[]>([]);
  const [selectedCampId, setSelectedCampId] = useState<string>("");
  const [sessions, setSessions] = useState<SessionRecord[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string>("");
  const [telemetry, setTelemetry] = useState<TelemetryEvent[]>([]);

  useEffect(() => {
    fetchCampaigns().then((data) => {
      setCampaigns(data);
      if (data.length > 0) setSelectedCampId(data[0].campaign_id);
    });
  }, []);

  useEffect(() => {
    if (!selectedCampId) return;
    fetchSessions(selectedCampId).then((data) => {
      setSessions(data);
      if (data.length > 0) setSelectedSessionId(data[0].session_id);
    });
  }, [selectedCampId]);

  useEffect(() => {
    if (!selectedSessionId) return;
    fetchSessionTelemetry(selectedSessionId).then((data) => {
      setTelemetry(data);
    });
  }, [selectedSessionId]);

  const currentSession = sessions.find((s) => s.session_id === selectedSessionId);

  return (
    <div className="space-y-8">
      {/* Session Selection Toolbar */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-5 bg-slate-900/80 border border-slate-800 rounded-2xl">
        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
            Campaign Audit
          </label>
          <select
            value={selectedCampId}
            onChange={(e) => setSelectedCampId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-white font-medium focus:outline-none focus:border-cyan-500"
          >
            {campaigns.map((c) => (
              <option key={c.campaign_id} value={c.campaign_id}>
                {c.title} ({c.created_at.slice(0, 19)})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
            Persona Session Journey
          </label>
          <select
            value={selectedSessionId}
            onChange={(e) => setSelectedSessionId(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-white font-medium focus:outline-none focus:border-indigo-500"
          >
            {sessions.map((s) => (
              <option key={s.session_id} value={s.session_id}>
                {s.persona_name} — {s.task_success ? "✅ Passed" : "❌ Abandoned"} ({s.duration_seconds}s,{" "}
                {s.total_steps} steps)
              </option>
            ))}
          </select>
        </div>
      </div>

      {currentSession && (
        <>
          {/* Session Overview Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Outcome</span>
              <div className="text-lg font-bold mt-1 flex items-center gap-1.5">
                {currentSession.task_success ? (
                  <span className="text-emerald-400 flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4" /> Goal Accomplished
                  </span>
                ) : (
                  <span className="text-rose-400 flex items-center gap-1">
                    <XCircle className="w-4 h-4" /> Journey Abandoned
                  </span>
                )}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Friction Score</span>
              <div className="text-lg font-bold text-white mt-1">
                {currentSession.friction_score.toFixed(1)} <span className="text-xs text-slate-500">/ 100</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Total Steps</span>
              <div className="text-lg font-bold text-white mt-1">{currentSession.total_steps}</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <span className="text-[11px] font-semibold text-slate-400 uppercase">Exit Reason</span>
              <div className="text-xs font-semibold text-cyan-400 mt-1 truncate">
                {currentSession.exit_reason}
              </div>
            </div>
          </div>

          {/* Chronological Forensics Journey Stream */}
          <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6">
            <div className="flex items-center space-x-2.5 pb-4 border-b border-slate-800">
              <Brain className="w-5 h-5 text-indigo-400" />
              <h3 className="text-base font-bold text-white">
                Chronological Cognitive Telemetry Timeline
              </h3>
            </div>

            <div className="space-y-4">
              {telemetry.map((evt) => {
                const isNegative = ["Frustrated", "Annoyed", "Confused"].includes(evt.emotion);
                const isPositive = ["Delighted", "Satisfied", "Curious"].includes(evt.emotion);
                const emotionBadgeColor = isNegative
                  ? "text-rose-400 bg-rose-950/40 border-rose-800/60"
                  : isPositive
                  ? "text-emerald-400 bg-emerald-950/40 border-emerald-800/60"
                  : "text-cyan-400 bg-cyan-950/40 border-cyan-800/60";

                return (
                  <div
                    key={evt.event_id}
                    className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 hover:border-slate-700 transition-all space-y-3"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-0.5 rounded-md bg-slate-800 font-mono text-[11px] font-bold text-cyan-300">
                          STEP {String(evt.step_number).padStart(2, "0")}
                        </span>
                        <span className="text-xs font-extrabold uppercase tracking-wide text-white">
                          {evt.action_type}
                        </span>
                        <span className="text-xs text-slate-500 font-mono truncate max-w-sm">
                          {evt.target_element || evt.page_url}
                        </span>
                      </div>

                      <div className="flex items-center space-x-2 text-[11px]">
                        <span className={`px-2 py-0.5 rounded-full border text-[10px] font-semibold ${emotionBadgeColor}`}>
                          {evt.emotion}
                        </span>
                        <span className="text-slate-400">
                          Conf: <b className="text-white">{evt.confidence.toFixed(2)}</b>
                        </span>
                        <span className="text-slate-400">
                          Hesitation: <b className="text-white">{evt.hesitation_ms}ms</b>
                        </span>
                      </div>
                    </div>

                    {/* Inner Monologue */}
                    <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 text-xs italic text-slate-300 leading-relaxed">
                      💭 <span className="font-semibold text-slate-200">Inner Monologue:</span> &ldquo;
                      {evt.cognitive_reasoning}&rdquo;
                    </div>

                    {/* Snapshot Preview if available */}
                    {evt.screenshot_path && (
                      <div className="pt-2">
                        <div className="text-[11px] font-semibold text-slate-400 flex items-center gap-1.5 mb-1.5">
                          <Camera className="w-3.5 h-3.5 text-cyan-400" />
                          <span>DOM Snapshot: {evt.page_title}</span>
                        </div>
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={`${API_BASE}/screenshots/${evt.screenshot_path.split(/[\\/]/).pop()}`}
                          alt={`Step ${evt.step_number}`}
                          className="rounded-lg border border-slate-800 max-h-72 object-cover object-top hover:opacity-95 transition-opacity"
                        />
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
