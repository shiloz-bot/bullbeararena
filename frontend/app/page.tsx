"use client";

import { useState } from "react";
import ArenaAnalysis from "./components/ArenaAnalysis";
import HeroSearch from "./components/HeroSearch";
import AgentCards from "./components/AgentCards";

export interface AnalysisResult {
  success: boolean;
  ticker: string;
  company_name: string;
  latest_filing: string;
  overall_score: number;
  overall_sentiment: string;
  title: string;
  consensus: string[];
  debates: { topic: string; positions: Record<string, string>; verdict: string }[];
  agent_verdicts: AgentVerdict[];
  roundtable_summary: string;
  final_recommendation: string;
  disclaimer: string;
}

export interface AgentVerdict {
  agent_id: string;
  agent_name: string;
  emoji: string;
  style: string;
  rating: string;
  confidence: number;
  bull_case: string[];
  bear_case: string[];
  key_insights: Record<string, string>;
  summary: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function analyzeStock(ticker: string) {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Analysis failed");
      }

      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen">
      {/* Hero Section */}
      <header className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-indigo-950/50 to-transparent" />
        <div className="relative max-w-6xl mx-auto px-4 pt-16 pb-12 text-center">
          <h1 className="text-5xl md:text-6xl font-bold mb-4">
            <span className="text-green-400">🐃</span> Bull
            <span className="text-red-400">Bear</span>
            <span className="text-indigo-400">Arena</span> 🐻
          </h1>
          <p className="text-xl text-slate-400 mb-8 max-w-2xl mx-auto">
            Watch legendary investors debate any stock. AI-powered multi-perspective analysis in seconds.
          </p>

          <HeroSearch onAnalyze={analyzeStock} loading={loading} />

          {error && (
            <div className="mt-6 p-4 bg-red-950/50 border border-red-800 rounded-xl text-red-300 max-w-xl mx-auto">
              {error}
            </div>
          )}
        </div>
      </header>

      {/* Agent Preview (shown when no analysis) */}
      {!result && !loading && <AgentCards />}

      {/* Loading State */}
      {loading && <LoadingState />}

      {/* Analysis Results */}
      {result && <ArenaAnalysis result={result} />}
    </main>
  );
}

function LoadingState() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-20 text-center">
      <div className="flex justify-center gap-3 mb-6">
        <div className="loading-dot w-3 h-3 rounded-full bg-indigo-400" />
        <div className="loading-dot w-3 h-3 rounded-full bg-indigo-400" />
        <div className="loading-dot w-3 h-3 rounded-full bg-indigo-400" />
      </div>
      <h3 className="text-2xl font-bold text-indigo-300 mb-2">The Arena is in Session</h3>
      <p className="text-slate-400">
        Our investors are reviewing the financials... This takes about 15-30 seconds.
      </p>
      <div className="mt-8 flex justify-center gap-4 text-3xl animate-pulse">
        <span>🤵</span><span>👩</span><span>🧑</span><span>🧐</span><span>👨</span>
      </div>
    </div>
  );
}
