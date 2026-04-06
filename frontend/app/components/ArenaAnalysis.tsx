"use client";
import { AnalysisResult, AgentVerdict } from "../page";

interface Props {
  result: AnalysisResult;
  language: string;
}

function ratingColor(r: string) {
  const m: Record<string, string> = {
    "Strong Buy": "text-[var(--color-bull)]", "Buy": "text-[var(--color-bull)]",
    "Hold": "text-[var(--color-neutral)]",
    "Sell": "text-[var(--color-bear)]", "Strong Sell": "text-[var(--color-bear)]",
  };
  return m[r] || "text-[var(--color-text-secondary)]";
}

function ratingBg(r: string) {
  const m: Record<string, string> = {
    "Strong Buy": "bg-[var(--color-bull-dim)] border-[var(--color-bull)]/30 text-[var(--color-bull)]",
    "Buy": "bg-[var(--color-bull-dim)]/50 border-[var(--color-bull)]/20 text-[var(--color-bull)]",
    "Hold": "bg-[var(--color-neutral-dim)]/50 border-[var(--color-neutral)]/20 text-[var(--color-neutral)]",
    "Sell": "bg-[var(--color-bear-dim)]/50 border-[var(--color-bear)]/20 text-[var(--color-bear)]",
    "Strong Sell": "bg-[var(--color-bear-dim)] border-[var(--color-bear)]/30 text-[var(--color-bear)]",
  };
  return m[r] || "bg-[var(--color-bg-card)] border-[var(--color-border)]";
}

function scoreColor(s: number) {
  if (s >= 70) return "var(--color-bull)";
  if (s >= 40) return "var(--color-neutral)";
  return "var(--color-bear)";
}

function ScoreRing({ score }: { score: number }) {
  const r = 54, c = 2 * Math.PI * r;
  const offset = c - (score / 100) * c;
  const color = scoreColor(score);
  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="140" height="140" className="-rotate-90">
        <circle cx="70" cy="70" r={r} stroke="var(--color-border)" strokeWidth="6" fill="none" />
        <circle cx="70" cy="70" r={r} stroke={color} strokeWidth="6" fill="none"
          strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round"
          className="score-ring-animated" />
      </svg>
      <div className="absolute text-center">
        <div className="text-3xl font-bold font-mono" style={{ color }}>{score}</div>
        <div className="text-[10px] text-[var(--color-text-dim)]">/100</div>
      </div>
    </div>
  );
}

