"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  Zap,
} from "lucide-react";
import {
  CampaignSummary,
  QuantixFeedback,
  StandardFeedback,
  autofillGoogleForm,
  fetchCampaigns,
  fetchFeedbacks,
} from "@/lib/api";

export function SurveyInspector() {
  const [campaigns, setCampaigns] = useState<CampaignSummary[]>([]);
  const [selectedCampId, setSelectedCampId] = useState<string>("");
  const [format, setFormat] = useState<"google" | "standard">("google");
  const [quantixFeedbacks, setQuantixFeedbacks] = useState<QuantixFeedback[]>([]);
  const [standardFeedbacks, setStandardFeedbacks] = useState<StandardFeedback[]>([]);
  const [fillingSessionId, setFillingSessionId] = useState<string | null>(null);
  const [fillResult, setFillResult] = useState<{ [key: string]: string }>({});

  useEffect(() => {
    fetchCampaigns().then((data) => {
      setCampaigns(data);
      if (data.length > 0) setSelectedCampId(data[0].campaign_id);
    });
  }, []);

  useEffect(() => {
    if (!selectedCampId) return;
    fetchFeedbacks(selectedCampId).then((data) => {
      setQuantixFeedbacks(data.quantix_feedbacks || []);
      setStandardFeedbacks(data.standard_feedbacks || []);
    });
  }, [selectedCampId]);

  const handleAutofill = async (sessionId: string) => {
    setFillingSessionId(sessionId);
    try {
      const res = await autofillGoogleForm(selectedCampId, sessionId);
      setFillResult((prev) => ({
        ...prev,
        [sessionId]: res.success ? `✅ Form Filled: ${res.message}` : `⚠️ ${res.message}`,
      }));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setFillResult((prev) => ({
        ...prev,
        [sessionId]: `Error: ${msg}`,
      }));
    } finally {
      setFillingSessionId(null);
    }
  };

  return (
    <div className="space-y-8">
      {/* Controls Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 bg-slate-900/80 border border-slate-800 rounded-2xl">
        <div>
          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
            Select Campaign
          </label>
          <select
            value={selectedCampId}
            onChange={(e) => setSelectedCampId(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-white font-medium focus:outline-none focus:border-cyan-500 min-w-[280px]"
          >
            {campaigns.map((c) => (
              <option key={c.campaign_id} value={c.campaign_id}>
                {c.title} ({c.created_at.slice(0, 19)})
              </option>
            ))}
          </select>
        </div>

        {/* Survey Format Toggle */}
        <div className="flex rounded-xl bg-slate-950 p-1 border border-slate-800">
          <button
            type="button"
            onClick={() => setFormat("google")}
            className={`py-1.5 px-3.5 rounded-lg text-xs font-semibold transition-all ${
              format === "google"
                ? "bg-teal-900/60 text-teal-200 border border-teal-700/60 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            📋 Google Form (Quantix Feedback)
          </button>
          <button
            type="button"
            onClick={() => setFormat("standard")}
            className={`py-1.5 px-3.5 rounded-lg text-xs font-semibold transition-all ${
              format === "standard"
                ? "bg-slate-800 text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            📊 Standard UX Scorecard (SUS / NPS)
          </button>
        </div>
      </div>

      {format === "google" ? (
        <div className="space-y-8">
          {quantixFeedbacks.length === 0 ? (
            <div className="p-8 text-center bg-slate-900/50 border border-slate-800 rounded-2xl">
              <p className="text-sm text-slate-400">
                No Google Form responses synthesized for this campaign yet. Launch a simulation to
                synthesize complete 8-section customer responses.
              </p>
            </div>
          ) : (
            quantixFeedbacks.map((qfb) => (
              <div
                key={qfb.form_id}
                className="bg-slate-900/90 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl space-y-6 p-6 sm:p-8"
              >
                {/* Google Forms Teal Header Banner */}
                <div className="rounded-xl bg-gradient-to-r from-[#02746b] to-[#039f93] p-6 text-white shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <h3 className="text-lg font-bold">Customer Feedback - Quantix</h3>
                    <p className="text-xs text-teal-100 mt-1">
                      Synthetic Persona Response &bull; <b>{qfb.persona_name}</b> ({qfb.primary_role})
                      &bull; Submitted: <code className="text-teal-200">{qfb.submitted_at.slice(0, 19)}</code>
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="px-3 py-1 rounded-full bg-teal-950/40 border border-teal-300/30 text-xs font-bold text-teal-100">
                      NPS: {qfb.nps_recommendation}/10
                    </span>
                    <span className="px-3 py-1 rounded-full bg-teal-950/40 border border-teal-300/30 text-xs font-bold text-teal-100">
                      Emotion: {qfb.emotional_sentiment}
                    </span>
                  </div>
                </div>

                {/* Section 1: Landing Page Evaluation */}
                <div className="space-y-3">
                  <h4 className="text-sm font-bold text-teal-400 uppercase tracking-wider">
                    1. Landing Page Evaluation
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-[11px] text-slate-400 font-semibold">Clarity (10-15s)</span>
                      <div className="text-xl font-bold text-white mt-1">{qfb.clarity_10_15s} / 5</div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-[11px] text-slate-400 font-semibold">Visual Design</span>
                      <div className="text-xl font-bold text-white mt-1">{qfb.visual_design} / 5</div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-[11px] text-slate-400 font-semibold">Credibility</span>
                      <div className="text-xl font-bold text-white mt-1">{qfb.credibility} / 5</div>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-2">
                    <div>
                      <span className="text-slate-400 font-semibold">Element that convinced you:</span>
                      <p className="text-slate-200 mt-0.5">&ldquo;{qfb.convincing_element}&rdquo;</p>
                    </div>
                    {qfb.hesitation_trigger && (
                      <div>
                        <span className="text-amber-400 font-semibold">Element that caused hesitation:</span>
                        <p className="text-slate-300 mt-0.5">&ldquo;{qfb.hesitation_trigger}&rdquo;</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Section 4: Core Product */}
                <div className="space-y-3 pt-3 border-t border-slate-800">
                  <h4 className="text-sm font-bold text-teal-400 uppercase tracking-wider">
                    4. Core Product &amp; Aha Moment
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-[11px] text-slate-400 font-semibold">Intuitiveness</span>
                      <div className="text-xl font-bold text-white mt-1">
                        {qfb.navigating_intuitiveness} / 5
                      </div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-[11px] text-slate-400 font-semibold">Speed</span>
                      <div className="text-xl font-bold text-white mt-1">
                        {qfb.speed_responsiveness} / 5
                      </div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-[11px] text-slate-400 font-semibold">Reliability</span>
                      <div className="text-xl font-bold text-white mt-1">{qfb.reliability} / 5</div>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                    <span className="text-emerald-400 font-semibold">✨ The &ldquo;Aha!&rdquo; Moment:</span>
                    <p className="text-slate-200 mt-1 italic">&ldquo;{qfb.aha_moment}&rdquo;</p>
                  </div>
                </div>

                {/* Section 6 & 7: Friction & PMF */}
                <div className="space-y-3 pt-3 border-t border-slate-800">
                  <h4 className="text-sm font-bold text-teal-400 uppercase tracking-wider">
                    6 &amp; 7. Friction, Missing Pieces &amp; PMF Assessment
                  </h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <span className="text-rose-400 font-semibold">🛑 Most Frustrating Moment:</span>
                      <p className="text-slate-300">&ldquo;{qfb.most_frustrating_moment}&rdquo;</p>
                    </div>

                    <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                      <span className="text-indigo-400 font-semibold">🪄 Magic Wand Change:</span>
                      <p className="text-slate-300">&ldquo;{qfb.magic_wand_change}&rdquo;</p>
                    </div>
                  </div>
                </div>

                {/* Live Playwright Autofill Action */}
                <div className="pt-4 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="text-xs text-slate-400">
                    {fillResult[qfb.session_id] ? (
                      <span className="text-emerald-400 font-medium">
                        {fillResult[qfb.session_id]}
                      </span>
                    ) : (
                      "Automate populating the official Quantix Google Form with this persona's survey data."
                    )}
                  </div>
                  <button
                    type="button"
                    disabled={fillingSessionId === qfb.session_id}
                    onClick={() => handleAutofill(qfb.session_id)}
                    className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-500 text-white text-xs font-bold transition-all flex items-center space-x-2 shadow-lg shadow-teal-900/30"
                  >
                    {fillingSessionId === qfb.session_id ? (
                      <>
                        <Activity className="w-3.5 h-3.5 animate-spin" />
                        <span>Filling Form with Playwright...</span>
                      </>
                    ) : (
                      <>
                        <Zap className="w-3.5 h-3.5 fill-current" />
                        <span>Auto-Fill Official Google Form</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      ) : (
        /* Standard Scorecard */
        <div className="space-y-6">
          {standardFeedbacks.map((fb) => (
            <div
              key={fb.feedback_id}
              className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-base font-bold text-white">{fb.persona_name}</h4>
                  <div className="text-xs text-slate-400 mt-0.5">{fb.sentiment_summary}</div>
                </div>
                <div className="flex items-center space-x-2 text-xs font-semibold">
                  <span className="px-2.5 py-1 rounded-full bg-indigo-950/60 border border-indigo-700/60 text-indigo-300">
                    SUS: {fb.sus_score.toFixed(1)}/100
                  </span>
                  <span className="px-2.5 py-1 rounded-full bg-cyan-950/60 border border-cyan-700/60 text-cyan-300">
                    CES: {fb.ces_score}/7
                  </span>
                  <span className="px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-700/60 text-emerald-300">
                    NPS: {fb.nps_rating}/10
                  </span>
                </div>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs italic text-slate-200">
                &ldquo;{fb.verbatim_quote}&rdquo;
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
