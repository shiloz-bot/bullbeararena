const AGENTS = [
  { id: "buffett", name: "Warren Buffett", emoji: "🤵", style: "Value Investing", desc: "Moats, ROE, and free cash flow" },
  { id: "wood", name: "Cathie Wood", emoji: "👩", style: "Disruptive Innovation", desc: "5-year horizons and exponential growth" },
  { id: "dalio", name: "Ray Dalio", emoji: "🧑", style: "Macro Cycle", desc: "Economic machines and paradigm shifts" },
  { id: "burry", name: "Michael Burry", emoji: "🧐", style: "Deep Value / Contrarian", desc: "Finding what others miss" },
  { id: "lynch", name: "Peter Lynch", emoji: "👨", style: "Pragmatic Growth", desc: "Buy what you know, find tenbaggers" },
];

export default function AgentCards() {
  return (
    <section className="py-16 px-4">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-2">Meet the Investors</h2>
        <p className="text-slate-400 text-center mb-12">Five legendary perspectives. One arena.</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {AGENTS.map((agent) => (
            <div
              key={agent.id}
              className="agent-card bg-[var(--surface)] rounded-2xl p-6 text-center border border-slate-700/50"
            >
              <div className="text-5xl mb-4">{agent.emoji}</div>
              <h3 className="font-bold text-lg mb-1">{agent.name}</h3>
              <span className="inline-block px-3 py-1 text-xs font-medium bg-indigo-950 text-indigo-300 rounded-full mb-2">
                {agent.style}
              </span>
              <p className="text-sm text-slate-400">{agent.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
