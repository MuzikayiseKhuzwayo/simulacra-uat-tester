"use client";

import React, { useEffect, useState } from "react";
import {
  FileCode,
  FileSpreadsheet,
  FileText,
  Flame,
  Sparkles,
} from "lucide-react";
import {
  API_BASE,
  CampaignSummary,
  fetchCampaign,
  fetchCampaigns,
} from "@/lib/api";

interface ExecutiveReportsProps {
  initialCampaignId?: string | null;
}

interface CampaignDetailPayload {
  campaign: CampaignSummary;
  report?: Record<string, unknown> | null;
  report_markdown?: string | null;
}

export function ExecutiveReports({ initialCampaignId }: ExecutiveReportsProps) {
  const [campaigns, setCampaigns] = useState<CampaignSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [campaignDetails, setCampaignDetails] = useState<CampaignDetailPayload | null>(null);

  useEffect(() => {
    fetchCampaigns().then((data) => {
      setCampaigns(data);
      if (data.length > 0) {
        const idToSelect =
          initialCampaignId && data.some((c) => c.campaign_id === initialCampaignId)
            ? initialCampaignId
            : data[0].campaign_id;
        setSelectedId(idToSelect);
      }
    });
  }, [initialCampaignId]);

  useEffect(() => {
    if (!selectedId) return;
    fetchCampaign(selectedId)
      .then((data: CampaignDetailPayload) => {
        setCampaignDetails(data);
      })
      .catch((err) => {
        console.error(err);
      });
  }, [selectedId]);

  if (campaigns.length === 0) {
    return (
      <div className="p-12 text-center bg-slate-900/50 border border-slate-800 rounded-2xl">
        <Sparkles className="w-10 h-10 text-slate-600 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-slate-300">No Simulation Audits Found</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
          Launch a simulation from the Simulation Studio to generate comprehensive executive UAT
          audits and KPI benchmarks.
        </p>
      </div>
    );
  }

  const camp = campaignDetails?.campaign;
  const sus = camp?.average_sus_score || 0;
  let susGrade = "F (Severe Friction)";
  let susColor = "text-rose-400 border-rose-500/30 bg-rose-950/20";
  if (sus >= 80.3) {
    susGrade = "Grade A (Excellent)";
    susColor = "text-emerald-400 border-emerald-500/30 bg-emerald-950/20";
  } else if (sus >= 68.0) {
    susGrade = "Grade B (Good)";
    susColor = "text-cyan-400 border-cyan-500/30 bg-cyan-950/20";
  } else if (sus >= 51.0) {
    susGrade = "Grade C (Marginal)";
    susColor = "text-amber-400 border-amber-500/30 bg-amber-950/20";
  }

  return (
    <div className="space-y-8">
      {/* Campaign Selector Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 bg-slate-900/80 border border-slate-800 rounded-2xl">
        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
            Selected Campaign Audit
          </label>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-white font-medium focus:outline-none focus:border-cyan-500 min-w-[320px]"
          >
            {campaigns.map((c) => (
              <option key={c.campaign_id} value={c.campaign_id}>
                {c.title} ({c.created_at.slice(0, 19)})
              </option>
            ))}
          </select>
        </div>

        {/* Action Export Buttons */}
        <div className="flex items-center space-x-2.5">
          <a
            href={`${API_BASE}/api/campaigns/${selectedId}/export/markdown`}
            download
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 flex items-center space-x-1.5 transition-all shadow-sm"
          >
            <FileText className="w-3.5 h-3.5 text-cyan-400" />
            <span>Markdown</span>
          </a>
          <a
            href={`${API_BASE}/api/campaigns/${selectedId}/export/excel`}
            download
            className="px-3.5 py-2 rounded-xl bg-emerald-950/40 hover:bg-emerald-900/50 text-xs font-semibold text-emerald-300 border border-emerald-800/60 flex items-center space-x-1.5 transition-all shadow-sm"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
            <span>Excel Audit</span>
          </a>
          <a
            href={`${API_BASE}/api/campaigns/${selectedId}/export/json`}
            download
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 flex items-center space-x-1.5 transition-all shadow-sm"
          >
            <FileCode className="w-3.5 h-3.5 text-indigo-400" />
            <span>JSON Data</span>
          </a>
        </div>
      </div>

      {/* 5 KPI Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {/* SUS Score */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 relative overflow-hidden">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Usability (SUS)
          </div>
          <div className="text-2xl font-black text-white">
            {sus.toFixed(1)} <span className="text-xs font-normal text-slate-500">/ 100</span>
          </div>
          <div className={`mt-2 text-[11px] font-semibold px-2 py-0.5 rounded-full inline-block border ${susColor}`}>
            {susGrade}
          </div>
        </div>

        {/* Task Success Rate */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Success Rate
          </div>
          <div className="text-2xl font-black text-white">
            {(camp?.success_rate_percent || 0).toFixed(1)}%
          </div>
          <div className="text-xs text-slate-500 mt-2">
            {camp?.successful_sessions || 0} / {camp?.total_sessions || 0} Journeys Completed
          </div>
        </div>

        {/* Friction Index */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Friction Index
          </div>
          <div className="text-2xl font-black text-white">
            {(camp?.average_friction_score || 0).toFixed(1)}
          </div>
          <div className="text-xs text-rose-400 mt-2 flex items-center gap-1 font-medium">
            <Flame className="w-3.5 h-3.5" />
            Cognitive Bottlenecks
          </div>
        </div>

        {/* Rage Clicks */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Rage Clicks
          </div>
          <div className="text-2xl font-black text-rose-400">
            {camp?.total_rage_clicks || 0}
          </div>
          <div className="text-xs text-slate-500 mt-2">Dead clicks & misclicks</div>
        </div>

        {/* Personas Tested */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Cohorts Tested
          </div>
          <div className="text-2xl font-black text-white">{camp?.total_sessions || 0}</div>
          <div className="text-xs text-slate-500 mt-2">Diverse Archetypes</div>
        </div>
      </div>

      {/* Rendered Executive Markdown Document */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl">
        <h3 className="text-base font-bold text-white mb-6 flex items-center space-x-2">
          <FileText className="w-5 h-5 text-cyan-400" />
          <span>Executive Synthesis &amp; Strategic Roadmap</span>
        </h3>

        {campaignDetails?.report_markdown ? (
          <div className="prose prose-invert max-w-none text-slate-300 text-sm leading-relaxed space-y-4 whitespace-pre-line font-sans">
            {campaignDetails.report_markdown}
          </div>
        ) : (
          <p className="text-xs text-slate-500 italic">No report document synthesized yet.</p>
        )}
      </div>
    </div>
  );
}
