export function AnswerPanel({ ragAnswer, noRagAnswer }) {
  return (
    <div className="space-y-4">
      <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide">
        Draft responses
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <AnswerCard
          tone="emerald"
          badge="RAG"
          title="With context"
          subtitle="Uses similar past tickets"
          text={ragAnswer.response}
          latency={ragAnswer.latency_ms}
          cost={ragAnswer.cost_usd}
        />
        <AnswerCard
          tone="slate"
          badge="No RAG"
          title="Without context"
          subtitle="LLM from training data only"
          text={noRagAnswer.response}
          latency={noRagAnswer.latency_ms}
          cost={noRagAnswer.cost_usd}
        />
      </div>
    </div>
  );
}

function AnswerCard({ tone, badge, title, subtitle, text, latency, cost }) {
  const colors = {
    emerald: { border: 'border-emerald-200', badge: 'bg-emerald-100 text-emerald-700' },
    slate:   { border: 'border-slate-200',   badge: 'bg-slate-100 text-slate-600'     },
  };
  const c = colors[tone];

  return (
    <div className={`bg-white rounded-xl shadow-sm border ${c.border} p-6 flex flex-col gap-3`}>
      <div className="flex items-center gap-3">
        <span className={`text-sm font-bold px-3 py-1 rounded-md ${c.badge} mono`}>{badge}</span>
        <div>
          <div className="font-semibold text-slate-900">{title}</div>
          <div className="text-sm text-slate-400">{subtitle}</div>
        </div>
      </div>
      <p className="text-sm text-slate-700 leading-relaxed flex-1">{text}</p>
      <div className="flex items-center justify-between text-sm text-slate-400 mono border-t border-slate-100 pt-3">
        <span>{formatLatency(latency)}</span>
        <span>${cost.toFixed(2)}</span>
      </div>
    </div>
  );
}

function formatLatency(ms) {
  if (ms < 1) return `${ms.toFixed(2)} ms`;
  if (ms < 1000) return `${Math.round(ms)} ms`;
  return `${(ms / 1000).toFixed(1)} s`;
}