"use client";

import { useState, useRef, useCallback } from "react";
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

  // Real-time state
  const [phase, setPhase] = useState<string>("");
  const [phaseMessage, setPhaseMessage] = useState("");
  const [companyInfo, setCompanyInfo] = useState<any>(null);
  const [streamVerdicts, setStreamVerdicts] = useState<Map<string, { verdict?: AgentVerdict; loading: boolean }>>(new Map());
  const [currentAgentId, setCurrentAgentId] = useState<string | null>(null);
  const [roundtableText, setRoundtableText] = useState("");
  const [showRoundtable, setShowRoundtable] = useState(false);
  const [debates, setDebates] = useState<Map<string, any>>(new Map());

  const resetState = useCallback(() => {
    setLoading(true);
    setError(null);
    setResult(null);
    setPhase("");
    setPhaseMessage("");
    setCompanyInfo(null);
    setStreamVerdicts(new Map());
    setCurrentAgentId(null);
    setRoundtableText("");
    setShowRoundtable(false);
    setDebates(new Map());
  }, []);

  async function analyzeStock(ticker: string) {
    resetState();

    try {
      const url = `${API_BASE}/api/analyze/stream?ticker=${encodeURIComponent(ticker)}&language=${language}`;
      const response = await fetch(url);
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Analysis failed");
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let currentEvent = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith("data: ") && currentEvent) {
            try {
              const data = JSON.parse(line.slice(6));
              handleSSEEvent(currentEvent, data);
            } catch {}
            currentEvent = "";
          }
        }
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleSSEEvent(event: string, data: any) {
    switch (event) {
      case "status":
        setPhase(data.phase);
        setPhaseMessage(data.message || "");
        break;
      case "company":
        setCompanyInfo(data);
        break;
      case "metrics":
        break;
      case "agent_start":
        setCurrentAgentId(data.agent_id);
        setStreamVerdicts(prev => {
          const next = new Map(prev);
          next.set(data.agent_id, { loading: true });
          return next;
        });
        break;
      case "agent_complete":
        setCurrentAgentId(null);
        setStreamVerdicts(prev => {
          const next = new Map(prev);
          next.set(data.agent_id, { verdict: data.verdict, loading: false });
          return next;
        });
        break;
      case "agent_error":
        setCurrentAgentId(null);
        setStreamVerdicts(prev => {
          const next = new Map(prev);
          next.set(data.agent_id, { loading: false });
          return next;
        });
        break;
      case "agent_debate":
        setDebates(prev => {
          const next = new Map(prev);
          next.set(data.agent_id, data.debate);
          return next;
        });
        break;
      case "report_chunk":
        setShowRoundtable(true);
        setRoundtableText(prev => prev + data.text);
        break;
      case "complete":
        setResult(data);
        break;
      case "error":
        setError(data.message);
        setLoading(false);
        break;
    }
  }

  const showStreaming = loading && !result;

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
              >EN</button>
              <button
                onClick={() => setLanguage("zh")}
                className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${language === "zh" ? "bg-[var(--color-accent-indigo)] text-white" : "text-[var(--color-text-dim)] hover:text-white"}`}
              >中文</button>
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
              : "Enter a ticker. 5 iconic investors analyze it from their unique perspectives. Get a debate-style report in seconds."}
          </p>
          <SearchBar onAnalyze={analyzeStock} loading={loading} language={language} />
          {error && (
            <div className="mt-6 p-4 bg-[var(--color-bear-dim)]/50 border border-[var(--color-bear)]/30 rounded-xl text-[var(--color-bear)] text-sm max-w-lg mx-auto">{error}</div>
          )}
          <AgentPreview language={language} />
        </header>
      )}

      {/* Streaming View */}
      {showStreaming && (
        <StreamingView
          phase={phase}
          phaseMessage={phaseMessage}
          companyInfo={companyInfo}
          verdicts={streamVerdicts}
          currentAgentId={currentAgentId}
          roundtableText={roundtableText}
          showRoundtable={showRoundtable}
          debates={debates}
          language={language}
        />
      )}

      {/* Final Result */}
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
    <form onSubmit={handleSubmit} className="flex gap-2 max-w-md mx-auto">
      <input
        type="text" name="ticker"
        placeholder={language === "zh" ? "输入股票代码（如 AAPL, TSLA）" : "Enter ticker (AAPL, TSLA, NVDA)"}
        disabled={loading}
        className="flex-1 px-4 py-3 bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl text-white placeholder:text-[var(--color-text-dim)] focus:outline-none focus:border-[var(--color-accent-indigo)] focus:ring-1 focus:ring-[var(--color-accent-indigo)] text-sm disabled:opacity-50 font-mono"
      />
      <button type="submit" disabled={loading}
        className="px-5 py-3 bg-[var(--color-accent-indigo)] hover:bg-[var(--color-accent-blue)] disabled:opacity-50 text-white font-semibold rounded-xl transition-all text-sm"
      >
        {loading ? (language === "zh" ? "分析中..." : "Analyzing...") : (language === "zh" ? "开始分析" : "Analyze")}
      </button>
    </form>
  );
}

const AGENTS = [
  { id: "buffett", name: "Warren Buffett", emoji: "🤵", style: "Value Investing", color: "#3b82f6" },
  { id: "wood", name: "Cathie Wood", emoji: "👩", style: "Disruptive Innovation", color: "#8b5cf6" },
  { id: "dalio", name: "Ray Dalio", emoji: "🧑", style: "Macro Cycle", color: "#06b6d4" },
  { id: "burry", name: "Michael Burry", emoji: "🧐", style: "Deep Value", color: "#ef4444" },
  { id: "lynch", name: "Peter Lynch", emoji: "👨", style: "Pragmatic Growth", color: "#f59e0b" },
  { id: "soros", name: "George Soros", emoji: "🦊", style: "Reflexivity", color: "#ec4899" },
  { id: "graham", name: "Ben Graham", emoji: "🐻", style: "Extreme Conservative", color: "#78716c" },
  { id: "druckenmiller", name: "S. Druckenmiller", emoji: "🐂", style: "Asymmetric Risk", color: "#14b8a6" },
  { id: "munger", name: "Charlie Munger", emoji: "🎩", style: "Mental Models", color: "#a3a3a3" },
  { id: "taleb", name: "Nassim Taleb", emoji: "🎲", style: "Black Swan", color: "#dc2626" },
];

function AgentPreview({ language }: { language: string }) {
  return (
    <div className="mt-16">
      <p className="text-xs text-[var(--color-text-dim)] uppercase tracking-widest mb-6">
        {language === "zh" ? "投资大师阵容" : "The Panel"}
      </p>
      <div className="flex flex-wrap justify-center gap-3">
        {AGENTS.map((a) => (
          <div key={a.id} className="flex flex-col items-center gap-1.5 px-3 py-2 rounded-xl bg-[var(--color-bg-card)]/50 border border-[var(--color-border)]/50 min-w-[100px]">
            <span className="text-2xl">{a.emoji}</span>
            <span className="text-[10px] font-medium text-[var(--color-text-primary)]">{a.name}</span>
            <span className="text-[9px] text-[var(--color-text-dim)]" style={{ color: a.color }}>{a.style}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function StreamingView({ phase, phaseMessage, companyInfo, verdicts, currentAgentId, roundtableText, showRoundtable, debates, language }: {
  phase: string;
  phaseMessage: string;
  companyInfo: any;
  verdicts: Map<string, { verdict?: AgentVerdict; loading: boolean }>;
  currentAgentId: string | null;
  roundtableText: string;
  showRoundtable: boolean;
  debates: Map<string, any>;
  language: string;
}) {
  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      {/* Company Header */}
      {companyInfo && (
        <div className="text-center mb-10 animate-fade-up">
          <div className="text-xs text-[var(--color-text-dim)] uppercase tracking-widest mb-2">
            {companyInfo.ticker} · {companyInfo.latest_filings?.[0]?.form || ""} {companyInfo.latest_filings?.[0]?.date || ""}
          </div>
          <h2 className="text-2xl font-bold">{companyInfo.company_name}</h2>
        </div>
      )}

      {/* Agent Grid - Real Time */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {AGENTS.map((agent, idx) => {
          const state = verdicts.get(agent.id);
          const isActive = currentAgentId === agent.id;
          const isDone = state?.verdict != null;
          const v = state?.verdict;

          return (
            <div key={agent.id}
              className={`animate-fade-up stagger-${idx + 1} rounded-2xl border transition-all duration-500 ${
                isActive ? "border-[var(--color-accent-indigo)] glow-blue bg-[var(--color-bg-card)]" :
                isDone ? "border-[var(--color-border)] bg-[var(--color-bg-card)]" :
                "border-[var(--color-border)]/40 bg-[var(--color-bg-secondary)]/50"
              }`}
            >
              <div className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className={`text-xl ${isActive ? "animate-bounce" : ""}`}>{agent.emoji}</span>
                    <div>
                      <div className="text-xs font-semibold">{agent.name}</div>
                      <div className="text-[10px]" style={{ color: agent.color }}>{agent.style}</div>
                    </div>
                  </div>
                  {isDone && v && (
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-md border ${
                      v.rating.includes("Buy") ? "bg-[var(--color-bull-dim)] border-[var(--color-bull)]/30 text-[var(--color-bull)]" :
                      v.rating.includes("Sell") ? "bg-[var(--color-bear-dim)] border-[var(--color-bear)]/30 text-[var(--color-bear)]" :
                      "bg-[var(--color-neutral-dim)]/50 border-[var(--color-neutral)]/20 text-[var(--color-neutral)]"
                    }`}>{v.rating}</span>
                  )}
                </div>

                {isActive && !isDone && (
                  <div className="flex items-center gap-2 text-xs text-[var(--color-accent-indigo)]">
                    <div className="flex gap-1">
                      <span className="w-1 h-1 rounded-full bg-[var(--color-accent-indigo)] animate-pulse" style={{ animationDelay: "0s" }} />
                      <span className="w-1 h-1 rounded-full bg-[var(--color-accent-indigo)] animate-pulse" style={{ animationDelay: "0.2s" }} />
                      <span className="w-1 h-1 rounded-full bg-[var(--color-accent-indigo)] animate-pulse" style={{ animationDelay: "0.4s" }} />
                    </div>
                    <span>{language === "zh" ? "正在分析..." : "Analyzing..."}</span>
                  </div>
                )}

                {isDone && v && (
                  <div>
                    <p className="text-xs text-[var(--color-text-secondary)] italic leading-relaxed mb-2">&ldquo;{v.summary}&rdquo;</p>
                    {v.bull_case.length > 0 && (
                      <div className="space-y-1">
                        {v.bull_case.slice(0, 2).map((p, i) => (
                          <div key={i} className="text-[10px] text-[var(--color-text-dim)] flex items-start gap-1">
                            <span className="text-[var(--color-bull)]">✅</span>
                            <span className="line-clamp-2">{p}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {!isActive && !isDone && !state?.loading && (
                  <div className="text-[10px] text-[var(--color-text-dim)]">
                    {language === "zh" ? "等待中" : "Waiting..."}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Debate Round — Live clashes */}
      {debates.size > 0 && (
        <div className="animate-fade-up mb-8">
          <div className="text-xs text-[var(--color-text-dim)] uppercase tracking-widest mb-4">
            ⚔️ {language === "zh" ? "激烈辩论中" : "Cross-Examination"}
          </div>
          <div className="space-y-3">
            {Array.from(debates.entries()).map(([agentId, debate]) => {
              if (!debate?.challenges?.length && !debate?.concessions?.length) return null;
              return (
                <div key={agentId} className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-lg">{debate.emoji}</span>
                    <span className="text-xs font-semibold">{debate.agent_name}</span>
                    <span className="text-[10px] text-[var(--color-accent-indigo)]">
                      {language === "zh" ? "回应：" : "responds"}
                    </span>
                  </div>
                  {debate.challenges?.map((c: any, i: number) => (
                    <div key={i} className="mb-2 pl-3 border-l-2 border-[var(--color-bear)]/40">
                      <div className="text-[10px] text-[var(--color-bear)] font-semibold mb-0.5">
                        🎯 → {c.target}
                      </div>
                      <div className="text-xs text-[var(--color-text-secondary)]">{c.counter}</div>
                    </div>
                  ))}
                  {debate.concessions?.map((c: any, i: number) => (
                    <div key={i} className="mb-2 pl-3 border-l-2 border-[var(--color-bull)]/40">
                      <div className="text-[10px] text-[var(--color-bull)] font-semibold mb-0.5">
                        🤝 ← {c.source}
                      </div>
                      <div className="text-xs text-[var(--color-text-secondary)]">{c.why}</div>
                    </div>
                  ))}
                  {debate.final_statement && (
                    <div className="mt-2 text-xs text-[var(--color-text-dim)] italic border-t border-[var(--color-border)]/40 pt-2">
                      "{debate.final_statement}"
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Roundtable Streaming - Typewriter Effect */}
      {showRoundtable && roundtableText && (
        <div className="animate-fade-up mb-8">
          <div className="text-xs text-[var(--color-text-dim)] uppercase tracking-widest mb-4">
            🏛️ {language === "zh" ? "圆桌讨论（实时）" : "Roundtable Discussion (Live)"}
          </div>
          <div className="bg-[var(--color-bg-card)] border border-[var(--color-accent-indigo)]/30 rounded-2xl p-6 glow-blue">
            <div className="text-sm text-[var(--color-text-secondary)] whitespace-pre-line leading-relaxed font-serif">
              {roundtableText}
              <span className="inline-block w-2 h-4 bg-[var(--color-accent-indigo)] animate-pulse ml-0.5 align-middle" />
            </div>
          </div>
        </div>
      )}

      {/* Phase Status */}
      <div className="text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-[var(--color-bg-card)] rounded-xl border border-[var(--color-border)] text-xs text-[var(--color-text-dim)]">
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--color-accent-indigo)] animate-pulse" />
          {phaseMessage}
        </div>
      </div>
    </div>
  );
}
