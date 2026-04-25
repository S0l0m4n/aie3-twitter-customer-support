export function SourcePanel({ sources }) {
  return (
    <div className="space-y-4">
      <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
        Retrieved sources ({sources.length})
      </h2>
      <div className="space-y-3">
        {sources.map((src, i) => (
          <SourceCard key={src.ticket_id ?? i} source={src} rank={i + 1} />
        ))}
      </div>
    </div>
  );
}

function SourceCard({ source, rank }) {
  const pct = Math.round(source.similarity * 100);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 mono">#{rank} · {source.ticket_id}</span>
        <SimilarityBadge similarity={source.similarity} />
      </div>

      <div>
        <div className="w-full bg-slate-100 rounded-full h-1.5 mb-3">
          <div
            className="bar-fill h-1.5 rounded-full bg-brand-500"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      <div className="space-y-2">
        <div>
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">Customer</span>
          <p className="text-xs text-slate-700 mt-0.5 leading-relaxed">{source.customer_text}</p>
        </div>
        <div>
          <span className="text-xs font-medium text-slate-400 uppercase tracking-wide">Brand reply</span>
          <p className="text-xs text-slate-500 mt-0.5 leading-relaxed italic">{source.brand_reply}</p>
        </div>
      </div>
    </div>
  );
}

function SimilarityBadge({ similarity }) {
  const pct = Math.round(similarity * 100);
  let color = 'bg-slate-100 text-slate-600';
  if (pct >= 85) color = 'bg-emerald-100 text-emerald-700';
  else if (pct >= 70) color = 'bg-amber-100 text-amber-700';

  return (
    <span className={`text-xs font-bold mono px-2 py-0.5 rounded ${color}`}>
      {pct}% match
    </span>
  );
}