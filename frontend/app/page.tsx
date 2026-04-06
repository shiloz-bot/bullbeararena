"use client";

import { useState } from "react";
import dynamic from "next/dynamic";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

const ArenaAnalysis = dynamic(() => import("./components/ArenaAnalysis"), { ssr: false });

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState<"en" | "zh">("en");

  async function analyzeStock(ticker: string) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticker, language }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Analysis failed");
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen main-grid">
      {/* Top Bar */}
      <nav className="border-b border-[var(--color-border)] bg-[var(--color-bg-primary)]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold tracking-tight">
              <span className="text-[var(--color-bull)]">Bull</span>
              <span className="text-[var(--color-bear)]">Bear</span>
              <span className="text-[var(--color-accent-indigo)]">Arena</span>
            </span>
            <span className="text-xs text-[var(--color-text-dim)] ml-1 hidden sm:inline">AI Stock Analysis</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex bg-[var(--color-bg-card)] rounded-lg p-0.5 border border-[var(--color-border)]">
              <button
                onClick={() => setLanguage("en")}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${language === "en" ? "bg-[var(--color-accent-indigo)] text-white" : "text-[var(--color-text-dim)] hover:text-white"}`}
              >
                EN
              </button>
              <button
                onClick={() => setLanguage("zh")}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${language === "zh" ? "bg-[var(--color-accent-indigo)] text-white" : "text-[var(--color-text-dim)] hover:text-white"}`}
              >
                中文
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      {!result && !loading && (
        <header className="max-w-4xl mx-auto px-6 pt-20 pb-16 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-[var(--color-bg-card)] rounded-full border border-[var(--color-border)] text-xs text-[var(--color-text-dim)] mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-bull)] animate-pulse" />
            {language === "zh" ? "AI 驱动的多视角股票分析" : "AI-Powered Multi-Perspective Analysis"}
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-4 leading-tight">
            {language === "zh" ? (
              <>让传奇投资者为你<span className="text-[var(--color-accent-indigo)]">辩论</span>任何股票</>
            ) : (
              <>Legendary Investors<br /><span className="text-[var(--color-accent-indigo)]">Debate</span> Any Stock</>
            )}
          </h1>
          <p className="text-lg text-[var(--color-text-secondary)] mb-10 max-w-xl mx-auto">
            {language === "zh"
              ? "输入股票代码，5 位投资大师将用各自独特的视角为你深度分析，生成辩论式报告。"
              : "Enter a ticker. 5 iconic investors analyze it from their unique perspectives. Get a debate-style report in seconds."
            }
          </p>
          <SearchBar onAnalyze={analyzeStock} loading={loading} language={language} />
          {error && (
            <div className="mt-6 p-4 bg-[var(--color-bear-dim)]/50 border border-[var(--color-bear)]/30 rounded-xl text-[var(--color-bear)] text-sm max-w-lg mx-auto">
              {error}
            </div>
          )}
          <AgentPreview language={language} />
        </header>
      )}

      {loading && <LoadingState language={language} />}
      {result && (
        <>
          <div className="max-w-7xl mx-auto px-6 pt-6 pb-4">
            <SearchBar onAnalyze={analyzeStock} loading={loading} language={language} compact />
          </div>
          <ArenaAnalysis result={result} language={language} />
        </>
      )}
    </main>
  );
}

function SearchBar({ onAnalyze, loading, language, compact }: { onAnalyze: (t: string) => void; loading: boolean; language: string; compact?: boolean }) {
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const ticker = new FormData(e.currentTarget).get("ticker") as string;
    if (ticker?.trim()) onAnalyze(ticker.trim().toUpperCase());
  };

  return (
    <form onSubmit={handleSubmit} className={`flex gap-2 max-w-md mx-auto ${compact ? "" : ""}`}>
      <input
        type="text"
        name="ticker"
        placeholder={language === "zh" ? "输入股票代码（如 AAPL, TSLA）" : "Enter ticker (AAPL, TSLA, NVDA)"}
        disabled={loading}
        className="flex-1 px-4 py-3 bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl text-white placeholder:text-[var(--color-text-dim)] focus:outline-none focus:border-[var(--color-accent-indigo)] focus:ring-1 focus:ring-[var(--color-accent-indigo)] text-sm disabled:opacity-50 font-mono"
      />
      <button
        type="submit"
        disabled={loading}
        className="px-5 py-3 bg-[var(--color-accent-indigo)] hover:bg-[var(--color-accent-blue)] disabled:opacity-50 text-white font-semibold rounded-xl transition-all text-sm"
      >
        {loading
          ? (language === "zh" ? "分析中..." : "Analyzing...")
          : (language === "zh" ? "开始分析" : "Analyze")
        }
      </button>
    </form>
  );
}

const AGENTS = [
  { name: "Warren Buffett", emoji: "🤵", style: "Value Investing", color: "#3b82f6" },
  { name: "Cathie Wood", emoji: "👩", style: "Disruptive Innovation", color: "#8b5cf6" },
  { name: "Ray Dalio", emoji: "🧑", style: "Macro Cycle", color: "#06b6d4" },
  { name: "Michael Burry", emoji: "🧐", style: "Deep Value", color: "#ef4444" },
  { name: "Peter Lynch", emoji: "👨", style: "Pragmatic Growth", color: "#f59e0b" },
];

function AgentPreview({ language }: { language: string }) {
  return (
    <div className="mt-16">
      <p className="text-xs text-[var(--color-text-dim)] uppercase tracking-widest mb-6">
        {language === "zh" ? "投资大师阵容" : "The Panel"}
      </p>
      <div className="flex flex-wrap justify-center gap-4">
        {AGENTS.map((a) => (
          <div key={a.name} className="flex flex-col items-center gap-2 px-4 py-3 rounded-xl bg-[var(--color-bg-card)]/50 border border-[var(--color-border)]/50 min-w-[120px]">
            <span className="text-3xl">{a.emoji}</span>
            <span className="text-xs font-medium text-[var(--color-text-primary)]">{a.name}</span>
            <span className="text-[10px] text-[var(--color-text-dim)]" style={{ color: a.color }}>{a.style}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function LoadingState({ language }: { language: string }) {
  return (
    <div className="max-w-2xl mx-auto px-6 py-32 text-center">
      <div className="flex justify-center gap-2 mb-8">
        {AGENTS.map((a, i) => (
          <span key={a.name} className="text-3xl animate-bounce" style={{ animationDelay: `${i * 0.15}s` }}>
            {a.emoji}
          </span>
        ))}
      </div>
      <h3 className="text-xl font-semibold text-[var(--color-accent-indigo)] mb-2">
        {language === "zh" ? "竞技场辩论中" : "The Arena is in Session"}
      </h3>
      <p className="text-sm text-[var(--color-text-dim)]">
        {language === "zh" ? "投资大师们正在审阅财报数据... 大约需要 15-30 秒" : "Investors are reviewing the financials... This takes about 15-30 seconds."}
      </p>
      <div className="mt-6 flex justify-center">
        <div className="w-48 h-1 bg-[var(--color-bg-card)] rounded-full overflow-hidden">
          <div className="h-full bg-[var(--color-accent-indigo)] rounded-full animate-pulse" style={{ width: "60%" }} />
        </div>
      </div>
    </div>
  );
}
