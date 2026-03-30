"use client";

interface HeroSearchProps {
  onAnalyze: (ticker: string) => void;
  loading: boolean;
}

export default function HeroSearch({ onAnalyze, loading }: HeroSearchProps) {
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const ticker = formData.get("ticker") as string;
    if (ticker?.trim()) {
      onAnalyze(ticker.trim().toUpperCase());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-3 max-w-lg mx-auto">
      <input
        type="text"
        name="ticker"
        placeholder="Enter ticker (e.g., AAPL, TSLA, NVDA)"
        disabled={loading}
        className="flex-1 px-5 py-3 bg-slate-800 border border-slate-700 rounded-xl text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-lg disabled:opacity-50"
      />
      <button
        type="submit"
        disabled={loading}
        className="px-6 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors"
      >
        {loading ? "Analyzing..." : "Analyze 🐃🐻"}
      </button>
    </form>
  );
}
