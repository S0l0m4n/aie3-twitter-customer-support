export function ComparisonTable({ ragAnswer, noRagAnswer, mlPrediction, llmPrediction }) {
  const cols = [
    {
      key: 'rag',
      label: 'RAG Answer',
      sub: 'with context',
      latency: ragAnswer.latency_ms,
      cost: ragAnswer.cost_usd,
      label_val: null,
      confidence: null,
    },
    {
      key: 'no_rag',
      label: 'No-RAG Answer',
      sub: 'no context',
      latency: noRagAnswer.latency_ms,
      cost: noRagAnswer.cost_usd,
      label_val: null,
      confidence: null,
    },
    {
      key: 'ml',
      label: 'ML Model',
      sub: 'scikit-learn',
      latency: mlPrediction.latency_ms,
      cost: mlPrediction.cost_usd,
      label_val: mlPrediction.label,
      confidence: mlPrediction.confidence,
    },
    {
      key: 'llm',
      label: 'LLM Prediction',
      sub: 'zero-shot',
      latency: llmPrediction.latency_ms,
      cost: llmPrediction.cost_usd,
      label_val: llmPrediction.label,
      confidence: llmPrediction.confidence,
    },
  ];

  return (
    <div className="space-y-3">
      <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
        Stats comparison
      </h2>
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100">
              <th className="text-left px-4 py-3 text-xs font-semibold text-slate-400 uppercase tracking-wide w-32">
                Metric
              </th>
              {cols.map((c) => (
                <th key={c.key} className="text-left px-4 py-3">
                  <div className="font-semibold text-slate-800">{c.label}</div>
                  <div className="text-xs font-normal text-slate-400 mono">{c.sub}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            <tr className="hover:bg-slate-50">
              <td className="px-4 py-3 text-xs font-medium text-slate-500">Latency</td>
              {cols.map((c) => (
                <td key={c.key} className="px-4 py-3 mono text-slate-700">
                  {formatLatency(c.latency)}
                </td>
              ))}
            </tr>
            <tr className="hover:bg-slate-50">
              <td className="px-4 py-3 text-xs font-medium text-slate-500">Cost</td>
              {cols.map((c) => (
                <td key={c.key} className="px-4 py-3 mono text-slate-700">
                  {c.cost === 0 ? <span className="text-emerald-600">$0.00</span> : `$${c.cost.toFixed(4)}`}
                </td>
              ))}
            </tr>
            <tr className="hover:bg-slate-50">
              <td className="px-4 py-3 text-xs font-medium text-slate-500">Priority</td>
              {cols.map((c) => (
                <td key={c.key} className="px-4 py-3">
                  {c.label_val ? <PriorityBadge label={c.label_val} /> : <span className="text-slate-300">—</span>}
                </td>
              ))}
            </tr>
            <tr className="hover:bg-slate-50">
              <td className="px-4 py-3 text-xs font-medium text-slate-500">Confidence</td>
              {cols.map((c) => (
                <td key={c.key} className="px-4 py-3 mono text-slate-700">
                  {c.confidence != null
                    ? <ConfidenceBar value={c.confidence} />
                    : <span className="text-slate-300">—</span>}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
      <p className="text-xs text-slate-400">
        ML confidence: calibrated <code className="mono">predict_proba</code>.
        LLM confidence: self-reported — not statistically calibrated.
      </p>
    </div>
  );
}

function PriorityBadge({ label }) {
  const isUrgent = label === 'urgent';
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold mono ${
        isUrgent ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-600'
      }`}
    >
      {isUrgent ? '⚠ urgent' : '✓ normal'}
    </span>
  );
}

function ConfidenceBar({ value }) {
  const pct = Math.round(value * 100);
  const barColor = pct >= 80 ? 'bg-brand-500' : pct >= 60 ? 'bg-amber-400' : 'bg-red-400';
  return (
    <div className="flex items-center gap-2">
      <div className="w-16 bg-slate-100 rounded-full h-1.5 flex-shrink-0">
        <div className={`bar-fill h-1.5 rounded-full ${barColor}`} style={{ width: `${pct}%` }} />
      </div>
      <span>{pct}%</span>
    </div>
  );
}

function formatLatency(ms) {
  if (ms < 1) return `${ms.toFixed(2)} ms`;
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(1)} s`;
}