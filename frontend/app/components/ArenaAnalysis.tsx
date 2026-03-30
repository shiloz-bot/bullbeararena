"use client";

import { AnalysisResult, AgentVerdict } from "../page";

interface Props {
  result: AnalysisResult;
}

function RatingBadge({ rating }: { rating: string }) {
  const colors: Record<string, string> = {
    "Strong Buy": "bg-green-500/20 text-green-300 border-green-500/30",
    "Buy": "bg-green-500/10 text-green-400 border-green-500/20",
    "Hold": "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
    "Sell": "bg-red-500/10 text-red-400 border-red-500/20",
    "Strong Sell": "bg-red-500/20 text-red-300 border-red-500/30",
  };
  return (
    <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${colors[rating] || "bg-slate-700 text-slate-300"}`}>
      {rating}
    </span>
  );
}

function ScoreRing({ score }: { score: number }) {
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 70 ? "#22c55e" : score >= 40 ? "#fbbf24" : "#ef4444";

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="160" height="160" className="-rotate-90">
        <circle cx="80" cy="80" r={radius} stroke="#334155" strokeWidth="8" fill="none" />
        <circle
          cx="80" cy="80" r={radius}
          stroke={color} strokeWidth="8" fill="none"
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1s ease-out" }}
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-3xl font-bold" style={{ color }}>{score}</div>
        <div className="text-xs text-slate-400">/100</div>
      </div>
    </div>
  );
}

function VerdictCard({ verdict }: { verdict: AgentVerdict }) {
  return (
    <div className="agent-card bg-slate-800/50 border border-slate-700/50 rounded-2xl p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <span className="text-2xl mr-2">{verdict.emoji}</span>
          <span className="font-bold text-lg">{verdict.agent_name}</span>
          <span className="ml-2 text-xs text-slate-400 bg-slate-700/50 px-2 py-0.5 rounded-full">
            {verdict.style}
          </span>
        </div>
        <RatingBadge rating={verdict.rating} />
      </div>

      <p className="text-slate-300 italic mb-4">&ldquo;{verdict.summary}&rdquo;</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <h4 className="text-xs font-semibold text-green-400 mb-2 uppercase tracking-wider">Bull Case</h4>
          <ul className="space-y-1">
            {verdict.bull_case.map((point, i) => (
              <li key={i} className="text-sm text-slate-300 flex items-start">
                <span className="text-green-400 mr-2">✅</span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h4 className="text-xs font-semibold text-red-400 mb-2 uppercase tracking-wider">Bear Case</h4>
          <ul className="space-y-1">
            {verdict.bear_case.map((point, i) => (
              <li key={i} className="text-sm text-slate-300 flex items-start">
                <span className="text-red-400 mr-2">⚠️</span>
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-4 flex items-center text-sm text-slate-400">
        <span>Confidence: {(verdict.confidence * 100).toFixed(0)}%</span>
        <div className="ml-2 flex-1 bg-slate-700 rounded-full h-2">
          <div
            className="bg-indigo-500 rounded-full h-2 transition-all duration-500"
            style={{ width: `${verdict.confidence * 100}%` }}
          />
        </div>
      </div>
    </div>
  );
}

export default function ArenaAnalysis({ result }: Props) {
  return (
    <section className="max-w-6xl mx-auto px-4 py-12">
      {/* Header */}
      <div className="text-center mb-12">
        <h2 className="text-3xl md:text-4xl font-bold mb-2">
          🏟️ {result.title}
        </h2>
        <p className="text-slate-400">
          {result.company_name} ({result.ticker}) • {result.latest_filing}
        </p>
      </div>

      {/* Score + Sentiment */}
      <div className="flex flex-col md:flex-row items-center justify-center gap-8 mb-12">
        <ScoreRing score={result.overall_score} />
        <div className="text-center md:text-left">
          <div className="text-2xl font-bold mb-2">{result.overall_sentiment}</div>
          {result.consensus.length > 0 && (
            <div className="space-y-1">
              {result.consensus.map((c, i) => (
                <p key={i} className="text-sm text-slate-400">🤝 {c}</p>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Agent Verdicts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12">
        {result.agent_verdicts.map((v) => (
          <VerdictCard key={v.agent_id} verdict={v} />
        ))}
      </div>

      {/* Debates */}
      {result.debates && result.debates.length > 0 && (
        <div className="mb-12">
          <h3 className="text-2xl font-bold mb-6 text-center">⚔️ Key Debates</h3>
          <div className="space-y-6">
            {result.debates.map((debate, i) => (
              <div key={i} className="bg-slate-800/30 border border-slate-700/30 rounded-xl p-6">
                <h4 className="text-lg font-semibold mb-4">{debate.topic}</h4>
                <div className="space-y-2 mb-4">
                  {Object.entries(debate.positions).map(([agent, position]) => (
                    <div key={agent} className="flex items-start gap-2 text-sm">
                      <span className="font-semibold text-indigo-300 min-w-[120px]">{agent}:</span>
                      <span className="text-slate-300">{position}</span>
                    </div>
                  ))}
                </div>
                <p className="text-sm text-slate-400 italic">💡 {debate.verdict}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Roundtable */}
      {result.roundtable_summary && (
        <div className="mb-12">
          <h3 className="text-2xl font-bold mb-6 text-center">🏛️ Roundtable Discussion</h3>
          <div className="bg-slate-800/30 border border-slate-700/30 rounded-2xl p-8">
            <div className="prose prose-invert max-w-none text-slate-300 whitespace-pre-line leading-relaxed">
              {result.roundtable_summary}
            </div>
          </div>
        </div>
      )}

      {/* Final Recommendation */}
      {result.final_recommendation && (
        <div className="mb-12 text-center">
          <div className="inline-block bg-indigo-950/50 border border-indigo-700/30 rounded-2xl p-8 max-w-2xl">
            <h3 className="text-lg font-bold mb-3">🎯 Final Takeaway</h3>
            <p className="text-slate-300">{result.final_recommendation}</p>
          </div>
        </div>
      )}

      {/* Disclaimer */}
      <div className="text-center text-xs text-slate-500 mt-12 border-t border-slate-800 pt-6">
        <p>⚠️ {result.disclaimer}</p>
        <p className="mt-1">Generated by BullBearArena 🐃🐻</p>
      </div>
    </section>
  );
}
