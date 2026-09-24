"use client";

import React, { useState } from "react";
import { Activity, CheckCircle2, FileCode, Sparkles } from "lucide-react";
import { generateTestPack } from "@/lib/api";

export function TestPackDesigner() {
  const [reqId, setReqId] = useState("REQ-001");
  const [title, setTitle] = useState("Self-service Instant Invoicing");
  const [userStory, setUserStory] = useState(
    "As a small business owner, I want to create an invoice in 15 seconds so that I can bill clients immediately."
  );
  const [acText, setAcText] = useState(
    "AC-001 | Customer can specify client name and amount.\nAC-002 | Invoice is assigned a unique identifier upon creation.\nAC-003 | Status displays as Issued immediately."
  );

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const acLines = acText.split("\n").filter((l) => l.trim().length > 0);
      const data = await generateTestPack({
        requirement_id: reqId,
        title,
        user_story: userStory,
        acceptance_criteria: acLines,
      });
      setResult(data as Record<string, unknown>);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg || "Failed to generate TestPack");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="p-6 bg-slate-900/80 border border-slate-800 rounded-2xl space-y-5">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <FileCode className="w-5 h-5 text-indigo-400" />
            <span>Deterministic Requirement Analysis &amp; Test Case Design</span>
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Synthesize traceable UAT test packs with risk vectors, test boundaries, and execution
            scenarios from formal user stories.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Requirement ID</label>
            <input
              type="text"
              value={reqId}
              onChange={(e) => setReqId(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">Requirement Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">User Story</label>
          <textarea
            value={userStory}
            onChange={(e) => setUserStory(e.target.value)}
            rows={2}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white resize-none"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Acceptance Criteria (one per line: ID | Description)
          </label>
          <textarea
            value={acText}
            onChange={(e) => setAcText(e.target.value)}
            rows={4}
            className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white font-mono resize-none"
          />
        </div>

        <button
          type="button"
          disabled={loading}
          onClick={handleGenerate}
          className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all flex items-center space-x-2"
        >
          {loading ? (
            <>
              <Activity className="w-4 h-4 animate-spin" />
              <span>Analyzing Requirement Guardrails...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>Generate Traceable UAT TestPack</span>
            </>
          )}
        </button>

        {error && <div className="text-xs text-rose-400 font-semibold">{error}</div>}
      </div>

      {result && (
        <div className="p-6 bg-slate-950 border border-slate-800 rounded-2xl space-y-3">
          <div className="flex items-center space-x-2 text-emerald-400 text-xs font-bold">
            <CheckCircle2 className="w-4 h-4" />
            <span>TestPack Generated Successfully</span>
          </div>
          <pre className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs text-cyan-300 overflow-x-auto font-mono max-h-96">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