function AgentCard({ v, idx }: { v: AgentVerdict; idx: number }) {
  return (
    <div className={`animate-fade-up stagger-${idx + 1} bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-2xl overflow-hidden`}>
      {/* Header */}
      <div className="px-5 py-4 border-b border-[var(--color-border)]/60 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{v.emoji}</span>
          <div>
            <div className="font-semibold text-sm">{v.agent_name}</div>
            <div className="text-[10px] text-[var(--color-text-dim)]">{v.style}</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-[10px] text-[var(--color-text-dim)]">Confidence</div>
            <div className="text-xs font-mono">{(v.confidence * 100).toFixed(0)}%</div>
          </div>
          <span className={`px-3 py-1 rounded-lg text-xs font-bold border ${ratingBg(v.rating)}`}>
            {v.rating}
          </span>
        </div>
      </div>

      {/* Summary */}
      <div className="px-5 py-3 border-b border-[var(--color-border)]/40">
        <p className="text-sm text-[var(--color-text-secondary)] italic leading-relaxed">&ldquo;{v.summary}&rdquo;</p>
      </div>

      {/* Bull / Bear */}
      <div className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-[var(--color-border)]/40">
        <div className="px-5 py-3">
          <div className="text-[10px] font-semibold text-[var(--color-bull)] uppercase tracking-wider mb-2">
            ✅ Bull Case
          </div>
          <ul className="space-y-1.5">
            {v.bull_case.map((p, i) => (
              <li key={i} className="text-xs text-[var(--color-text-secondary)] leading-relaxed">{p}</li>
            ))}
            {v.bull_case.length === 0 && <li className="text-xs text-[var(--color-text-dim)] italic">—</li>}
          </ul>
        </div>
        <div className="px-5 py-3">
          <div className="text-[10px] font-semibold text-[var(--color-bear)] uppercase tracking-wider mb-2">
            ⚠️ Bear Case
          </div>
          <ul className="space-y-1.5">
            {v.bear_case.map((p, i) => (
              <li key={i} className="text-xs text-[var(--color-text-secondary)] leading-relaxed">{p}</li>
            ))}
            {v.bear_case.length === 0 && <li className="text-xs text-[var(--color-text-dim)] italic">—</li>}
          </ul>
        </div>
      </div>

      {/* Key Insights - expandable */}
      {Object.keys(v.key_insights).length > 0 && (
        <details className="border-t border-[var(--color-border)]/40">
          <summary className="px-5 py-2.5 text-[10px] font-semibold text-[var(--color-accent-indigo)] uppercase tracking-wider cursor-pointer hover:bg-[var(--color-bg-card-hover)] transition-colors">
            💡 Key Insights ({Object.keys(v.key_insights).length})
          </summary>
          <div className="px-5 pb-4 space-y-3">
            {Object.entries(v.key_insights).map(([k, val]) => (
              <div key={k}>
                <div className="text-[10px] font-medium text-[var(--color-text-dim)] uppercase mb-0.5">{k.replace(/_/g, ' ')}</div>
                <div className="text-xs text-[var(--color-text-secondary)] leading-relaxed">{val}</div>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}

export default function ArenaAnalysis({ result, language }: Props) {
  return (
    <div className="max-w-7xl mx-auto px-6 pb-16">
      {/* Header */}
      <div className="text-center pt-8 pb-10 animate-fade-up">
        <div className="text-xs text-[var(--color-text-dim)] uppercase tracking-widest mb-2">
          {result.company_name} ({result.ticker}) · {result.latest_filing}
        </div>
        <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-1">
          🏟️ {result.title}
        </h2>
      </div>

      {/* Score + Sentiment Row */}
      <div className="flex flex-col sm:flex-row items-center justify-center gap-8 mb-12 animate-fade-up stagger-1">
        <ScoreRing score={result.overall_score} />
        <div className="text-center sm:text-left">
          <div className="text-2xl font-bold mb-2">{result.overall_sentiment}</div>
          {result.consensus.length > 0 && (
            <div className="space-y-1.5">
              {result.consensus.map((c, i) => (
                <div key={i} className="text-xs text-[var(--color-text-secondary)] flex items-start gap-2">
                  <span className="text-[var(--color-accent-indigo)] mt-0.5">🤝</span>
                  <span>{c}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Agent Verdicts */}
      <div className="mb-12">
        <div className="text-xs text-[var(--color-text-dim)] uppercase tracking-widest mb-4">
          {language === "zh" ? "📊 各分析师独立判断" : "📊 Individual Analyst Verdicts"}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {result.agent_verdicts.map((v, i) => (
            <AgentCard key={v.agent_id} v={v} idx={i} />
          ))}
        </div>
      </div>

      {/* Debates */}
      {result.debates?.length > 0 && (
        <div className="mb-12 animate-fade-up stagger-2">
          <div className="text-xs text-[var(--color-text-dim)] uppercase tracking-widest mb-4">
            ⚔️ {language === "zh" ? "关键辩论" : "Key Debates"}
          </div>
          <div className="space-y-4">
            {result.debates.map((d, i) => (
              <div key={i} className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-2xl p-5">
                <h4 className="font-semibold text-sm mb-3">{d.topic}</h4>
                <div className="space-y-2 mb-4">
                  {Object.entries(d.positions).map(([name, pos]) => (
                    <div key={name} className="flex items-start gap-2 text-xs">
                      <span className="font-medium text-[var(--color-accent-indigo)] min-w-[110px] shrink-0">{name}</span>
                      <span className="text-[var(--color-text-secondary)]">{pos}</span>
                    </div>
                  ))}
                </div>
                <div className="text-xs text-[var(--color-text-dim)] italic border-t border-[var(--color-border)]/40 pt-3">
                  💡 {d.verdict}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Roundtable */}
      {result.roundtable_summary && (
        <div className="mb-12 animate-fade-up stagger-3">
          <div className="text-xs text-[var(--color-text-dim)] uppercase tracking-widest mb-4">
            🏛️ {language === "zh" ? "圆桌讨论" : "Roundtable Discussion"}
          </div>
          <div className="bg-[var(--color-bg-card)] border border-[var(--color-border)] rounded-2xl p-6 sm:p-8">
            <div className="prose-dark text-sm whitespace-pre-line leading-relaxed">
              {result.roundtable_summary}
            </div>
          </div>
        </div>
      )}

      {/* Final */}
      {result.final_recommendation && (
        <div className="text-center mb-12 animate-fade-up stagger-4">
          <div className="inline-block bg-[var(--color-bg-card)] border border-[var(--color-accent-indigo)]/30 rounded-2xl p-6 max-w-2xl glow-blue">
            <div className="text-xs text-[var(--color-accent-indigo)] uppercase tracking-widest mb-2 font-semibold">
              🎯 {language === "zh" ? "最终建议" : "Final Takeaway"}
            </div>
            <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">{result.final_recommendation}</p>
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <div className="text-center text-[10px] text-[var(--color-text-dim)] border-t border-[var(--color-border)]/40 pt-6 max-w-xl mx-auto leading-relaxed">
        ⚠️ {result.disclaimer}
        <br />Generated by <span className="text-[var(--color-accent-indigo)]">BullBearArena</span> 🐃🐻
      </div>
    </div>
  );
}
